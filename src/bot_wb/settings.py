import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _resolve_bot_token() -> str:
    primary = os.getenv("BOT_TOKEN")
    if primary:
        return primary
    fallback = os.getenv("TELEGRAM_BOT_TOKEN")
    return fallback or ""


@dataclass
class Settings:
    bot_token: str = field(default_factory=_resolve_bot_token)
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper(),
    )
    wb_seller_base: str = field(
        default_factory=lambda: os.getenv(
            "WB_SELLER_BASE",
            "https://seller.wildberries.ru",
        ),
    )
    wb_seller_auth_url: str = field(
        default_factory=lambda: os.getenv(
            "WB_SELLER_AUTH_URL",
            "https://seller-auth.wildberries.ru/ru/?redirect_url=https%3A%2F%2Fseller.wildberries.ru%2F",
        ),
    )
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))
    sessions_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        if not self.bot_token:
            raise RuntimeError("BOT_TOKEN is empty. Put it into .env")
        self.log_level = self.log_level.upper()
        self.sessions_dir = self.data_dir / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
