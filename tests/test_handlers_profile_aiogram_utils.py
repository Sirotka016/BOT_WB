import pytest

try:
    from aiogram_tests.handler import CallbackQueryHandler  # type: ignore
    from aiogram_tests.handler.internal import MockTelegramEvent
except ModuleNotFoundError:  # pragma: no cover - aiogram-tests not v3-ready
    pytest.skip(
        (
            "aiogram-tests currently targets aiogram v2 "
            "and is incompatible with aiogram v3"
        ),
        allow_module_level=True,
    )

from bot_wb.handlers.profile import on_profile


@pytest.mark.asyncio
async def test_profile_handler_runs():  # pragma: no cover
    mocked_event = MockTelegramEvent(
        from_user={"id": 1, "is_bot": False, "first_name": "Test"},
        message={"chat": {"id": 1}},
        data="profile",
    )
    handler = CallbackQueryHandler(on_profile)
    await handler(mocked_event)
