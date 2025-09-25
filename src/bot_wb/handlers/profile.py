from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot_wb.logging import logger
from bot_wb.services.wb_http_client import WBHttpClient
from bot_wb.storage.repo import UserRepo
from bot_wb.ui import texts
from bot_wb.ui.keyboards import kb_profile_switch, kb_profile_view

from ._render import _edit_or_send, _replace_message

router = Router(name=__name__)
_repo = UserRepo()


async def _render_profile(cb: CallbackQuery, *, force_replace: bool = False) -> None:
    if cb.bot is None:
        raise RuntimeError("Callback does not contain bot instance")
    tg_id = cb.from_user.id
    profiles = await _repo.get_profiles(tg_id)
    if not profiles:
        client = WBHttpClient(tg_id)
        try:
            profiles = await client.list_organizations()
        finally:
            await client.aclose()
        await _repo.set_profiles(tg_id, profiles)
        if len(profiles) == 1:
            first_id = profiles[0].get("id")
            if first_id is not None:
                await _repo.set_active_profile(tg_id, str(first_id))

    active_id = await _repo.get_active_profile(tg_id)

    if len(profiles) <= 1:
        org_name = profiles[0].get("name") if profiles else None
        text = texts.profile_text_single(org_name)
        markup = kb_profile_view(has_multiple=False)
    else:
        text = texts.profile_text_multi(profiles, active_id)
        markup = kb_profile_view(has_multiple=True)

    chat = getattr(cb.message, "chat", None)
    chat_id = getattr(chat, "id", cb.from_user.id)
    if force_replace:
        await _replace_message(cb.bot, chat_id, text, markup)
    else:
        await _edit_or_send(cb.bot, chat_id, text, markup)
    await _repo.set_view(tg_id, "profile")
    logger.info("Rendered profile view for chat {}", chat_id)


@router.callback_query(F.data == "profile")
async def on_profile(cb: CallbackQuery):
    await _render_profile(cb)
    await cb.answer()


@router.callback_query(F.data == "profile_refresh")
async def on_profile_refresh(cb: CallbackQuery):
    await _render_profile(cb, force_replace=True)
    await cb.answer("Обновлено")


@router.callback_query(F.data == "profile_switch")
async def on_profile_switch(cb: CallbackQuery):
    tg_id = cb.from_user.id
    profiles = await _repo.get_profiles(tg_id)
    active_id = await _repo.get_active_profile(tg_id)
    if not profiles:
        await cb.answer("Профили не найдены", show_alert=True)
        return
    message_obj = cb.message
    if message_obj is None or not hasattr(message_obj, "edit_text"):
        await cb.answer()
        return
    await message_obj.edit_text(
        text="Выберите профиль для работы:",
        reply_markup=kb_profile_switch(
            [(str(p.get("id") or ""), p.get("name") or "—") for p in profiles],
            active_id,
        ),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("set_profile:"))
async def on_set_profile(cb: CallbackQuery):
    if cb.data is None:
        await cb.answer("Некорректные данные", show_alert=True)
        return
    pid = cb.data.split(":", 1)[1]
    tg_id = cb.from_user.id

    client = WBHttpClient(tg_id)
    ok = True
    try:
        ok = await client.set_active_organization(pid)
    finally:
        await client.aclose()

    if ok:
        await _repo.set_active_profile(tg_id, pid)
        await cb.answer("Профиль выбран")
        await _render_profile(cb)
    else:
        await cb.answer("Не удалось сменить профиль", show_alert=True)
