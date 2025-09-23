import asyncio
import re
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Route,
    Request,
    TimeoutError as PWTimeoutError,
)

# Каталоги для контекстов и storage_state
CONTEXTS_DIR = Path("data/contexts")
STATES_DIR = Path("data/storage")
CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)
STATES_DIR.mkdir(parents=True, exist_ok=True)

# Для ускорения: не грузим тяжёлые ресурсы и трекеры
BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
BLOCKED_URL_PARTS = (
    "googletagmanager",
    "google-analytics",
    "yandex",
    "metrika",
    "doubleclick",
    "facebook",
    "vk.com/rtrg",
    "gtm.js",
    "analytics.js",
)

PHONE_INPUT_SEL = "input[type='tel'], input[name='phone'], input[placeholder*='999 999-99-99']"
SMS_CODE_INPUTS_SEL = "input[autocomplete='one-time-code'], input[name^='code'], input[data-test*='code']"
EMAIL_INPUT_SEL = "input[type='email'], input[name='email']"
SUBMIT_BTN_SEL = "button[type='submit'], button:has-text('Получить код'), button:has-text('Продолжить'), [data-qa='sendPhone'], [data-qa='sendEmail']"


def _normalize_phone_for_ru_mask(phone: str) -> str:
    """
    Преобразует ввод пользователя к формату, который ожидает поле с маской '+7 999 999-99-99':
    - если пришло '+7XXXXXXXXXX' -> 'XXXXXXXXXX'
    - если пришло '8XXXXXXXXXX'  -> 'XXXXXXXXXX'
    - если пришло 'XXXXXXXXXX'   -> 'XXXXXXXXXX'
    Возвращает ровно 10 цифр или ''.
    """

    digits = re.sub(r"\D", "", phone)
    if digits.startswith("7") and len(digits) == 11:
        digits = digits[1:]
    elif digits.startswith("8") and len(digits) == 11:
        digits = digits[1:]
    # если ввели сразу 10 цифр — оставляем как есть
    return digits if len(digits) == 10 else ""


async def _fill_code_inputs(page: Page, code: str):
    """
    Универсальная функция для 4-значных (или n-значных) кодов из отдельных инпутов.
    Если на странице один инпут — просто печатаем туда весь код.
    """

    digits = re.sub(r"\D", "", code)
    inputs = await page.query_selector_all(SMS_CODE_INPUTS_SEL)
    if inputs and len(inputs) in (4, 5, 6) and len(digits) >= len(inputs):
        for i, ch in enumerate(digits[: len(inputs)]):
            await inputs[i].fill(ch)
        return True
    # одиночное поле — пробуем найти наиболее вероятный инпут
    single_sel = "input[name='code'], input[maxlength='4'], input[ maxlength='4' ], input[type='text'][maxlength], input[type='tel']"
    el = await page.query_selector(single_sel)
    if el:
        await el.fill(digits)
        return True
    return False


def _should_block(req: Request) -> bool:
    if req.resource_type in BLOCKED_RESOURCE_TYPES:
        return True
    url = req.url.lower()
    return any(p in url for p in BLOCKED_URL_PARTS)


class WBBrowser:
    """
    Один Chromium на весь процесс (headful для дебага). На каждого tg_user_id — отдельный context,
    состояние (cookies/localStorage) сохраняем в data/storage/<tg_user_id>.json.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/") + "/"
        self._pw = None
        self._browser: Optional[Browser] = None
        self._contexts: dict[int, BrowserContext] = {}
        self._pages: dict[int, Page] = {}

    # ---------- Жизненный цикл браузера ----------

    async def start(self):
        if self._pw is None:
            self._pw = await async_playwright().start()
        if self._browser is None:
            # headless=False — удобнее видеть, что происходит; на сервере можно включить True
            self._browser = await self._pw.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )

    async def stop(self):
        for ctx in list(self._contexts.values()):
            try:
                await ctx.close()
            except Exception:
                pass
        self._contexts.clear()
        self._pages.clear()
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._pw:
            try:
                await self._pw.stop()
            except Exception:
                pass
            self._pw = None

    async def _route_speedups(self, route: Route):
        req = route.request
        if _should_block(req):
            return await route.abort()
        return await route.continue_()

    async def _save_state(self, tg_user_id: int):
        """
        Сохранить состояние контекста пользователя в файл storage_state.
        """
        ctx = self._contexts.get(tg_user_id)
        if not ctx:
            return
        state_file = STATES_DIR / f"{tg_user_id}.json"
        await ctx.storage_state(path=str(state_file))

    # ---------- Получение страницы пользователя ----------

    async def get_page(self, tg_user_id: int) -> Page:
        """
        Возвращает страницу в контексте пользователя. Контекст и страница переиспользуются.
        Если для пользователя уже есть storage_state — подтягиваем его при создании контекста.
        """
        await self.start()
        if tg_user_id in self._pages:
            return self._pages[tg_user_id]

        state_file = STATES_DIR / f"{tg_user_id}.json"
        ctx = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            storage_state=str(state_file) if state_file.exists() else None,
        )
        await ctx.route("**/*", self._route_speedups)
        page = await ctx.new_page()
        self._contexts[tg_user_id] = ctx
        self._pages[tg_user_id] = page
        return page

    async def open_partner(self, tg_user_id: int):
        page = await self.get_page(tg_user_id)
        await page.goto(self.base_url, wait_until="domcontentloaded")
        # на всякий случай переключимся на русский, если есть селектор языка
        try:
            await page.wait_for_timeout(100)
            # необязательно; оставляем как no-op, если элемента нет
        except Exception:
            pass

    async def is_logged_in(self, tg_user_id: int) -> bool:
        """
        Эвристика авторизации: ищем элемент, который появляется только после входа.
        TODO: подставить стабильный селектор под реальную вёрстку WB Partner.
        """
        page = await self.get_page(tg_user_id)
        try:
            el = await page.query_selector(
                "header [href*='logout'], [data-qa='profileMenu'], header .avatar"
            )
            return el is not None
        except Exception:
            return False

    # ---------- Шаги авторизации ----------

    async def fill_phone(self, tg_user_id: int, phone: str):
        """
        На стартовом экране уже проставлено '+7', поэтому вводим только 10 цифр локального номера.
        """

        page = await self.get_page(tg_user_id)
        # гарантируем, что мы на странице входа (если пользователь нажал 'Авторизация' не с первого раза)
        if page.url.rstrip("/") != self.base_url.rstrip("/"):
            await page.goto(self.base_url, wait_until="domcontentloaded")

        local10 = _normalize_phone_for_ru_mask(phone)
        if not local10:
            raise ValueError("bad phone for RU mask")

        await page.wait_for_selector(PHONE_INPUT_SEL, state="visible", timeout=8000)
        # кликаем по инпуту, чтобы поставить курсор после '+7 '
        input_el = await page.query_selector(PHONE_INPUT_SEL)
        await input_el.click()
        # возможно, поле уже содержит часть маски, чистим что могли набрать ранее
        await input_el.fill("")  # заполнит только цифры части; '+7 ' часто не удаляется — это нормально
        await page.keyboard.type(local10, delay=20)  # небольшая задержка для стабильности маски

        # отправляем форму
        try:
            btn = await page.query_selector(SUBMIT_BTN_SEL)
            if btn:
                await btn.click()
            else:
                await page.keyboard.press("Enter")
        except PWTimeoutError:
            await page.keyboard.press("Enter")

    async def fill_sms_code(self, tg_user_id: int, code: str):
        page = await self.get_page(tg_user_id)
        # ждём появления формы ввода кода
        try:
            await page.wait_for_selector(SMS_CODE_INPUTS_SEL, state="attached", timeout=8000)
        except PWTimeoutError:
            # возможно, другой селектор — ждём любое поле ввода кода
            await page.wait_for_selector("input", timeout=8000)

        await _fill_code_inputs(page, code)
        await page.keyboard.press("Enter")

    async def fill_email(self, tg_user_id: int, email: str):
        page = await self.get_page(tg_user_id)
        await page.wait_for_selector(EMAIL_INPUT_SEL, state="visible", timeout=8000)
        await page.fill(EMAIL_INPUT_SEL, email)
        btn = await page.query_selector(SUBMIT_BTN_SEL)
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")

    async def fill_email_code(self, tg_user_id: int, code: str):
        page = await self.get_page(tg_user_id)
        try:
            await page.wait_for_selector(SMS_CODE_INPUTS_SEL, state="attached", timeout=8000)
        except PWTimeoutError:
            await page.wait_for_selector("input", timeout=8000)

        await _fill_code_inputs(page, code)
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.6)
        await self._save_state(tg_user_id)  # сохраняем storage_state после успешного шага

    # ---------- Выход ----------

    async def logout(self, tg_user_id: int):
        """
        Завершить сессию пользователя: закрыть его контекст и удалить storage_state-файл.
        """
        ctx = self._contexts.pop(tg_user_id, None)
        self._pages.pop(tg_user_id, None)
        if ctx:
            try:
                await ctx.close()
            except Exception:
                pass
        # удалить storage_state
        try:
            state_file = STATES_DIR / f"{tg_user_id}.json"
            if state_file.exists():
                state_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove storage state for {tg_user_id}: {e}")
