import asyncio
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Request,
    Route,
    async_playwright,
)

CONTEXTS_DIR = Path("data/contexts")
CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)

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
    return any(part in url for part in BLOCKED_URL_PARTS)


class WBBrowser:
    """
    Один Chromium на весь процесс. Для каждого tg_user_id — отдельный persistent context
    в data/contexts/<tg_user_id>. Действуем только через реальную страницу кабинета.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/") + "/"
        self._pw = None
        self._browser: Optional[Browser] = None
        self._contexts: dict[int, BrowserContext] = {}
        self._pages: dict[int, Page] = {}

    async def start(self):
        if self._pw is None:
            self._pw = await async_playwright().start()
        if self._browser is None:
            # headless=False — быстрее дебажить. На сервере можно переключить на True.
            self._browser = await self._pw.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )

    async def stop(self):
        for ctx in list(self._contexts.values()):
            await ctx.close()
        self._contexts.clear()
        self._pages.clear()
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()
            self._pw = None

    async def _route_speedups(self, route: Route):
        req = route.request
        if _should_block(req):
            return await route.abort()
        return await route.continue_()

    async def get_page(self, tg_user_id: int) -> Page:
        """
        Возвращает готовую страницу в личном контексте пользователя.
        Контекст и страница переиспользуются для скорости.
        """

        await self.start()
        if tg_user_id in self._pages:
            return self._pages[tg_user_id]

        user_dir = CONTEXTS_DIR / str(tg_user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        ctx = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_data_dir=str(user_dir),
        )
        await ctx.route("**/*", self._route_speedups)  # блокируем тяжёлые ресурсы
        page = await ctx.new_page()
        self._contexts[tg_user_id] = ctx
        self._pages[tg_user_id] = page
        return page

    async def open_partner(self, tg_user_id: int):
        page = await self.get_page(tg_user_id)
        await page.goto(self.base_url, wait_until="domcontentloaded")

    async def is_logged_in(self, tg_user_id: int) -> bool:
        """
        Эвристика: наличие элемента, доступного только после входа.
        TODO: заменить селектор на стабильный под фактическую верстку.
        """

        page = await self.get_page(tg_user_id)
        try:
            el = await page.query_selector("header [href*='logout'], [data-qa='profileMenu']")
            return el is not None
        except Exception:
            return False

    async def fill_phone(self, tg_user_id: int, phone: str):
        page = await self.get_page(tg_user_id)
        await page.goto(self.base_url, wait_until="domcontentloaded")

        phone_input_sel = "input[type='tel'], input[name='phone']"
        submit_phone_sel = "button[type='submit'], button:has-text('Получить код'), [data-qa='sendPhone']"

        await page.wait_for_selector(phone_input_sel, state="visible", timeout=8000)
        await page.fill(phone_input_sel, phone)
        await page.wait_for_timeout(120)  # короткая стабилизация маски
        btn = await page.query_selector(submit_phone_sel)
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")

    async def fill_sms_code(self, tg_user_id: int, code: str):
        page = await self.get_page(tg_user_id)

        # Пытаемся найти несколько полей для цифр
        inputs = await page.query_selector_all(
            "input[autocomplete='one-time-code'], input[name^='code'], input[type='tel']"
        )
        if inputs and len(code) >= len(inputs) >= 4:
            for idx, ch in enumerate(code[: len(inputs)]):
                await inputs[idx].fill(ch)
        else:
            # Одиночное поле
            code_sel = "input[name='code'], input[type='text'][maxlength='6'], input[type='tel']"
            await page.wait_for_selector(code_sel, state="visible", timeout=8000)
            await page.fill(code_sel, code)
        await page.keyboard.press("Enter")

    async def fill_email(self, tg_user_id: int, email: str):
        page = await self.get_page(tg_user_id)
        email_sel = "input[type='email'], input[name='email']"
        submit_sel = "button[type='submit'], button:has-text('Продолжить'), [data-qa='sendEmail']"
        await page.wait_for_selector(email_sel, state="visible", timeout=8000)
        await page.fill(email_sel, email)
        btn = await page.query_selector(submit_sel)
        if btn:
            await btn.click()
        else:
            await page.keyboard.press("Enter")

    async def fill_email_code(self, tg_user_id: int, code: str):
        # как для SMS
        await self.fill_sms_code(tg_user_id, code)
        await asyncio.sleep(0.6)  # короткая пауза на редирект/обновление

    async def logout(self, tg_user_id: int):
        # Закрыть контекст и удалить его директорию
        ctx = self._contexts.pop(tg_user_id, None)
        self._pages.pop(tg_user_id, None)
        if ctx:
            try:
                await ctx.close()
            except Exception:
                pass
        user_dir = CONTEXTS_DIR / str(tg_user_id)
        try:
            import shutil

            if user_dir.exists():
                shutil.rmtree(user_dir)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Failed to remove {user_dir}: {exc}")

