from typing import Optional

from .client import WBClient
from .types import OrgInfo


class ProfileAPI:
    def __init__(self, client: WBClient):
        self.c = client

    async def organization(self) -> Optional[OrgInfo]:
        # TODO: заменить на реальную ручку/ключи
        js = await self.c.get_json("api/profile/organization")
        name = js.get("name") or js.get("orgName")
        if not name:
            return None
        return {"name": name, "inn": js.get("inn"), "id": str(js.get("id") or "")}
