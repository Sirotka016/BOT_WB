from typing import NotRequired, TypedDict


class OrgInfo(TypedDict):
    name: str
    inn: NotRequired[str]
    id: NotRequired[str]
