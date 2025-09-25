import pytest
import respx

from bot_wb.services.wb_http_client import WBHttpClient
from bot_wb.storage.session import CookieStorage


@pytest.mark.asyncio
async def test_is_logged_in_success(tmp_path):
    storage = CookieStorage(1, root=tmp_path)
    client = WBHttpClient(1, storage=storage)
    try:
        with respx.mock(assert_all_called=True) as mock:
            mock.get("https://seller.wildberries.ru/").respond(
                200,
                text="<html>Seller cabinet</html>",
            )
            assert await client.is_logged_in() is True
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_is_logged_in_unauthorized(tmp_path):
    storage = CookieStorage(2, root=tmp_path)
    client = WBHttpClient(2, storage=storage)
    try:
        with respx.mock(assert_all_called=True) as mock:
            mock.get("https://seller.wildberries.ru/").respond(401, text="Forbidden")
            assert await client.is_logged_in() is False
    finally:
        await client.aclose()
