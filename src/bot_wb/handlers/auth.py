from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from ..ui.keyboards import kb_auth_stub, kb_home, kb_logout
from ..ui import texts
from ..services.auth_service import AuthService
from ..storage.repo import UserRepo

router = Router(name=__name__)
_repo = UserRepo()
_auth = AuthService(_repo)


async def _edit_flow_message(message: Message, state: FSMContext, text: str, reply_markup=None):
    data = await state.get_data()
    chat_id = data.get("chat_id", message.chat.id)
    message_id = data.get("message_id")
    if message_id:
        await message.bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup,
        )
    else:
        sent = await message.answer(text, reply_markup=reply_markup)
        await state.update_data(chat_id=sent.chat.id, message_id=sent.message_id)


async def _delete_user_message(message: Message):
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


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
        await state.update_data(chat_id=cb.message.chat.id, message_id=cb.message.message_id)
        await cb.answer()
        return

    await cb.message.edit_text(texts.ask_phone_text(), reply_markup=kb_auth_stub())
    await state.update_data(chat_id=cb.message.chat.id, message_id=cb.message.message_id)
    await state.set_state(AuthFSM.waiting_phone)
    await cb.answer()


@router.message(AuthFSM.waiting_phone)
async def got_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.startswith("+") or not phone[1:].isdigit() or len(phone) < 12:
        await _edit_flow_message(
            message,
            state,
            "❌ Неверный формат номера. Пример: +79991234567\n\n" + texts.ask_phone_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    ok = await _auth.start_by_phone(message.from_user.id, phone)
    if not ok:
        await _edit_flow_message(
            message,
            state,
            "⚠️ Не удалось отправить код. Попробуйте позже.\n\n" + texts.ask_phone_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    await _edit_flow_message(message, state, texts.ask_sms_code_text(), kb_auth_stub())
    await state.set_state(AuthFSM.waiting_sms_code)
    await _delete_user_message(message)


@router.message(AuthFSM.waiting_sms_code)
async def got_sms(message: Message, state: FSMContext):
    code = message.text.strip()
    if not code.isdigit():
        await _edit_flow_message(
            message,
            state,
            "Код должен содержать только цифры.\n\n" + texts.ask_sms_code_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    ok = await _auth.confirm_sms(message.from_user.id, code)
    if not ok:
        await _edit_flow_message(
            message,
            state,
            "Неверный код или ошибка сервера. Попробуйте ещё раз.\n\n" + texts.ask_sms_code_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    await _edit_flow_message(message, state, texts.ask_email_text(), kb_auth_stub())
    await state.set_state(AuthFSM.waiting_email)
    await _delete_user_message(message)


@router.message(AuthFSM.waiting_email)
async def got_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email or "." not in email:
        await _edit_flow_message(
            message,
            state,
            "Неверный e-mail. Пример: user@example.com\n\n" + texts.ask_email_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    ok = await _auth.submit_email(message.from_user.id, email)
    if not ok:
        await _edit_flow_message(
            message,
            state,
            "Не удалось запросить код на e-mail. Попробуйте позже.\n\n" + texts.ask_email_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    await _edit_flow_message(message, state, texts.ask_email_code_text(), kb_auth_stub())
    await state.set_state(AuthFSM.waiting_email_code)
    await _delete_user_message(message)


@router.message(AuthFSM.waiting_email_code)
async def got_email_code(message: Message, state: FSMContext):
    code = message.text.strip()
    if not code:
        await _edit_flow_message(
            message,
            state,
            "Введите код из письма.\n\n" + texts.ask_email_code_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    ok = await _auth.confirm_email(message.from_user.id, code)
    if not ok:
        await _edit_flow_message(
            message,
            state,
            "Код не подошёл или ошибка сервера. Попробуйте снова.\n\n" + texts.ask_email_code_text(),
            kb_auth_stub(),
        )
        await _delete_user_message(message)
        return

    await _edit_flow_message(message, state, texts.auth_success_text(), kb_logout())
    await state.clear()
    await _delete_user_message(message)


@router.callback_query(F.data == "logout")
async def logout(cb: CallbackQuery, state: FSMContext):
    await _auth.logout(cb.from_user.id)
    await state.clear()
    await cb.message.edit_text(texts.logout_done_text(), reply_markup=None)
    await cb.answer()


@router.callback_query(F.data == "home")
async def to_home(cb: CallbackQuery):
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    await cb.message.edit_text(texts.home_text(user_name), reply_markup=kb_home())
    await cb.answer()


@router.callback_query(F.data == "refresh")
async def refresh(cb: CallbackQuery):
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    await cb.message.edit_text(texts.home_text(user_name), reply_markup=kb_home())
    await cb.answer()


@router.callback_query(F.data == "close")
async def close(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Сессия завершена. Нажмите /start для новой сессии.", reply_markup=None)
    await cb.answer()
