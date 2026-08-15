from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.buttons import Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import LangCB, NavCB, home_kb, lang_kb, profile_kb
from app.storage import Storage
from app.util import is_cancel, paint, profile_text

router = Router()


async def show_menu(event: Message | CallbackQuery, db: Storage, lang: str, theme: Theme, greeting: str | None = None):
    markup = await home_kb(db, event.from_user.id, lang, theme)
    await paint(event, greeting or t(lang, "menu"), markup)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Storage, db_user, lang: str, theme: Theme):
    await state.clear()
    wipe = await message.answer("\u2060", reply_markup=ReplyKeyboardRemove())
    try:
        await wipe.delete()
    except Exception:
        pass
    if not db_user["lang"]:
        await message.answer(t("ru", "choose_lang"), reply_markup=lang_kb(theme))
        return
    await show_menu(
        message,
        db,
        lang,
        theme,
        t(lang, "welcome", name=message.from_user.first_name or ""),
    )


@router.callback_query(LangCB.filter())
async def set_lang(call: CallbackQuery, callback_data: LangCB, db: Storage, theme: Theme):
    lang = callback_data.code
    await db.set_lang(call.from_user.id, lang)
    await show_menu(
        call,
        db,
        lang,
        theme,
        t(lang, "welcome", name=call.from_user.first_name or ""),
    )


@router.callback_query(NavCB.filter(F.a == "menu"))
async def nav_menu(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, theme: Theme):
    await state.clear()
    await show_menu(call, db, lang, theme)


@router.callback_query(NavCB.filter(F.a == "fsmx"))
@router.message(Command("cancel"))
@router.message(F.text.func(lambda text: isinstance(text, str) and is_cancel(text)))
async def cancel_fsm(event: Message | CallbackQuery, state: FSMContext, db: Storage, lang: str, theme: Theme):
    await state.clear()
    await show_menu(event, db, lang, theme, t(lang, "cancelled"))


@router.callback_query(NavCB.filter(F.a == "about"))
async def about(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    await paint(
        call,
        t(
            lang,
            "about",
            commission=settings.commission_percent,
            support=settings.support_username.lstrip("@"),
            chat=settings.support_chat or "",
        ),
        kb.as_markup(),
    )


@router.callback_query(NavCB.filter(F.a == "profile"))
async def profile(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    await state.clear()
    user = await db.get_user(call.from_user.id)
    await paint(call, profile_text(user, lang, settings.currency), profile_kb(lang, theme))
