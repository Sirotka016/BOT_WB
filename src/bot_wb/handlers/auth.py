import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from ..ui.keyboards import kb_auth_stub, kb_home, kb_logout
from ..ui import texts
from ..services.auth_service import AuthService
from ..storage.repo import UserRepo

router = Router(name=__name__)
_repo = UserRepo()
_auth = AuthService(_repo)


class AuthFSM(StatesGroup):
    waiting_phone = State()
    waiting_sms_code = State()
    waiting_email_code = State()


@router.callback_query(F.data == "auth")
async def on_auth(cb: CallbackQuery, state: FSMContext):
    tg_id = cb.from_user.id
    if await _auth.is_authorized(tg_id):
        await cb.message.edit_text(texts.logged_in_text(), reply_markup=kb_logout())
    else:
        await _auth.start_partner(tg_id)
        await cb.message.edit_text(texts.ask_phone_text(), reply_markup=kb_auth_stub())
        await state.set_state(AuthFSM.waiting_phone)
    await cb.answer()


@router.message(AuthFSM.waiting_phone)
async def got_phone(m: Message, state: FSMContext):
    phone_raw = (m.text or "").strip()
    digits = re.sub(r"\D", "", phone_raw)
    if not (len(digits) in (10, 11) and digits[-10:].isdigit()):
        await m.reply("Неверный формат. Пример: +79991234567")
        return
    await _auth.submit_phone(m.from_user.id, phone_raw)
    await m.answer(texts.ask_sms_code_text())
    await state.set_state(AuthFSM.waiting_sms_code)


@router.message(AuthFSM.waiting_sms_code)
async def got_sms(m: Message, state: FSMContext):
    code = (m.text or "").strip()
    if not code.isdigit():
        await m.reply("Код должен содержать только цифры.")
        return
    await _auth.submit_sms(m.from_user.id, code)
    # Сразу просим код с e-mail, без шага ввода адреса
    await m.answer(texts.ask_email_code_text())
    await state.set_state(AuthFSM.waiting_email_code)


@router.message(AuthFSM.waiting_email_code)
async def got_email_code(m: Message, state: FSMContext):
    code = (m.text or "").strip()
    if not code:
        await m.reply("Введите код с e-mail.")
        return
    await _auth.submit_email_code(m.from_user.id, code)
    await state.clear()
    await m.answer(texts.auth_success_text(), reply_markup=kb_logout())


@router.callback_query(F.data == "logout")
async def logout(cb: CallbackQuery, state: FSMContext):
    await _auth.logout(cb.from_user.id)
    await state.clear()
    await cb.message.edit_text(texts.logout_done_text(), reply_markup=None)
    await cb.answer()


@router.callback_query(F.data == "home")
async def to_home(cb: CallbackQuery):
    from ..ui.texts import home_text
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    await cb.message.edit_text(home_text(user_name), reply_markup=kb_home())
    await cb.answer()


@router.callback_query(F.data == "refresh")
async def refresh(cb: CallbackQuery):
    from ..ui.texts import home_text
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    await cb.message.edit_text(home_text(user_name), reply_markup=kb_home())
    await cb.answer()


@router.callback_query(F.data == "close")
async def close(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Сессия завершена. Нажмите /start для новой сессии.", reply_markup=None)
    await cb.answer()
