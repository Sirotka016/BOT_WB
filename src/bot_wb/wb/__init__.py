from .auth import AuthAPI
from .client import WBClient
from .profile import ProfileAPI
from .shipments import ShipmentsAPI


class WBSeller:
    """
    Фасад: wb = WBSeller(tg_id); wb.auth.start_phone(...), wb.profile.organization() и т.п.
    """

    def __init__(self, tg_user_id: int):
        self.client = WBClient(tg_user_id)
        self.auth = AuthAPI(self.client)
        self.profile = ProfileAPI(self.client)
        self.shipments = ShipmentsAPI(self.client)

    async def aclose(self) -> None:
        await self.client.aclose()


__all__ = ["WBSeller", "WBClient", "AuthAPI", "ProfileAPI", "ShipmentsAPI"]
