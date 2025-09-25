from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    # Делает пакет bot_wb видимым для локального запуска "python main.py"
    sys.path.insert(0, str(SRC))

from bot_wb.main import main  # noqa: E402


if __name__ == "__main__":
    asyncio.run(main())
