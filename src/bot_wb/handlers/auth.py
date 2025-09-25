from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot_wb.logging import logger
from bot_wb.services.auth_service import AuthService
from bot_wb.storage.repo import UserRepo
from bot_wb.ui import texts
from bot_wb.ui.keyboards import kb_home

from ._render import render_home

router = Router(name=__name__)
_repo = UserRepo()
_auth = AuthService(_repo)


@router.callback_query(F.data == "auth")
async def on_auth(cb: CallbackQuery, state: FSMContext):
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    auth_prompt = (
        "Открыл окно входа WB Seller.\n"
        "Пожалуйста, авторизуйтесь в появившемся окне "
        "(телефон → SMS → код с e-mail).\n\n"
        "Окно останется открытым до успешного входа или таймаута, "
        "не закрывайте его вручную."
    )

    message_obj = cb.message
    if message_obj and hasattr(message_obj, "edit_text"):
        await message_obj.edit_text(auth_prompt, reply_markup=None)
    await state.clear()
    await cb.answer()

    if cb.bot is None:
        raise RuntimeError("Callback does not contain bot instance")

    logger.info(
        "User {} requested interactive auth",
        cb.from_user.id if cb.from_user else "?",
    )
    ok = await _auth.interactive_login(cb.from_user.id)
    chat = getattr(message_obj, "chat", None)
    chat_id = getattr(chat, "id", cb.from_user.id)

    if ok:
        await render_home(cb.bot, chat_id, user_name, force_replace=True)
        logger.info("Auth flow completed successfully for user {}", cb.from_user.id)
    else:
        logger.warning("Auth flow failed for user {}", cb.from_user.id)
        failure_text = (
            "Не удалось завершить авторизацию. "
            "Попробуйте ещё раз: нажмите «Авторизация»."
        )
        if message_obj and hasattr(message_obj, "edit_text"):
            try:
                await message_obj.edit_text(
                    failure_text,
                    reply_markup=kb_home(authorized=False),
                )
            except TelegramBadRequest:
                if hasattr(message_obj, "answer"):
                    msg = await message_obj.answer(
                        failure_text,
                        reply_markup=kb_home(authorized=False),
                    )
                    await _repo.set_anchor(cb.from_user.id, msg.message_id)
                else:
                    msg = await cb.bot.send_message(
                        chat_id,
                        failure_text,
                        reply_markup=kb_home(authorized=False),
                    )
                    await _repo.set_anchor(cb.from_user.id, msg.message_id)
        else:
            msg = await cb.bot.send_message(
                chat_id,
                failure_text,
                reply_markup=kb_home(authorized=False),
            )
            await _repo.set_anchor(cb.from_user.id, msg.message_id)


@router.callback_query(F.data == "logout")
async def logout(cb: CallbackQuery, state: FSMContext):
    if cb.bot is None:
        raise RuntimeError("Callback does not contain bot instance")
    await _auth.logout(cb.from_user.id)
    await state.clear()
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    chat = getattr(cb.message, "chat", None)
    chat_id = getattr(chat, "id", cb.from_user.id)
    await render_home(cb.bot, chat_id, user_name, force_replace=True)
    await cb.answer()


@router.callback_query(F.data == "close")
async def close(cb: CallbackQuery, state: FSMContext):
    if cb.bot is None:
        raise RuntimeError("Callback does not contain bot instance")
    await state.clear()
    await _repo.set_view(cb.from_user.id, None)
    anchor = await _repo.get_anchor(cb.from_user.id)
    text = texts.logout_done_text()
    message_obj = cb.message
    if anchor:
        chat = getattr(cb.message, "chat", None)
        chat_id = getattr(chat, "id", cb.from_user.id)
        await cb.bot.edit_message_text(text=text, chat_id=chat_id, message_id=anchor)
    elif isinstance(message_obj, Message):
        await message_obj.edit_text(text)
    await cb.answer()
