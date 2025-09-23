import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ..services.auth_service import AuthService
from ..storage.repo import UserRepo
from ..ui import texts
from ..ui.keyboards import kb_auth_stub
from ._render import render_home, render_profile

router = Router(name=__name__)
_repo = UserRepo()
_auth = AuthService(_repo)


class AuthFSM(StatesGroup):
    waiting_phone = State()
    waiting_sms_code = State()
    waiting_email_code = State()


@router.callback_query(F.data == "auth")
async def on_auth(cb: CallbackQuery, state: FSMContext):
    await _repo.set_view(cb.from_user.id, "auth_phone")
    await cb.message.edit_text(texts.ask_phone_text(), reply_markup=kb_auth_stub())
    await state.set_state(AuthFSM.waiting_phone)
    await cb.answer()


@router.callback_query(F.data == "profile")
async def on_profile(cb: CallbackQuery):
    await render_profile(cb.bot, cb.message.chat.id)
    await cb.answer()


@router.message(AuthFSM.waiting_phone)
async def got_phone(message: Message, state: FSMContext):
    phone_raw = (message.text or "").strip()
    digits = re.sub(r"\D", "", phone_raw)
    anchor = await _repo.get_anchor(message.chat.id)
    target_message_id = anchor or message.message_id
    if not (len(digits) in (10, 11) and digits[-10:].isdigit()):
        await message.bot.edit_message_text(
            "Неверный формат. Пример: +79991234567",
            message.chat.id,
            target_message_id,
        )
        return
    ok = await _auth.login_phone(message.from_user.id, phone_raw)
    text = texts.ask_sms_code_text() if ok else "Не удалось отправить код. Попробуйте позже."
    await _repo.set_view(message.from_user.id, "auth_sms")
    await message.bot.edit_message_text(
        text,
        message.chat.id,
        target_message_id,
        reply_markup=kb_auth_stub(),
    )
    if ok:
        await state.set_state(AuthFSM.waiting_sms_code)


@router.message(AuthFSM.waiting_sms_code)
async def got_sms(message: Message, state: FSMContext):
    code = (message.text or "").strip()
    anchor = await _repo.get_anchor(message.chat.id)
    target_message_id = anchor or message.message_id
    if not code.isdigit():
        await message.bot.edit_message_text(
            "Код должен содержать только цифры.",
            message.chat.id,
            target_message_id,
        )
        return
    user = await _repo.get(message.from_user.id)
    ok = await _auth.login_sms(message.from_user.id, (user or {}).get("phone", ""), code)
    text = texts.ask_email_code_text() if ok else "Неверный код или ошибка. Попробуйте снова."
    await _repo.set_view(message.from_user.id, "auth_email_code" if ok else "auth_sms")
    await message.bot.edit_message_text(
        text,
        message.chat.id,
        target_message_id,
        reply_markup=kb_auth_stub(),
    )
    if ok:
        await state.set_state(AuthFSM.waiting_email_code)


@router.message(AuthFSM.waiting_email_code)
async def got_email_code(message: Message, state: FSMContext):
    code = (message.text or "").strip()
    anchor = await _repo.get_anchor(message.chat.id)
    target_message_id = anchor or message.message_id
    if not code:
        await message.bot.edit_message_text(
            "Введите код с e-mail.",
            message.chat.id,
            target_message_id,
        )
        return
    ok = await _auth.login_email_code(message.from_user.id, code)
    if ok:
        await state.clear()
        await _repo.set_view(message.from_user.id, "home")
        user_name = message.from_user.full_name if message.from_user else "друг"
        await render_home(message.bot, message.chat.id, user_name)
    else:
        await message.bot.edit_message_text(
            "Код с e-mail не подошёл. Попробуйте снова.",
            message.chat.id,
            target_message_id,
        )


@router.callback_query(F.data == "logout")
async def logout(cb: CallbackQuery, state: FSMContext):
    await _auth.logout(cb.from_user.id)
    await state.clear()
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    await render_home(cb.bot, cb.message.chat.id, user_name)
    await cb.answer()


@router.callback_query(F.data == "home")
async def to_home(cb: CallbackQuery):
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    await render_home(cb.bot, cb.message.chat.id, user_name)
    await cb.answer()


@router.callback_query(F.data == "refresh")
async def refresh(cb: CallbackQuery):
    view = await _repo.get_view(cb.from_user.id)
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    if view == "profile":
        await render_profile(cb.bot, cb.message.chat.id)
    else:
        await render_home(cb.bot, cb.message.chat.id, user_name)
    await cb.answer()


@router.callback_query(F.data == "close")
async def close(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await _repo.set_view(cb.from_user.id, None)
    anchor = await _repo.get_anchor(cb.from_user.id)
    text = "Сессия завершена. Нажмите /start для новой сессии."
    if anchor:
        await cb.bot.edit_message_text(text, cb.message.chat.id, anchor)
    else:
        await cb.message.edit_text(text)
    await cb.answer()
