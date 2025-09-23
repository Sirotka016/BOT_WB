import json
from pathlib import Path
from typing import Any, Dict

SESS_ROOT = Path("data/sessions")
SESS_ROOT.mkdir(parents=True, exist_ok=True)


class CookieStorage:
    def __init__(self, tg_user_id: int):
        self.dir = SESS_ROOT / str(tg_user_id)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.cookies_path = self.dir / "cookies.json"

    def load(self) -> Dict[str, Any]:
        if self.cookies_path.exists():
            try:
                return json.loads(self.cookies_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save(self, jar: Dict[str, Any]) -> None:
        self.cookies_path.write_text(
            json.dumps(jar, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        for p in self.dir.glob("*"):
            p.unlink(missing_ok=True)
