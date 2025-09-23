import asyncio
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
        page = await self.get_page(tg_user_id)
        await page.goto(self.base_url, wait_until="domcontentloaded")

        phone_input_sel = "input[type='tel'], input[name='phone']"
        submit_phone_sel = (
            "button[type='submit'], button:has-text('Получить код'), [data-qa='sendPhone']"
        )

        await page.wait_for_selector(phone_input_sel, state="visible", timeout=8000)
        await page.fill(phone_input_sel, phone)
        await page.wait_for_timeout(120)  # стабилизация маски телефона
        btn = await page.query_selector(submit_phone_sel)
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")

    async def fill_sms_code(self, tg_user_id: int, code: str):
        page = await self.get_page(tg_user_id)

        inputs = await page.query_selector_all(
            "input[autocomplete='one-time-code'], input[name^='code'], input[type='tel']"
        )
        if inputs and len(code) >= len(inputs) >= 4:
            for i, ch in enumerate(code[: len(inputs)]):
                await inputs[i].fill(ch)
        else:
            code_sel = "input[name='code'], input[type='text'][maxlength='6'], input[type='tel']"
            await page.wait_for_selector(code_sel, state="visible", timeout=8000)
            await page.fill(code_sel, code)
        await page.keyboard.press("Enter")

    async def fill_email(self, tg_user_id: int, email: str):
        page = await self.get_page(tg_user_id)
        email_sel = "input[type='email'], input[name='email']"
        submit_sel = (
            "button[type='submit'], button:has-text('Продолжить'), [data-qa='sendEmail']"
        )
        await page.wait_for_selector(email_sel, state="visible", timeout=8000)
        await page.fill(email_sel, email)
        btn = await page.query_selector(submit_sel)
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")

    async def fill_email_code(self, tg_user_id: int, code: str):
        # повторяем логику для СМС-кода
        await self.fill_sms_code(tg_user_id, code)
        await asyncio.sleep(0.6)  # короткая пауза на редирект/обновление
        # после успешного шага — сохраняем storage_state пользователя
        await self._save_state(tg_user_id)

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
