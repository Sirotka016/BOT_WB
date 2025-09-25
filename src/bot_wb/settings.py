from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN", "")
    wb_base_url: str = os.getenv("WB_BASE_URL", "https://example.wb-partner.ru")
    wb_partner_url: str = os.getenv("WB_PARTNER_URL", "https://seller.wildberries.ru/")
    wb_seller_base: str = os.getenv("WB_SELLER_BASE", "https://seller.wildberries.ru")
    wb_seller_auth_url: str = os.getenv(
        "WB_SELLER_AUTH_URL",
        "https://seller-auth.wildberries.ru/ru/?redirect_url=https%3A%2F%2Fseller.wildberries.ru%2F",
    )
    webapp_host: str = os.getenv("WEBAPP_HOST", "0.0.0.0")
    webapp_port: int = int(os.getenv("WEBAPP_PORT", "8080"))
    webapp_public_url: str = os.getenv("WEBAPP_PUBLIC_URL", "http://localhost:8080")


def _build_settings() -> Settings:
    settings_obj = Settings()
    if not settings_obj.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Put it into .env")
    return settings_obj


settings = _build_settings()
