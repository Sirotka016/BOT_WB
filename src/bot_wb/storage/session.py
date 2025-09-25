from __future__ import annotations

import json
from contextlib import suppress
from pathlib import Path
from typing import Any

from bot_wb.settings import settings


class CookieStorage:
    def __init__(self, tg_user_id: int, root: Path | None = None):
        base_dir = root or settings.sessions_dir
        base_dir.mkdir(parents=True, exist_ok=True)
        self.dir = base_dir / str(tg_user_id)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.cookies_path = self.dir / "cookies.json"

    def load(self) -> dict[str, Any]:
        if self.cookies_path.exists():
            try:
                return json.loads(self.cookies_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def save(self, jar: dict[str, Any]) -> None:
        safe_jar = {str(k): v for k, v in jar.items()}
        self.cookies_path.write_text(
            json.dumps(safe_jar, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        if self.dir.exists():
            for path in self.dir.glob("*"):
                path.unlink(missing_ok=True)
            with suppress(OSError):
                self.dir.rmdir()
