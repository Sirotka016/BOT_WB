from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    wb_base_url: str = os.getenv("WB_BASE_URL", "https://example.wb-partner.ru")
    wb_partner_url: str = os.getenv("WB_PARTNER_URL", "https://seller.wildberries.ru/")


def _build_settings() -> Settings:
    settings_obj = Settings()
    if not settings_obj.bot_token:
        raise RuntimeError("BOT_TOKEN is empty. Put it into .env")
    return settings_obj


settings = _build_settings()
