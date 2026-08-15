import secrets

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.i18n import t
from app.keyboards import NavCB, WalletCB, deposit_kb, lang_kb, main_menu, profile_kb, requisites_kb, withdraw_method_kb
from app.services.ton import incoming_by_comment, ton_to_currency
from app.states import Requisites, Wallet
from app.storage import WALLET_DONE, WALLET_PENDING, Storage
from app.util import is_cancel, parse_amount, profile_text, valid_card, valid_phone, valid_ton

router = Router()


def _restore(lang: str, deal_id=None):
    return main_menu(lang, deal_id)


@router.callback_query(NavCB.filter(F.a == "profile"))
async def back_profile(call: CallbackQuery, db: Storage, lang: str, settings: Settings):
    user = await db.get_user(call.from_user.id)
    await call.message.edit_text(profile_text(user, lang, settings.currency), reply_markup=profile_kb(lang))
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "req"))
async def requisites(call: CallbackQuery, lang: str):
    await call.message.edit_text(t(lang, "req_menu"), reply_markup=requisites_kb(lang))
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "lang"))
async def change_lang(call: CallbackQuery):
    await call.message.edit_text(t("ru", "choose_lang"), reply_markup=lang_kb())
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "req_card"))
async def ask_card(call: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(Requisites.card)
    await call.message.answer(t(lang, "req_ask_card"), reply_markup=_restore(lang))
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "req_phone"))
async def ask_phone(call: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(Requisites.phone)
    await call.message.answer(t(lang, "req_ask_phone"))
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "req_ton"))
async def ask_ton(call: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(Requisites.ton)
    await call.message.answer(t(lang, "req_ask_ton"))
    await call.answer()


@router.message(Requisites.card)
async def save_card(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    number = (message.text or "").replace(" ", "")
    if not valid_card(number):
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_requisite(message.from_user.id, "card", number)
    await state.clear()
    await message.answer(t(lang, "req_saved"), reply_markup=requisites_kb(lang))


@router.message(Requisites.phone)
async def save_phone(message: Message, state: FSMContext, lang: str):
    if is_cancel(message.text or ""):
        return
    phone = (message.text or "").strip()
    if not valid_phone(phone):
        await message.answer(t(lang, "req_bad"))
        return
    await state.update_data(phone=phone)
    await state.set_state(Requisites.bank)
    await message.answer(t(lang, "req_ask_bank"))


@router.message(Requisites.bank)
async def save_bank(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer(t(lang, "req_bad"))
        return
    data = await state.get_data()
    await db.set_requisite(message.from_user.id, "phone", data["phone"])
    await db.set_requisite(message.from_user.id, "bank_name", name)
    await state.clear()
    await message.answer(t(lang, "req_saved"), reply_markup=requisites_kb(lang))


@router.message(Requisites.ton)
async def save_ton(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    address = (message.text or "").strip()
    if not valid_ton(address):
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_requisite(message.from_user.id, "ton_address", address)
    await state.clear()
    await message.answer(t(lang, "req_saved"), reply_markup=requisites_kb(lang))


@router.callback_query(NavCB.filter(F.a == "dep"))
async def ask_deposit(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    await state.set_state(Wallet.deposit_amount)
    await call.message.answer(
        t(lang, "deposit_ask", currency=settings.currency, min=f"{settings.min_deposit:.2f}")
    )
    await call.answer()


@router.message(Wallet.deposit_amount)
async def make_deposit(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if is_cancel(message.text or ""):
        return
    amount = parse_amount(message.text or "")
    if amount is None or amount < settings.min_deposit:
        await message.answer(t(lang, "min_amount", min=f"{settings.min_deposit:.2f}", currency=settings.currency))
        return
    comment = f"G{message.from_user.id}{secrets.randbelow(9000) + 1000}"
    deposit_id = await db.create_deposit(message.from_user.id, amount, comment)
    extra = (
        t(lang, "deposit_ton", address=settings.ton_address)
        if settings.ton_address
        else t(lang, "deposit_manual", support=settings.support_username.lstrip("@"))
    )
    await state.clear()
    await message.answer(
        t(
            lang,
            "deposit_created",
            id=deposit_id,
            amount=f"{amount:.2f}",
            currency=settings.currency,
            comment=comment,
            extra=extra,
        ),
        reply_markup=deposit_kb(lang, deposit_id),
    )


@router.callback_query(WalletCB.filter(F.a == "chk"))
async def check_deposit(call: CallbackQuery, callback_data: WalletCB, db: Storage, lang: str, settings: Settings):
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None or deposit["user_id"] != call.from_user.id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deposit["status"] == WALLET_DONE:
        await call.answer(t(lang, "deposit_ok", amount=f"{deposit['amount']:.2f}", currency=settings.currency), show_alert=True)
        return
    if deposit["status"] != WALLET_PENDING:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    ton_amount = await incoming_by_comment(settings, deposit["comment"])
    credited = ton_to_currency(ton_amount, settings, float(deposit["amount"])) if ton_amount else None
    if credited is None:
        await call.answer(t(lang, "deposit_wait"), show_alert=True)
        return
    await db.finish_deposit(deposit["id"], WALLET_DONE)
    await db.change_balance(call.from_user.id, float(deposit["amount"]))
    await call.message.edit_text(
        t(lang, "deposit_ok", amount=f"{deposit['amount']:.2f}", currency=settings.currency)
    )
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "wd"))
async def ask_withdraw(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    await state.set_state(Wallet.withdraw_amount)
    await call.message.answer(
        t(lang, "withdraw_ask", currency=settings.currency, min=f"{settings.min_withdraw:.2f}")
    )
    await call.answer()


@router.message(Wallet.withdraw_amount)
async def withdraw_amount(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if is_cancel(message.text or ""):
        return
    amount = parse_amount(message.text or "")
    if amount is None or amount < settings.min_withdraw:
        await message.answer(t(lang, "min_amount", min=f"{settings.min_withdraw:.2f}", currency=settings.currency))
        return
    user = await db.get_user(message.from_user.id)
    if float(user["balance"]) < amount:
        await message.answer(t(lang, "withdraw_low"))
        await state.clear()
        return
    await state.update_data(amount=amount)
    await state.set_state(None)
    await message.answer(t(lang, "withdraw_method"), reply_markup=withdraw_method_kb(lang))


@router.callback_query(WalletCB.filter(F.a == "wdm"))
async def withdraw_method(call: CallbackQuery, callback_data: WalletCB, state: FSMContext, db: Storage, lang: str, settings: Settings):
    data = await state.get_data()
    amount = data.get("amount")
    if not amount:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    user = await db.get_user(call.from_user.id)
    method = callback_data.m
    if method == "card":
        details = user["card"]
    elif method == "phone":
        details = f"{user['phone'] or ''} / {user['bank_name'] or ''}".strip(" /")
    else:
        details = user["ton_address"]
    if not details:
        await call.answer(t(lang, "withdraw_no_req"), show_alert=True)
        return
    try:
        await db.change_balance(call.from_user.id, -float(amount))
    except ValueError:
        await call.answer(t(lang, "withdraw_low"), show_alert=True)
        return
    wid = await db.create_withdraw(call.from_user.id, float(amount), method, details)
    await state.clear()
    await call.message.edit_text(
        t(lang, "withdraw_ok", id=wid, amount=f"{amount:.2f}", currency=settings.currency, details=details)
    )
    await call.answer()
    for admin_id in settings.admins:
        try:
            await call.bot.send_message(
                admin_id,
                t("ru", "admin_wd_line", id=wid, amount=f"{amount:.2f}", currency=settings.currency, method=method, details=details, user=call.from_user.id),
            )
        except Exception:
            pass
