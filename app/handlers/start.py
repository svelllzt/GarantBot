from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.buttons import Theme
from app.config import Settings
from app.handlers.deals import present_start_deal
from app.i18n import t
from app.keyboards import LangCB, NavCB, home_kb, lang_kb, profile_kb
from app.storage import Storage
from app.util import is_cancel, paint, profile_text

router = Router()


async def show_menu(event: Message | CallbackQuery, db: Storage, lang: str, theme: Theme, greeting: str | None = None, settings=None):
    markup = await home_kb(db, event.from_user.id, lang, theme)
    await paint(event, greeting or t(lang, "menu"), markup, screen="menu", settings=settings)


async def _after_start(event, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings, ton):
    data = await state.get_data()
    payload = data.get("start_payload")
    if payload:
        await state.update_data(start_payload=None)
        if await present_start_deal(event, db, lang, settings, theme, ton, payload):
            return
    await show_menu(
        event,
        db,
        lang,
        theme,
        t(lang, "welcome", name=event.from_user.first_name or ""),
        settings=settings,
    )


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    db: Storage,
    db_user,
    lang: str,
    theme: Theme,
    settings: Settings,
    ton,
):
    payload = (command.args or "").strip()
    await state.clear()
    if payload:
        await state.update_data(start_payload=payload)
    wipe = await message.answer("\u2060", reply_markup=ReplyKeyboardRemove())
    try:
        await wipe.delete()
    except Exception:
        pass
    if not db_user["lang"]:
        await message.answer(t("ru", "choose_lang"), reply_markup=lang_kb(theme))
        return
    await _after_start(message, state, db, lang, theme, settings, ton)


@router.callback_query(LangCB.filter())
async def set_lang(call: CallbackQuery, callback_data: LangCB, state: FSMContext, db: Storage, theme: Theme, settings: Settings, ton):
    lang = callback_data.code
    await db.set_lang(call.from_user.id, lang)
    await _after_start(call, state, db, lang, theme, settings, ton)


@router.callback_query(NavCB.filter(F.a == "menu"))
async def nav_menu(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    await state.clear()
    await show_menu(call, db, lang, theme, settings=settings)


@router.callback_query(NavCB.filter(F.a == "fsmx"))
@router.message(Command("cancel"))
@router.message(F.text.func(lambda text: isinstance(text, str) and is_cancel(text)))
async def cancel_fsm(event: Message | CallbackQuery, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    await state.clear()
    await show_menu(event, db, lang, theme, t(lang, "cancelled"), settings=settings)


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
        screen="about",
        settings=settings,
    )


@router.callback_query(NavCB.filter(F.a == "profile"))
async def profile(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    await state.clear()
    user = await db.get_user(call.from_user.id)
    await paint(
        call,
        profile_text(user, lang, settings.currency),
        profile_kb(lang, theme),
        screen="profile",
        settings=settings,
    )
