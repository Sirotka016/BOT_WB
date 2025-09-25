from types import SimpleNamespace
from typing import Any

import pytest

from bot_wb.handlers import _render as render_module
from bot_wb.handlers import profile as profile_module

CHAT_ID_SINGLE = 500
CHAT_ID_MULTI = 600
ANCHOR_ID = 321


class FakeRepo:
    def __init__(
        self,
        profiles: list[dict],
        anchor: int | None = None,
        active: str | None = None,
    ) -> None:
        self._profiles = profiles
        self._anchor = anchor
        self._active = active
        self.views: dict[int, str | None] = {}

    async def get_profiles(self, tg_id: int) -> list[dict]:
        return self._profiles

    async def set_profiles(self, tg_id: int, profiles: list[dict]) -> None:
        self._profiles = profiles

    async def get_active_profile(self, tg_id: int) -> str | None:
        return self._active

    async def set_active_profile(self, tg_id: int, profile_id: str) -> None:
        self._active = profile_id

    async def set_view(self, tg_id: int, view: str | None) -> None:
        self.views[tg_id] = view

    async def get_anchor(self, tg_id: int) -> int | None:
        return self._anchor

    async def set_anchor(self, tg_id: int, anchor: int) -> None:
        self._anchor = anchor


class DummyBot:
    def __init__(self, initial_message_id: int = 100):
        self.sent: list[dict[str, Any]] = []
        self.edited: list[dict[str, Any]] = []
        self.deleted: list[dict[str, Any]] = []
        self._message_id = initial_message_id

    async def send_message(self, chat_id: int, text: str, reply_markup: Any):
        self._message_id += 1
        self.sent.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": reply_markup,
            },
        )
        return SimpleNamespace(message_id=self._message_id)

    async def edit_message_text(
        self,
        text: str,
        chat_id: int,
        message_id: int,
        reply_markup: Any,
    ) -> None:
        self.edited.append(
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "reply_markup": reply_markup,
            },
        )

    async def delete_message(self, chat_id: int, message_id: int):
        self.deleted.append({"chat_id": chat_id, "message_id": message_id})


class StubClient:
    def __init__(self, tg_user_id: int, *, profiles: list[dict]):
        self._profiles = profiles

    async def list_organizations(self) -> list[dict]:
        return self._profiles

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_render_profile_single(monkeypatch):
    repo = FakeRepo(profiles=[{"id": "default", "name": "Org"}])
    bot = DummyBot()
    monkeypatch.setattr(profile_module, "_repo", repo)
    monkeypatch.setattr(render_module, "_repo", repo)

    def _make_client(tg_id: int, *_: Any, **__: Any) -> StubClient:
        return StubClient(tg_id, profiles=repo._profiles)

    monkeypatch.setattr(profile_module, "WBHttpClient", _make_client)

    message = SimpleNamespace(chat=SimpleNamespace(id=CHAT_ID_SINGLE))
    cb = SimpleNamespace(
        message=message,
        bot=bot,
        from_user=SimpleNamespace(id=777),
    )

    await profile_module._render_profile(cb)

    assert repo.views[777] == "profile"
    assert bot.sent[0]["chat_id"] == CHAT_ID_SINGLE
    assert "Организация" in bot.sent[0]["text"]
    buttons = [
        [button.text for button in row] for row in bot.sent[0]["reply_markup"].inline_keyboard
    ]
    assert not any("🔀" in text for row in buttons for text in row)


@pytest.mark.asyncio
async def test_render_profile_multi_force_replace(monkeypatch):
    profiles = [
        {"id": "1", "name": "Org 1"},
        {"id": "2", "name": "Org 2"},
    ]
    repo = FakeRepo(profiles=profiles, anchor=ANCHOR_ID, active="2")
    bot = DummyBot()
    monkeypatch.setattr(profile_module, "_repo", repo)
    monkeypatch.setattr(render_module, "_repo", repo)

    def _make_multi_client(tg_id: int, *_: Any, **__: Any) -> StubClient:
        return StubClient(tg_id, profiles=profiles)

    monkeypatch.setattr(profile_module, "WBHttpClient", _make_multi_client)

    message = SimpleNamespace(chat=SimpleNamespace(id=CHAT_ID_MULTI))
    cb = SimpleNamespace(
        message=message,
        bot=bot,
        from_user=SimpleNamespace(id=42),
    )

    await profile_module._render_profile(cb, force_replace=True)

    assert repo._anchor != ANCHOR_ID
    assert bot.deleted[0]["message_id"] == ANCHOR_ID
    buttons = [
        [button.text for button in row] for row in bot.sent[0]["reply_markup"].inline_keyboard
    ]
    assert any("🔀" in text for row in buttons for text in row)
    assert repo.views[42] == "profile"
