from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    wb_base_url: str = os.getenv("WB_BASE_URL", "https://example.wb-partner.ru")
    wb_partner_url: str = os.getenv("WB_PARTNER_URL", "https://seller.wildberries.ru/")
    wb_seller_base: str = os.getenv("WB_SELLER_BASE", "https://seller.wildberries.ru")
    wb_seller_auth_url: str = os.getenv(
        "WB_SELLER_AUTH_URL",
        "https://seller-auth.wildberries.ru/ru/?redirect_url=https%3A%2F%2Fseller.wildberries.ru%2F",
    )


def _build_settings() -> Settings:
    settings_obj = Settings()
    if not settings_obj.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Put it into .env")
    return settings_obj


settings = _build_settings()
