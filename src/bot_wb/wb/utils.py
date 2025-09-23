import re
from typing import Optional


def normalize_ru_phone_e164(phone: str) -> str:
    d = re.sub(r"\D", "", phone)
    if len(d) == 11 and (d.startswith("7") or d.startswith("8")):
        d = d[1:]
    if len(d) != 10:
        return ""
    return f"+7{d}"


def pick_csrf_from_html(html: str) -> Optional[str]:
    # TODO: если WB требует CSRF, вытащить из meta/hidden input
    # пример: <meta name="csrf-token" content="...">
    m = re.search(r'name=["\']csrf[^"\']*["\']\s+content=["\']([^"\']+)["\']', html, re.I)
    return m.group(1) if m else None
