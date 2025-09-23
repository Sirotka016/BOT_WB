# Заглушки под будущие функции (слоты/поставки)
from .client import WBClient


class ShipmentsAPI:
    def __init__(self, client: WBClient):
        self.c = client

    async def find_slots(self, **filters):
        # TODO: GET/POST на поиск слотов
        return []

    async def create_supply(self, payload: dict):
        # TODO
        return {"id": "TODO"}
