from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.i18n import t
from app.keyboards import LangCB, lang_kb, main_menu, profile_kb
from app.storage import Storage
from app.util import is_cancel, profile_text

router = Router()

PROFILE = {t("ru", "btn_profile"), t("en", "btn_profile")}
ABOUT = {t("ru", "btn_about"), t("en", "btn_about")}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db: Storage, db_user, lang: str):
    await state.clear()
    if not db_user["lang"]:
        await message.answer(t("ru", "choose_lang"), reply_markup=lang_kb())
        return
    active = await db.active_deal(message.from_user.id)
    await message.answer(
        t(lang, "welcome", name=message.from_user.first_name or ""),
        reply_markup=main_menu(lang, active["id"] if active else None),
    )


@router.callback_query(LangCB.filter())
async def set_lang(call: CallbackQuery, callback_data: LangCB, db: Storage):
    lang = callback_data.code
    await db.set_lang(call.from_user.id, lang)
    active = await db.active_deal(call.from_user.id)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        t(lang, "welcome", name=call.from_user.first_name or ""),
        reply_markup=main_menu(lang, active["id"] if active else None),
    )
    await call.answer()


@router.message(Command("cancel"))
@router.message(F.text.func(lambda text: isinstance(text, str) and is_cancel(text)))
async def cancel_fsm(message: Message, state: FSMContext, db: Storage, lang: str):
    await state.clear()
    active = await db.active_deal(message.from_user.id)
    await message.answer(t(lang, "cancelled"), reply_markup=main_menu(lang, active["id"] if active else None))


@router.message(F.text.in_(ABOUT))
async def about(message: Message, lang: str, settings: Settings):
    await message.answer(
        t(
            lang,
            "about",
            commission=settings.commission_percent,
            support=settings.support_username.lstrip("@"),
            chat=settings.support_chat or "",
        )
    )


@router.message(F.text.in_(PROFILE))
async def profile(message: Message, db: Storage, lang: str, settings: Settings):
    user = await db.get_user(message.from_user.id)
    await message.answer(profile_text(user, lang, settings.currency), reply_markup=profile_kb(lang))
