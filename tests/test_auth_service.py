import pytest

from bot_wb.services import auth_service as auth_module
from bot_wb.services.auth_service import AuthService


class FakeRepo:
    def __init__(self):
        self.authorized: dict[int, bool] = {}
        self.profiles: dict[int, list[dict]] = {}
        self.active: dict[int, str | None] = {}
        self.names: dict[int, str | None] = {}

    async def set_profiles(self, tg_id: int, profiles: list[dict]) -> None:
        self.profiles[tg_id] = profiles

    async def set_active_profile(self, tg_id: int, profile_id: str) -> None:
        self.active[tg_id] = profile_id

    async def set_profile_org(self, tg_id: int, name: str | None) -> None:
        self.names[tg_id] = name

    async def set_authorized(self, tg_id: int, flag: bool) -> None:
        self.authorized[tg_id] = flag

    async def clear_auth(self, tg_id: int) -> None:  # pragma: no cover - not used here
        self.authorized[tg_id] = False


class DummyBrowserLogin:
    def __init__(self, tg_user_id: int, result: bool):
        self.tg_user_id = tg_user_id
        self._result = result

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def run_flow(self, timeout_sec: int = 420) -> bool:
        return self._result


class DummyClient:
    def __init__(self, tg_user_id: int, *, profiles: list[dict]):
        self.tg_user_id = tg_user_id
        self._profiles = profiles

    async def list_organizations(self) -> list[dict]:
        return self._profiles

    async def get_organization_name(self) -> str | None:
        return "WB"

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_interactive_login_success(monkeypatch):
    repo = FakeRepo()
    monkeypatch.setattr(
        auth_module,
        "BrowserLogin",
        lambda tg_id: DummyBrowserLogin(tg_id, result=True),
    )
    monkeypatch.setattr(
        auth_module,
        "WBHttpClient",
        lambda tg_id: DummyClient(tg_id, profiles=[{"id": "1", "name": "Org"}]),
    )

    service = AuthService(repo)
    ok = await service.interactive_login(100)

    assert ok is True
    assert repo.authorized[100] is True
    assert repo.active[100] == "1"
    assert repo.profiles[100][0]["name"] == "Org"


@pytest.mark.asyncio
async def test_interactive_login_failure(monkeypatch):
    repo = FakeRepo()
    monkeypatch.setattr(
        auth_module,
        "BrowserLogin",
        lambda tg_id: DummyBrowserLogin(tg_id, result=False),
    )
    monkeypatch.setattr(
        auth_module,
        "WBHttpClient",
        lambda tg_id: DummyClient(tg_id, profiles=[]),
    )

    service = AuthService(repo)
    ok = await service.interactive_login(200)

    assert ok is False
    assert repo.authorized.get(200) is False
