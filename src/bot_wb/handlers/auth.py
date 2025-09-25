from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from ..services.auth_service import AuthService
from ..storage.repo import UserRepo
from ..ui import texts
from ..ui.keyboards import kb_home
from ._render import render_home, render_profile

router = Router(name=__name__)
_repo = UserRepo()
_auth = AuthService(_repo)


@router.callback_query(F.data == "auth")
async def on_auth(cb: CallbackQuery, state: FSMContext):
    user_name = cb.from_user.full_name if cb.from_user else "друг"

    await cb.message.edit_text(
        "Открыл окно входа WB Seller.\n"
        "Пожалуйста, авторизуйтесь в появившемся окне (телефон → SMS → код с e-mail).\n\n"
        "После завершения здесь появится подтверждение.",
        reply_markup=None,
    )
    await state.clear()
    await cb.answer()

    ok = await _auth.interactive_login(cb.from_user.id)

    if ok:
        await render_home(cb.bot, cb.message.chat.id, user_name)
    else:
        await cb.message.edit_text(
            "Не удалось завершить авторизацию. Попробуйте ещё раз: нажмите «Авторизация».",
            reply_markup=kb_home(authorized=False),
        )


@router.callback_query(F.data == "profile")
async def on_profile(cb: CallbackQuery):
    await render_profile(cb.bot, cb.message.chat.id)
    await cb.answer()


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
    text = texts.logout_done_text()
    if anchor:
        await cb.bot.edit_message_text(
            text=text,
            chat_id=cb.message.chat.id,
            message_id=anchor,
        )
    else:
        await cb.message.edit_text(text)
    await cb.answer()
