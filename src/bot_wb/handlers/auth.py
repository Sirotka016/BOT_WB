from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from ..services.auth_service import AuthService
from ..storage.repo import UserRepo
from ..ui import texts
from ..ui.keyboards import kb_auth_stub, kb_home, kb_logout

router = Router(name=__name__)
_repo = UserRepo()
_auth = AuthService(_repo)


class AuthFSM(StatesGroup):
    waiting_phone = State()
    waiting_sms_code = State()
    waiting_email = State()
    waiting_email_code = State()


@router.callback_query(F.data == "auth")
async def on_auth(cb: CallbackQuery, state: FSMContext):
    tg_id = cb.from_user.id
    if await _auth.is_authorized(tg_id):
        await cb.message.edit_text(texts.logged_in_text(), reply_markup=kb_logout())
    else:
        # открываем кабинет заранее, чтобы ускорить шаг 1
        await _auth.start_partner(tg_id)
        await cb.message.edit_text(texts.ask_phone_text(), reply_markup=kb_auth_stub())
        await state.set_state(AuthFSM.waiting_phone)
    await cb.answer()


@router.message(AuthFSM.waiting_phone)
async def got_phone(m: Message, state: FSMContext):
    phone = (m.text or "").strip()
    if not (phone.startswith("+") and phone[1:].isdigit() and len(phone) >= 12):
        await m.reply("Неверный формат. Пример: +79991234567")
        return
    await _auth.submit_phone(m.from_user.id, phone)
    await m.answer(texts.ask_sms_code_text())
    await state.set_state(AuthFSM.waiting_sms_code)


@router.message(AuthFSM.waiting_sms_code)
async def got_sms(m: Message, state: FSMContext):
    code = (m.text or "").strip()
    if not code.isdigit():
        await m.reply("Код должен содержать только цифры.")
        return
    await _auth.submit_sms(m.from_user.id, code)
    await m.answer(texts.ask_email_text())
    await state.set_state(AuthFSM.waiting_email)


@router.message(AuthFSM.waiting_email)
async def got_email(m: Message, state: FSMContext):
    email = (m.text or "").strip()
    if "@" not in email or "." not in email:
        await m.reply("Неверный e-mail. Пример: user@example.com")
        return
    await _auth.submit_email(m.from_user.id, email)
    await m.answer(texts.ask_email_code_text())
    await state.set_state(AuthFSM.waiting_email_code)


@router.message(AuthFSM.waiting_email_code)
async def got_email_code(m: Message, state: FSMContext):
    code = (m.text or "").strip()
    if not code:
        await m.reply("Введите код из письма.")
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
