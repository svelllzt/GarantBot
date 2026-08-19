import secrets

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.buttons import Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import NavCB, WalletCB, asset_pick_kb, cancel_kb, deposit_kb, lang_kb, requisites_kb
from app.services.ton import incoming_by_comment, incoming_usdt_by_comment
from app.states import Requisites, Wallet
from app.storage import WALLET_DONE, WALLET_PENDING, Storage
from app.util import is_cancel, money_asset, paint, parse_amount, parse_ton, valid_ton

router = Router()


def _min_dep(settings: Settings, asset: str) -> float:
    if asset == "TON":
        return float(settings.min_deposit_ton or settings.min_ton_deal or 0.1)
    return float(settings.min_deposit)


def _min_wd(settings: Settings, asset: str) -> float:
    if asset == "TON":
        return float(settings.min_withdraw_ton or settings.min_ton_deal or 0.1)
    return float(settings.min_withdraw)


def _parse(text: str, asset: str) -> float | None:
    if asset == "TON":
        return parse_ton(text)
    return parse_amount(text)


@router.callback_query(NavCB.filter(F.a == "req"))
async def requisites(call: CallbackQuery, lang: str, theme: Theme, settings: Settings):
    await paint(call, t(lang, "req_menu"), requisites_kb(lang, theme), screen="requisites", settings=settings)


@router.callback_query(NavCB.filter(F.a == "lang"))
async def change_lang(call: CallbackQuery, theme: Theme, settings: Settings):
    await paint(call, t("ru", "choose_lang"), lang_kb(theme), screen="profile", settings=settings)


@router.callback_query(NavCB.filter(F.a == "req_ton"))
async def ask_ton(call: CallbackQuery, state: FSMContext, lang: str, theme: Theme):
    await state.set_state(Requisites.ton)
    await call.message.answer(t(lang, "req_ask_ton"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(Requisites.ton)
async def save_ton(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    address = (message.text or "").strip()
    if not valid_ton(address):
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_requisite(message.from_user.id, "ton_address", address)
    await state.clear()
    await message.answer(t(lang, "req_saved"), reply_markup=requisites_kb(lang, theme))


@router.callback_query(NavCB.filter(F.a == "dep"))
async def pick_deposit_asset(call: CallbackQuery, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    await state.clear()
    await paint(call, t(lang, "deposit_pick"), asset_pick_kb(lang, theme, "dasset"), screen="profile", settings=settings)


@router.callback_query(WalletCB.filter(F.a == "dasset"))
async def ask_deposit(call: CallbackQuery, callback_data: WalletCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    asset = "TON" if callback_data.m == "TON" else "USDT"
    await state.update_data(asset=asset)
    await state.set_state(Wallet.deposit_amount)
    await call.message.answer(
        t(lang, "deposit_ask", currency=asset, min=money_asset(_min_dep(settings, asset), asset)),
        reply_markup=cancel_kb(lang, theme),
    )
    await call.answer()


@router.message(Wallet.deposit_amount)
async def make_deposit(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    asset = "TON" if data.get("asset") == "TON" else "USDT"
    amount = _parse(message.text or "", asset)
    minimum = _min_dep(settings, asset)
    if amount is None or amount < minimum:
        await message.answer(t(lang, "min_amount", min=money_asset(minimum, asset), currency=asset))
        return
    comment = ""
    deposit_id = None
    for _ in range(8):
        comment = f"G{message.from_user.id}{secrets.randbelow(9000) + 1000}"
        try:
            deposit_id = await db.create_deposit(message.from_user.id, amount, comment, asset)
            break
        except Exception:
            deposit_id = None
    if not deposit_id:
        await message.answer(t(lang, "error"))
        return
    extra = (
        t(lang, "deposit_usdt_net" if asset == "USDT" else "deposit_ton", address=settings.ton_address)
        if settings.ton_address
        else t(lang, "deposit_manual", support=settings.support_username.lstrip("@"))
    )
    await state.clear()
    await message.answer(
        t(
            lang,
            "deposit_created",
            id=deposit_id,
            amount=money_asset(amount, asset),
            currency=asset,
            comment=comment,
            extra=extra,
        ),
        reply_markup=deposit_kb(lang, theme, deposit_id),
    )


@router.callback_query(WalletCB.filter(F.a == "chk"))
async def check_deposit(call: CallbackQuery, callback_data: WalletCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None or deposit["user_id"] != call.from_user.id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    asset = "USDT"
    try:
        asset = (deposit["asset"] or "USDT").upper()
    except (KeyError, IndexError, TypeError):
        asset = "USDT"
    if asset != "TON":
        asset = "USDT"
    if deposit["status"] == WALLET_DONE:
        await call.answer(
            t(lang, "deposit_ok", amount=money_asset(deposit["amount"], asset), currency=asset),
            show_alert=True,
        )
        return
    if deposit["status"] != WALLET_PENDING:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    need = float(deposit["amount"])
    if asset == "TON":
        got = await incoming_by_comment(settings, deposit["comment"])
    else:
        got = await incoming_usdt_by_comment(settings, deposit["comment"])
    if got is None or got + 1e-9 < need:
        await call.answer(t(lang, "deposit_wait"), show_alert=True)
        return
    if not await db.claim_deposit(deposit["id"], WALLET_DONE):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    try:
        await db.credit_asset(call.from_user.id, asset, got)
    except Exception:
        await db.finish_deposit(deposit["id"], WALLET_PENDING)
        await call.answer(t(lang, "error"), show_alert=True)
        return
    from app.keyboards import home_kb

    await paint(
        call,
        t(lang, "deposit_ok", amount=money_asset(got, asset), currency=asset),
        await home_kb(db, call.from_user.id, lang, theme),
        screen="menu",
        settings=settings,
    )


@router.callback_query(NavCB.filter(F.a == "wd"))
async def pick_withdraw_asset(call: CallbackQuery, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    await state.clear()
    await paint(call, t(lang, "withdraw_pick"), asset_pick_kb(lang, theme, "wasset"), screen="profile", settings=settings)


@router.callback_query(WalletCB.filter(F.a == "wasset"))
async def ask_withdraw(call: CallbackQuery, callback_data: WalletCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    asset = "TON" if callback_data.m == "TON" else "USDT"
    await state.update_data(asset=asset)
    await state.set_state(Wallet.withdraw_amount)
    await call.message.answer(
        t(lang, "withdraw_ask", currency=asset, min=money_asset(_min_wd(settings, asset), asset)),
        reply_markup=cancel_kb(lang, theme),
    )
    await call.answer()


@router.message(Wallet.withdraw_amount)
async def withdraw_amount(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    asset = "TON" if data.get("asset") == "TON" else "USDT"
    amount = _parse(message.text or "", asset)
    minimum = _min_wd(settings, asset)
    if amount is None or amount < minimum:
        await message.answer(t(lang, "min_amount", min=money_asset(minimum, asset), currency=asset))
        return
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer(t(lang, "error"))
        await state.clear()
        return
    available = db.available(user, asset)
    if available + 1e-12 < amount:
        frozen = db.frozen_of(user, asset)
        if frozen > 0:
            await message.answer(t(lang, "withdraw_frozen", have=money_asset(available, asset), frozen=money_asset(frozen, asset), currency=asset))
        else:
            await message.answer(t(lang, "withdraw_low"))
        await state.clear()
        return
    dest = (user["ton_address"] or "").strip()
    await state.update_data(amount=amount, asset=asset)
    if dest and valid_ton(dest):
        await _place_withdraw(message, state, db, lang, settings, theme, dest)
        return
    await state.set_state(Wallet.withdraw_ton)
    await message.answer(t(lang, "req_ask_ton"), reply_markup=cancel_kb(lang, theme))


@router.message(Wallet.withdraw_ton)
async def withdraw_ton_addr(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    address = (message.text or "").strip()
    if not valid_ton(address):
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_requisite(message.from_user.id, "ton_address", address)
    await _place_withdraw(message, state, db, lang, settings, theme, address)


async def _place_withdraw(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, dest: str) -> None:
    data = await state.get_data()
    asset = "TON" if data.get("asset") == "TON" else "USDT"
    amount = float(data.get("amount") or 0)
    if amount <= 0:
        await message.answer(t(lang, "error"))
        await state.clear()
        return
    try:
        await db.spend_available(message.from_user.id, asset, amount)
    except ValueError:
        await message.answer(t(lang, "withdraw_low"))
        await state.clear()
        return
    try:
        wid = await db.create_withdraw(message.from_user.id, amount, "ton", dest, asset)
    except ValueError:
        await db.credit_asset(message.from_user.id, asset, amount)
        await message.answer(t(lang, "withdraw_busy"))
        await state.clear()
        return
    await state.clear()
    from app.keyboards import home_kb

    await message.answer(
        t(lang, "withdraw_ok", id=wid, amount=money_asset(amount, asset), currency=asset, details=dest),
        reply_markup=await home_kb(db, message.from_user.id, lang, theme),
    )
