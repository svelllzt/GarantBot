import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.buttons import KEYS, Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import (
    AdminCB,
    BtnCB,
    DealCB,
    NavCB,
    admin_bal_asset_kb,
    admin_kb,
    admins_kb,
    bans_kb,
    button_edit_kb,
    button_style_kb,
    buttons_list_kb,
    cancel_kb,
    cfg_fields_kb,
    dispute_admin_kb,
    faq_admin_item_kb,
    faq_admin_kb,
    screens_admin_kb,
    ticket_kb,
)
from app.catalog import label
from app.media import SCREENS
from app.services.bank import BankAccount
from app.services import deals as svc
from app.services.deals import DealError
from app.states import AdminFlow
from app.storage import WALLET_DONE, WALLET_PENDING, WALLET_REJECTED, WALLET_SENDING, Storage
from app.util import ban_notice, clean_ton, deal_asset, extract_emoji_id, is_cancel, money, money_asset, parse_amount, parse_ton, paint, valid_ton

router = Router()
_wd_locks: dict[int, asyncio.Lock] = {}


WALLET_FIELDS = (
    "ton_address",
    "ton_mnemonic",
    "ton_api_key",
    "usdt_master",
    "fragment_mnemonic",
    "fragment_wallet",
    "fragment_api_key",
)
SESSION_FIELDS = (
    "bank_api_id",
    "bank_api_hash",
    "bank_session",
    "bank_username",
    "fragment_cookies",
)
BOT_FIELDS = (
    "support_username",
    "support_chat",
    "required_channel",
    "deals_channel",
    "commission_percent",
    "service_id",
    "currency",
    "min_deposit",
    "min_withdraw",
    "min_deposit_ton",
    "min_withdraw_ton",
    "min_ton_deal",
    "min_rub_deal",
    "ton_rate",
    "ton_network",
    "ton_gas",
    "bank_transfer_stars",
    "bank_min_stars",
    "fragment_stars",
    "fragment_provider",
)
SECRET_FIELDS = {
    "ton_mnemonic",
    "ton_api_key",
    "fragment_mnemonic",
    "fragment_api_key",
    "bank_api_hash",
    "bank_session",
    "fragment_cookies",
}
TON_RELOAD = {"ton_address", "ton_mnemonic", "ton_api_key"}
BANK_RELOAD = {
    "fragment_mnemonic",
    "fragment_wallet",
    "fragment_api_key",
    "fragment_cookies",
    "bank_api_id",
    "bank_api_hash",
    "bank_session",
    "bank_username",
}
CFG_FIELDS = set(WALLET_FIELDS) | set(SESSION_FIELDS) | set(BOT_FIELDS)


def _ticket_asset(row) -> str:
    try:
        asset = (row["asset"] or "USDT").upper()
    except (KeyError, IndexError, TypeError):
        asset = "USDT"
    return "TON" if asset == "TON" else "USDT"


def _wd_lock(ticket_id: int) -> asyncio.Lock:
    lock = _wd_locks.get(ticket_id)
    if lock is None:
        lock = asyncio.Lock()
        _wd_locks[ticket_id] = lock
    return lock


def _admin(settings: Settings, user_id: int) -> bool:
    return settings.is_admin(user_id)


async def _deny(call: CallbackQuery, lang: str, settings: Settings) -> bool:
    if _admin(settings, call.from_user.id):
        return False
    await call.answer(t(lang, "admin_only"), show_alert=True)
    return True


async def _deny_msg(message: Message, lang: str, settings: Settings) -> bool:
    if _admin(settings, message.from_user.id):
        return False
    await message.answer(t(lang, "admin_only"))
    return True


def _mask(value: str, keep: int = 6) -> str:
    raw = (value or "").strip()
    if not raw:
        return "—"
    if len(raw) <= keep * 2:
        return raw[:2] + "…" if len(raw) > 2 else "…"
    return f"{raw[:keep]}…{raw[-keep:]}"


def _cfg_lines(settings: Settings, lang: str, fields: tuple[str, ...]) -> str:
    lines = []
    for key in fields:
        raw = getattr(settings, key, "")
        text = "" if raw is None else str(raw).strip()
        shown = _mask(text) if key in SECRET_FIELDS else (text or "—")
        lines.append(t(lang, "admin_cfg_value", title=t(lang, f"admin_cfg_{key}"), value=shown))
    return "\n\n".join(lines)


def _wallets_text(settings: Settings, lang: str) -> str:
    return t(lang, "admin_cfg_wallets_text", lines=_cfg_lines(settings, lang, WALLET_FIELDS))


def _sessions_text(settings: Settings, lang: str) -> str:
    return t(lang, "admin_cfg_sessions_text", lines=_cfg_lines(settings, lang, SESSION_FIELDS))


def _bot_text(settings: Settings, lang: str) -> str:
    return t(lang, "admin_cfg_bot_text", lines=_cfg_lines(settings, lang, BOT_FIELDS))


def _admins_text(settings: Settings, lang: str) -> str:
    ids = sorted(settings.admins)
    lines = "\n".join(f"<code>{uid}</code>" for uid in ids) or "—"
    return t(lang, "admin_cfg_admins_text", lines=lines)


def _save_admins(settings: Settings, ids: list[int]) -> None:
    unique = []
    seen = set()
    for uid in ids:
        if uid in seen or uid <= 0:
            continue
        seen.add(uid)
        unique.append(uid)
    settings.patch("admin_ids", ",".join(str(x) for x in unique))


@router.message(Command("admin"))
async def admin_entry(message: Message, lang: str, settings: Settings, theme: Theme):
    if await _deny_msg(message, lang, settings):
        return
    await message.answer(t(lang, "admin_menu"), reply_markup=admin_kb(lang, theme))


@router.callback_query(NavCB.filter(F.a == "admin"))
async def admin_nav(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(call, t(lang, "admin_menu"), admin_kb(lang, theme), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "stats"))
async def stats(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme, bank: BankAccount):
    if await _deny(call, lang, settings):
        return
    info = await db.stats()
    status_lines = []
    for status, count in sorted(info["by_status"].items()):
        status_lines.append(f"{t(lang, f'deal_status_{status}')}: {count}")
    cat_lines = []
    for cat, count in info["by_cat"]:
        cat_lines.append(f"{label(cat, lang)}: {count}")
    recent_rows = await db.recent_deals(12)
    recent_lines = []
    for deal in recent_rows:
        amount = money(deal["amount"]) if deal["amount"] is not None else "—"
        recent_lines.append(
            t(
                lang,
                "admin_deal_line",
                id=deal["id"],
                status=t(lang, f"deal_status_{deal['status']}"),
                cat=label(deal["category"] if "category" in deal.keys() else None, lang),
                amount=amount,
            )
        )
    fee = bank.fee
    stars_n = await bank.stars() if bank.online else None
    if not bank.online:
        stars_s = t(lang, "admin_stars_offline")
        left = "—"
    elif stars_n is None:
        stars_s = t(lang, "admin_stars_unknown")
        left = "—"
    else:
        stars_s = f"{stars_n}★"
        left = str(stars_n // fee) if fee else "—"
    pending_nft = len(await db.pending_nft_sends())
    svc_user = await db.get_user(settings.service_uid()) if settings.service_uid() else None
    await paint(
        call,
        t(
            lang,
            "admin_stats_text",
            users=info["users"],
            banned=info["banned"],
            deals=info["deals"],
            closed=info["closed"],
            disputes=info["disputes"],
            volume=f"{info['volume']:.2f}",
            escrow=f"{info['escrow']:.2f}",
            currency=settings.currency,
            bank=bank.mention,
            stars=stars_s,
            fragment=t(lang, bank.stars_buyer.status_key()),
            fee=fee,
            nft_left=left,
            pending_nft=pending_nft,
            svc_id=settings.service_uid() or "—",
            svc_usdt=money_asset(db.available(svc_user, "USDT") if svc_user else 0, "USDT"),
            svc_ton=money_asset(db.available(svc_user, "TON") if svc_user else 0, "TON"),
            by_status="\n".join(status_lines) or "—",
            by_cat="\n".join(cat_lines) or "—",
            recent="\n".join(recent_lines) or "—",
        ),
        admin_kb(lang, theme),
        settings=settings,
    )


@router.callback_query(AdminCB.filter(F.a == "ban"))
async def ask_ban(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.ban_id)
    await call.message.answer(t(lang, "admin_ask_ban"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "unban"))
async def ask_unban(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.unban_id)
    await call.message.answer(t(lang, "admin_ask_id"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.ban_id)
async def do_ban(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    raw = (message.text or "").strip()
    user = None
    if raw.isdigit():
        user = await db.get_user(int(raw))
    else:
        user = await db.get_user_by_username(raw)
    if user is None:
        await message.answer(t(lang, "admin_user_missing"))
        return
    await state.update_data(target_id=user["user_id"])
    await state.set_state(AdminFlow.ban_reason)
    await message.answer(t(lang, "admin_ask_ban_reason"), reply_markup=cancel_kb(lang, theme))


@router.message(AdminFlow.ban_reason)
async def do_ban_reason(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    reason = (message.text or "").strip()
    if reason in {"-", "—"}:
        reason = ""
    data = await state.get_data()
    uid = int(data["target_id"])
    await db.set_banned(uid, True, reason or None)
    await state.clear()
    await message.answer(t(lang, "admin_banned", id=uid))
    try:
        user = await db.get_user(uid)
        user_lang = (user["lang"] if user else None) or "ru"
        await message.bot.send_message(
            uid,
            ban_notice(user_lang, reason, settings.support_username),
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception:
        pass


@router.message(AdminFlow.unban_id)
async def do_unban(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    raw = (message.text or "").strip()
    user = None
    if raw.isdigit():
        user = await db.get_user(int(raw))
    else:
        user = await db.get_user_by_username(raw)
    if user is None:
        await message.answer(t(lang, "admin_user_missing"))
        return
    uid = int(user["user_id"])
    await db.set_banned(uid, False)
    await state.clear()
    await message.answer(t(lang, "admin_unbanned", id=uid))


@router.callback_query(AdminCB.filter(F.a == "bal"))
async def ask_balance_id(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.balance_id)
    await call.message.answer(t(lang, "admin_ask_id"))
    await call.answer()


@router.message(AdminFlow.balance_id)
async def ask_balance_asset(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    if not (message.text or "").isdigit():
        await message.answer(t(lang, "req_bad"))
        return
    user = await db.get_user(int(message.text))
    if user is None:
        await message.answer(t(lang, "admin_user_missing"))
        await state.clear()
        return
    await state.update_data(target_id=user["user_id"])
    await message.answer(t(lang, "admin_ask_balance_asset"), reply_markup=admin_bal_asset_kb(lang, theme))


@router.callback_query(AdminCB.filter(F.a == "balcur"))
async def ask_balance_amount(call: CallbackQuery, callback_data: AdminCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    asset = "TON" if callback_data.k == "TON" else "USDT"
    data = await state.get_data()
    if not data.get("target_id"):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.update_data(asset=asset)
    await state.set_state(AdminFlow.balance_amount)
    await paint(call, t(lang, "admin_ask_balance", currency=asset), cancel_kb(lang, theme), settings=settings)


@router.message(AdminFlow.balance_amount)
async def set_balance(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    asset = "TON" if data.get("asset") == "TON" else "USDT"
    amount = parse_ton(message.text or "") if asset == "TON" else parse_amount((message.text or "").lstrip("+"))
    if amount is None:
        await message.answer(t(lang, "req_bad"))
        return
    user = await db.get_user(int(data["target_id"]))
    if user is None:
        await message.answer(t(lang, "admin_user_missing"))
        await state.clear()
        return
    frozen = db.frozen_of(user, asset)
    if amount + 1e-12 < frozen:
        await message.answer(t(lang, "admin_balance_frozen", frozen=money_asset(frozen, asset), currency=asset))
        return
    await db.set_asset(int(data["target_id"]), asset, amount)
    await state.clear()
    await message.answer(t(lang, "admin_done"))


@router.callback_query(AdminCB.filter(F.a == "mail"))
async def ask_mail(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.mail)
    await call.message.answer(t(lang, "admin_ask_mail"))
    await call.answer()


@router.message(AdminFlow.mail)
async def send_mail(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    text = message.html_text or message.text or ""
    await state.clear()
    await message.answer(t(lang, "mail_started"))
    ok = fail = 0
    for user_id in await db.user_ids():
        try:
            await message.bot.send_message(user_id, text)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)
    await message.answer(t(lang, "mail_done", ok=ok, fail=fail))


@router.callback_query(AdminCB.filter(F.a == "disp"))
async def disputes(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    rows = await db.open_disputes()
    if not rows:
        await call.answer(t(lang, "admin_no_disputes"), show_alert=True)
        return
    for deal in rows:
        buyer = await db.get_user(deal["buyer_id"])
        seller = await db.get_user(deal["seller_id"])
        reason = ""
        try:
            reason = (deal["dispute_reason"] or "").strip()
        except (KeyError, IndexError, TypeError):
            reason = ""
        extra = f"\n{reason}" if reason else ""
        asset = deal_asset(deal)
        from app.handlers.deals import _thread_text
        thread = await _thread_text(db, deal["id"], lang, viewer_id=call.from_user.id, is_admin=True)
        body = t(
                lang,
                "deal_dispute_admin",
                id=deal["id"],
                buyer=buyer["username"] if buyer else "-",
                buyer_id=deal["buyer_id"],
                seller=seller["username"] if seller else "-",
                seller_id=deal["seller_id"],
                amount=money_asset(deal["amount"], asset),
                currency=asset,
                nft="—" if not deal["nft_id"] else str(deal["nft_id"]),
            ) + extra
        if thread:
            body = body + "\n\n" + thread
        await call.message.answer(
            body[:3500],
            reply_markup=dispute_admin_kb(lang, theme, deal["id"]),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "win_b"))
async def win_buyer(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, ton):
    if await _deny(call, lang, settings):
        return
    try:
        await svc.verdict_buyer(db, callback_data.i, ton, settings=settings)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    await db.add_dispute_msg(deal["id"], call.from_user.id, t(lang, "admin_verdict_buyer"), is_admin=True)
    await paint(call, t(lang, "admin_verdict_buyer"), settings=settings)
    for uid in (deal["seller_id"], deal["buyer_id"]):
        if not uid:
            continue
        user = await db.get_user(uid)
        if not user:
            continue
        try:
            await call.bot.send_message(
                uid,
                t(user["lang"] or "ru", "admin_verdict_buyer") + "\n" + t(user["lang"] or "ru", "deal_dispute_closed", id=deal["id"]),
            )
        except Exception:
            pass


@router.callback_query(AdminCB.filter(F.a == "win_s"))
async def win_seller(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, ton):
    if await _deny(call, lang, settings):
        return
    try:
        await svc.verdict_seller(db, settings, callback_data.i, ton)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    await db.add_dispute_msg(deal["id"], call.from_user.id, t(lang, "admin_verdict_seller"), is_admin=True)
    await paint(call, t(lang, "admin_verdict_seller"), settings=settings)
    for uid in (deal["seller_id"], deal["buyer_id"]):
        if not uid:
            continue
        user = await db.get_user(uid)
        if not user:
            continue
        try:
            await call.bot.send_message(
                uid,
                t(user["lang"] or "ru", "admin_verdict_seller") + "\n" + t(user["lang"] or "ru", "deal_dispute_closed", id=deal["id"]),
            )
        except Exception:
            pass
    from app.handlers.deals import notify_service_fee
    await notify_service_fee(call.bot, db, settings, deal)


@router.callback_query(AdminCB.filter(F.a == "deps"))
async def deposits(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    rows = await db.recent_deposits(15)
    if not rows:
        await call.answer(t(lang, "admin_empty_list"), show_alert=True)
        return
    lines = [t(lang, "admin_deposits_log"), ""]
    for row in rows:
        asset = _ticket_asset(row)
        lines.append(
            t(
                lang,
                "admin_dep_line",
                id=row["id"],
                amount=money_asset(row["amount"], asset),
                currency=asset,
                comment=row["comment"],
                user=row["user_id"],
            )
        )
    await paint(call, "\n".join(lines), admin_kb(lang, theme), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "wds"))
async def withdraws(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    rows = await db.pending_withdraws()
    if not rows:
        await call.answer(t(lang, "admin_empty_list"), show_alert=True)
        return
    for row in rows:
        asset = _ticket_asset(row)
        await call.message.answer(
            t(
                lang,
                "admin_wd_line",
                id=row["id"],
                amount=money_asset(row["amount"], asset),
                currency=asset,
                method=row["method"],
                details=row["details"],
                user=row["user_id"],
            ),
            reply_markup=ticket_kb("wd", row["id"], lang, theme),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "dep_ok"))
async def dep_ok(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if await _deny(call, lang, settings):
        return
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None or deposit["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if not await db.claim_deposit(deposit["id"], WALLET_DONE):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    asset = _ticket_asset(deposit)
    try:
        await db.credit_asset(deposit["user_id"], asset, float(deposit["amount"]))
    except Exception:
        await db.finish_deposit(deposit["id"], WALLET_PENDING)
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await paint(call, t(lang, "admin_dep_ok"), settings=settings)
    try:
        user = await db.get_user(deposit["user_id"])
        await call.bot.send_message(
            deposit["user_id"],
            t(user["lang"] or "ru", "deposit_ok", amount=money_asset(deposit["amount"], asset), currency=asset),
        )
    except Exception:
        pass


@router.callback_query(AdminCB.filter(F.a == "dep_no"))
async def dep_no(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if await _deny(call, lang, settings):
        return
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None or deposit["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if not await db.claim_deposit(deposit["id"], WALLET_REJECTED):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await paint(call, t(lang, "admin_dep_no"), settings=settings)
    try:
        user = await db.get_user(deposit["user_id"])
        asset = _ticket_asset(deposit)
        await call.bot.send_message(
            deposit["user_id"],
            t(
                (user["lang"] if user else None) or "ru",
                "deposit_rejected",
                id=deposit["id"],
                amount=money_asset(deposit["amount"], asset),
                currency=asset,
            ),
        )
    except Exception:
        pass


@router.callback_query(AdminCB.filter(F.a == "wd_ok"))
async def wd_ok(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, ton):
    if await _deny(call, lang, settings):
        return
    wid = int(callback_data.i)
    async with _wd_lock(wid):
        item = await db.get_withdraw(wid)
        if item is None or item["status"] not in {WALLET_PENDING, WALLET_SENDING}:
            await call.answer(t(lang, "error"), show_alert=True)
            return
        dest = clean_ton(item["details"] or "")
        if not valid_ton(dest):
            await call.answer(t(lang, "admin_wd_bad_addr"), show_alert=True)
            return
        if not getattr(ton, "can_send", False):
            await call.answer(t(lang, "admin_wd_no_wallet"), show_alert=True)
            return
        asset = _ticket_asset(item)
        amount = float(item["amount"] or 0)
        if amount <= 0:
            await call.answer(t(lang, "error"), show_alert=True)
            return
        if item["status"] == WALLET_PENDING:
            if not await db.claim_withdraw(item["id"], WALLET_SENDING):
                await call.answer(t(lang, "error"), show_alert=True)
                return
        try:
            await call.answer(t(lang, "admin_wd_sending"))
        except Exception:
            pass
        tx = await ton.payout(dest, amount, asset, comment=f"W{item['id']}")
        if not tx:
            await paint(call, t(lang, "admin_wd_fail", id=item["id"]), settings=settings)
            return
        await db.finish_withdraw(item["id"], WALLET_DONE, tx)
        await paint(
            call,
            t(
                lang,
                "admin_wd_ok",
                id=item["id"],
                amount=money_asset(amount, asset),
                currency=asset,
                address=dest,
                hash=tx,
            ),
            settings=settings,
        )
        try:
            user = await db.get_user(item["user_id"])
            await call.bot.send_message(
                item["user_id"],
                t(
                    (user["lang"] if user else None) or "ru",
                    "withdraw_sent",
                    id=item["id"],
                    amount=money_asset(amount, asset),
                    currency=asset,
                    address=dest,
                    hash=tx,
                ),
            )
        except Exception:
            pass


@router.callback_query(AdminCB.filter(F.a == "wd_no"))
async def wd_no(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if await _deny(call, lang, settings):
        return
    wid = int(callback_data.i)
    async with _wd_lock(wid):
        item = await db.get_withdraw(wid)
        if item is None or item["status"] != WALLET_PENDING:
            await call.answer(t(lang, "error"), show_alert=True)
            return
        if not await db.claim_withdraw(item["id"], WALLET_REJECTED, from_status=item["status"]):
            await call.answer(t(lang, "error"), show_alert=True)
            return
        asset = _ticket_asset(item)
        try:
            await db.credit_asset(item["user_id"], asset, float(item["amount"]))
        except Exception:
            await db.finish_withdraw(item["id"], item["status"])
            await call.answer(t(lang, "error"), show_alert=True)
            return
        await paint(call, t(lang, "admin_wd_no"), settings=settings)
        try:
            user = await db.get_user(item["user_id"])
            await call.bot.send_message(
                item["user_id"],
                t(
                    (user["lang"] if user else None) or "ru",
                    "withdraw_rejected",
                    id=item["id"],
                    amount=money_asset(item["amount"], asset),
                    currency=asset,
                ),
            )
        except Exception:
            pass


@router.callback_query(AdminCB.filter(F.a == "home"))
async def admin_home(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(call, t(lang, "admin_menu"), admin_kb(lang, theme), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "set"))
async def admin_bot_settings(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(call, _bot_text(settings, lang), cfg_fields_kb(lang, theme, list(BOT_FIELDS)), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "wal"))
async def admin_wallets(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(call, _wallets_text(settings, lang), cfg_fields_kb(lang, theme, list(WALLET_FIELDS)), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "sess"))
async def admin_sessions(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(call, _sessions_text(settings, lang), cfg_fields_kb(lang, theme, list(SESSION_FIELDS)), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "adms"))
async def admin_admins(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(call, _admins_text(settings, lang), admins_kb(lang, theme, sorted(settings.admins)), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "cfgset"))
async def admin_cfg_ask(
    call: CallbackQuery,
    callback_data: AdminCB,
    state: FSMContext,
    lang: str,
    settings: Settings,
    theme: Theme,
):
    if await _deny(call, lang, settings):
        return
    field = callback_data.k
    if field not in CFG_FIELDS:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(AdminFlow.cfg_value)
    await state.update_data(cfg_field=field)
    await paint(
        call,
        t(lang, "admin_cfg_ask", key=t(lang, f"admin_cfg_{field}")),
        cancel_kb(lang, theme),
        settings=settings,
    )


@router.message(AdminFlow.cfg_value, F.text)
async def admin_cfg_save(
    message: Message,
    state: FSMContext,
    lang: str,
    settings: Settings,
    theme: Theme,
    bank: BankAccount,
    ton,
):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    field = str(data.get("cfg_field") or "")
    if field not in CFG_FIELDS:
        await state.clear()
        return
    value = (message.text or "").strip()
    if value.lower() in {"-", "—", "none", "null", "empty"}:
        value = ""
    if field == "commission_percent":
        try:
            pct = float((value or "0").replace(",", "."))
        except ValueError:
            await message.answer(t(lang, "req_bad"))
            return
        if pct < 0 or pct > 50:
            await message.answer(t(lang, "req_bad"))
            return
        value = str(pct)
    try:
        settings.patch(field, value)
    except Exception:
        await message.answer(t(lang, "req_bad"))
        return
    if field == "required_channel":
        from app.services.channel import forget_sub

        forget_sub()
    await state.clear()
    note = t(lang, "admin_cfg_saved", key=t(lang, f"admin_cfg_{field}"))
    svc_name = ""
    try:
        if field in TON_RELOAD:
            svc_name = "TON"
            await ton.close()
            await ton.connect()
            note += "\n" + t(lang, "admin_cfg_reconnect", svc=svc_name)
        elif field in BANK_RELOAD:
            svc_name = "bank"
            await bank.restart()
            note += "\n" + t(lang, "admin_cfg_reconnect", svc=svc_name)
    except Exception:
        note += "\n" + t(lang, "admin_cfg_reconnect_fail", svc=svc_name or "service")
    if field in WALLET_FIELDS:
        kind = WALLET_FIELDS
        text = _wallets_text(settings, lang)
    elif field in SESSION_FIELDS:
        kind = SESSION_FIELDS
        text = _sessions_text(settings, lang)
    else:
        kind = BOT_FIELDS
        text = _bot_text(settings, lang)
    await message.answer(note + "\n\n" + text, reply_markup=cfg_fields_kb(lang, theme, list(kind)))


@router.callback_query(AdminCB.filter(F.a == "admadd"))
async def admin_add_ask(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.adm_add)
    await paint(call, t(lang, "admin_adm_ask"), cancel_kb(lang, theme), settings=settings)


@router.message(AdminFlow.adm_add, F.text)
async def admin_add_save(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    raw = (message.text or "").strip().lstrip("@")
    uid = 0
    if raw.isdigit():
        uid = int(raw)
    else:
        row = await db.get_user_by_username(raw)
        if row:
            uid = int(row["user_id"])
        else:
            try:
                chat = await message.bot.get_chat("@" + raw)
                uid = int(getattr(chat, "id", 0) or 0)
            except Exception:
                uid = 0
    if uid <= 0:
        await message.answer(t(lang, "admin_user_missing"), reply_markup=admins_kb(lang, theme, sorted(settings.admins)))
        await state.clear()
        return
    ids = list(settings.admins)
    if uid in ids:
        await state.clear()
        await message.answer(t(lang, "admin_adm_exists"), reply_markup=admins_kb(lang, theme, sorted(ids)))
        return
    ids.append(uid)
    _save_admins(settings, ids)
    await state.clear()
    await message.answer(t(lang, "admin_adm_added", id=uid) + "\n\n" + _admins_text(settings, lang), reply_markup=admins_kb(lang, theme, sorted(settings.admins)))


@router.callback_query(AdminCB.filter(F.a == "admrm"))
async def admin_remove(call: CallbackQuery, callback_data: AdminCB, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    uid = int(callback_data.i)
    if uid == call.from_user.id:
        await call.answer(t(lang, "admin_adm_self"), show_alert=True)
        return
    ids = [x for x in settings.admins if x != uid]
    if not ids:
        await call.answer(t(lang, "admin_adm_last"), show_alert=True)
        return
    if uid not in settings.admins:
        await call.answer()
        return
    _save_admins(settings, ids)
    await paint(call, t(lang, "admin_adm_removed", id=uid) + "\n\n" + _admins_text(settings, lang), admins_kb(lang, theme, sorted(settings.admins)), settings=settings)


def _btn_card(lang: str, theme: Theme, key: str) -> str:
    style = theme.style(key) or t(lang, "admin_btn_style_none")
    emoji = theme.emoji(key) or t(lang, "admin_btn_no_emoji")
    return t(
        lang,
        "admin_btn_card",
        title=theme.text(key, lang, id=0),
        key=key,
        ru=theme.text(key, "ru", id=0),
        en=theme.text(key, "en", id=0),
        style=style,
        emoji=emoji,
    )


@router.callback_query(BtnCB.filter(F.a == "list"))
async def btn_list(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(call, t(lang, "admin_btn_pick"), buttons_list_kb(lang, theme, callback_data.p), settings=settings)


@router.callback_query(BtnCB.filter(F.a == "open"))
async def btn_open(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    key = callback_data.k
    if key not in KEYS:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await paint(call, _btn_card(lang, theme, key), button_edit_kb(lang, theme, key, callback_data.p), settings=settings)


@router.callback_query(BtnCB.filter(F.a == "color"))
async def btn_color(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await paint(
        call,
        _btn_card(lang, theme, callback_data.k),
        button_style_kb(lang, theme, callback_data.k, callback_data.p),
        settings=settings,
    )


@router.callback_query(BtnCB.filter(F.a == "setst"))
async def btn_set_style(call: CallbackQuery, callback_data: BtnCB, db: Storage, lang: str, settings: Settings):
    if await _deny(call, lang, settings):
        return
    key = callback_data.k
    style = None if callback_data.s in {"-", "none"} else callback_data.s
    await db.patch_button(key, style="" if style is None else style)
    theme = Theme(await db.button_map())
    await paint(
        call,
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, key),
        button_edit_kb(lang, theme, key, callback_data.p),
        settings=settings,
    )


@router.callback_query(BtnCB.filter(F.a == "reset"))
async def btn_reset(call: CallbackQuery, callback_data: BtnCB, db: Storage, lang: str, settings: Settings):
    if await _deny(call, lang, settings):
        return
    await db.reset_button(callback_data.k)
    theme = Theme(await db.button_map())
    await paint(
        call,
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, callback_data.k),
        button_edit_kb(lang, theme, callback_data.k, callback_data.p),
        settings=settings,
    )


@router.callback_query(BtnCB.filter(F.a == "name"))
async def btn_name(call: CallbackQuery, callback_data: BtnCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.btn_name_ru)
    await state.update_data(btn_key=callback_data.k, btn_page=callback_data.p)
    await call.message.answer(t(lang, "admin_btn_ask_ru"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.btn_name_ru)
async def btn_name_ru(message: Message, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    label = (message.text or "").strip()
    if not label or len(label) > 64:
        await message.answer(t(lang, "req_bad"))
        return
    await state.update_data(label_ru=label)
    await state.set_state(AdminFlow.btn_name_en)
    await message.answer(t(lang, "admin_btn_ask_en"), reply_markup=cancel_kb(lang, theme))


@router.message(AdminFlow.btn_name_en)
async def btn_name_en(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    ru = data["label_ru"]
    en = (message.text or "").strip()
    if en in {"-", "—"}:
        en = ru
    if not en or len(en) > 64:
        await message.answer(t(lang, "req_bad"))
        return
    key = data["btn_key"]
    await db.patch_button(key, label_ru=ru, label_en=en)
    theme = Theme(await db.button_map())
    await state.clear()
    await message.answer(
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, key),
        reply_markup=button_edit_kb(lang, theme, key, data.get("btn_page", 0)),
    )


@router.callback_query(BtnCB.filter(F.a == "emoji"))
async def btn_emoji(call: CallbackQuery, callback_data: BtnCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.btn_emoji)
    await state.update_data(btn_key=callback_data.k, btn_page=callback_data.p)
    await call.message.answer(t(lang, "admin_btn_ask_emoji"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.btn_emoji)
async def btn_emoji_save(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    key = data["btn_key"]
    raw = (message.text or "").strip()
    if raw in {"-", "—"}:
        emoji_id = ""
    else:
        emoji_id = extract_emoji_id(message)
        if not emoji_id:
            await message.answer(t(lang, "req_bad"))
            return
    await db.patch_button(key, emoji_id=emoji_id)
    theme = Theme(await db.button_map())
    await state.clear()
    await message.answer(
        t(lang, "admin_btn_saved") + "\n\n" + _btn_card(lang, theme, key),
        reply_markup=button_edit_kb(lang, theme, key, data.get("btn_page", 0)),
    )


@router.callback_query(AdminCB.filter(F.a == "bans"))
async def bans_list(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    rows = await db.banned_users()
    if not rows:
        await paint(call, t(lang, "admin_bans_empty"), bans_kb(lang, theme, []), settings=settings)
        return
    lines = []
    for row in rows:
        lines.append(
            t(
                lang,
                "admin_bans_line",
                name=row["username"] or row["nick"] or "-",
                id=row["user_id"],
                reason=row["ban_reason"] or "—",
            )
        )
    await paint(call, "\n\n".join(lines), bans_kb(lang, theme, rows), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "unbani"))
async def unban_row(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await db.set_banned(callback_data.i, False)
    await call.answer(t(lang, "admin_unbanned", id=callback_data.i), show_alert=True)
    rows = await db.banned_users()
    await paint(call, t(lang, "admin_unbanned", id=callback_data.i), bans_kb(lang, theme, rows), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faq"))
async def faq_admin(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    items = await db.faq_all()
    text = t(lang, "admin_faq") if items else t(lang, "admin_faq_empty")
    await paint(call, text, faq_admin_kb(lang, theme, items), screen="faq", settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faqadd"))
async def faq_add(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.faq_title_ru)
    await call.message.answer(t(lang, "admin_faq_ask_title_ru"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.faq_title_ru)
async def faq_title_ru(message: Message, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    title = (message.text or "").strip()
    if len(title) < 2:
        await message.answer(t(lang, "req_bad"))
        return
    await state.update_data(title_ru=title[:120])
    await state.set_state(AdminFlow.faq_title_en)
    await message.answer(t(lang, "admin_faq_ask_title_en"), reply_markup=cancel_kb(lang, theme))


@router.message(AdminFlow.faq_title_en)
async def faq_title_en(message: Message, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    title = (message.text or "").strip()
    if title in {"-", "—"}:
        title = data["title_ru"]
    await state.update_data(title_en=title[:120])
    await state.set_state(AdminFlow.faq_body_ru)
    await message.answer(t(lang, "admin_faq_ask_body_ru"), reply_markup=cancel_kb(lang, theme))


@router.message(AdminFlow.faq_body_ru)
async def faq_body_ru(message: Message, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    body = (message.html_text or message.text or "").strip()
    if len(body) < 2:
        await message.answer(t(lang, "req_bad"))
        return
    await state.update_data(body_ru=body[:3500])
    await state.set_state(AdminFlow.faq_body_en)
    await message.answer(t(lang, "admin_faq_ask_body_en"), reply_markup=cancel_kb(lang, theme))


@router.message(AdminFlow.faq_body_en)
async def faq_body_en(message: Message, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    body = (message.html_text or message.text or "").strip()
    if body in {"-", "—"}:
        body = data["body_ru"]
    await state.update_data(body_en=body[:3500])
    await state.set_state(AdminFlow.faq_photo)
    await message.answer(t(lang, "admin_faq_ask_photo"), reply_markup=cancel_kb(lang, theme))


@router.message(AdminFlow.faq_photo)
async def faq_photo_save(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    raw = (message.text or "").strip()
    photo = message.photo[-1].file_id if message.photo else None
    if not photo and raw not in {"-", "—"}:
        await message.answer(t(lang, "req_bad"))
        return
    edit_id = data.get("faq_edit")
    if edit_id:
        await db.set_faq_photo(int(edit_id), photo)
        await state.clear()
        await message.answer(t(lang, "admin_faq_saved"), reply_markup=faq_admin_item_kb(lang, theme, int(edit_id)))
        return
    faq_id = await db.add_faq(data["title_ru"], data["title_en"], data["body_ru"], data["body_en"])
    if photo:
        await db.set_faq_photo(faq_id, photo)
    await state.clear()
    await message.answer(t(lang, "admin_faq_saved"), reply_markup=faq_admin_item_kb(lang, theme, faq_id))


@router.callback_query(AdminCB.filter(F.a == "faqo"))
async def faq_admin_open(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    item = await db.get_faq(callback_data.i)
    if item is None:
        await call.answer(t(lang, "faq_missing"), show_alert=True)
        return
    text = f"<b>{item['title_ru']}</b>\n\n{item['body_ru']}"
    await paint(call, text, faq_admin_item_kb(lang, theme, item["id"]), screen="faq", settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faqdel"))
async def faq_del(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await db.delete_faq(callback_data.i)
    items = await db.faq_all()
    await paint(call, t(lang, "admin_faq_deleted"), faq_admin_kb(lang, theme, items), screen="faq", settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faqph"))
async def faq_photo_ask(call: CallbackQuery, callback_data: AdminCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    await state.set_state(AdminFlow.faq_photo)
    await state.update_data(faq_edit=callback_data.i)
    await call.message.answer(t(lang, "admin_faq_ask_photo"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "scr"))
async def screens_admin(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    mapping = await db.screen_map()
    lines = [t(lang, "admin_screens_pick"), ""]
    for key in SCREENS:
        mark = "✓" if mapping.get(key) else "—"
        lines.append(f"{mark} {t(lang, f'admin_screen_name_{key}')}")
    await paint(call, "\n".join(lines), screens_admin_kb(lang, theme), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "scrset"))
async def screen_ask(call: CallbackQuery, callback_data: AdminCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if await _deny(call, lang, settings):
        return
    key = callback_data.k
    if key not in SCREENS:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(AdminFlow.screen_photo)
    await state.update_data(screen_key=key)
    title = t(lang, f"admin_screen_name_{key}")
    await call.message.answer(t(lang, "admin_screen_ask", key=title), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.screen_photo)
async def screen_save(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    key = data.get("screen_key")
    if not key:
        await state.clear()
        return
    raw = (message.text or "").strip()
    if raw in {"-", "—"}:
        await db.clear_screen(key)
        await state.clear()
        await message.answer(t(lang, "admin_screen_cleared", key=t(lang, f"admin_screen_name_{key}")))
        return
    if not message.photo:
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_screen(key, message.photo[-1].file_id)
    await state.clear()
    await message.answer(t(lang, "admin_screen_saved", key=t(lang, f"admin_screen_name_{key}")))


@router.callback_query(AdminCB.filter(F.a.in_({"disr", "dsw"})))
async def dispute_reply_ask(call: CallbackQuery, callback_data: AdminCB, state: FSMContext, lang: str, settings: Settings, theme: Theme, db: Storage):
    if await _deny(call, lang, settings):
        return
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    side = callback_data.x
    if callback_data.a == "disr" or side not in (1, 2):
        kb = InlineKeyboardBuilder()
        theme.add(kb, "admin_write_seller", lang, callback_data=AdminCB(a="dsw", i=callback_data.i, x=1).pack())
        theme.add(kb, "admin_write_buyer", lang, callback_data=AdminCB(a="dsw", i=callback_data.i, x=2).pack())
        theme.add(kb, "btn_back", lang, callback_data=DealCB(a="disth", i=callback_data.i).pack())
        kb.adjust(1)
        await call.message.answer(t(lang, "admin_ask_reply", id=callback_data.i), reply_markup=kb.as_markup())
        await call.answer()
        return
    target_id = deal["seller_id"] if side == 1 else deal["buyer_id"]
    if not target_id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(AdminFlow.dispute_reply)
    await state.update_data(deal_id=callback_data.i, target_id=target_id, target_side=side)
    ask_key = "admin_ask_write_seller" if side == 1 else "admin_ask_write_buyer"
    await call.message.answer(t(lang, ask_key, id=callback_data.i), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.dispute_reply)
async def dispute_reply(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if await _deny_msg(message, lang, settings):
        return
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    deal_id = int(data.get("deal_id") or 0)
    deal = await db.get_deal(deal_id)
    if deal is None:
        await state.clear()
        await message.answer(t(lang, "error"))
        return
    target_id = int(data.get("target_id") or 0)
    caption = (message.caption or message.text or "").strip()
    file_id = message.photo[-1].file_id if message.photo else None
    if not caption and not file_id:
        await message.answer(t(lang, "req_bad"))
        return
    if not target_id:
        target_id = deal["seller_id"] if int(data.get("target_side") or 0) == 1 else deal["buyer_id"]
    await db.add_dispute_msg(
        deal_id,
        message.from_user.id,
        caption or None,
        file_id,
        is_admin=True,
        target_id=target_id or 0,
    )
    await state.clear()
    note = t(lang, "deal_dispute_new", id=deal_id, who=t(lang, "admin_menu"), text=caption or t(lang, "deal_dispute_photo"))
    from app.handlers.deals import _push_dispute

    await _push_dispute(
        message.bot,
        db,
        settings,
        deal,
        message.from_user.id,
        note,
        file_id,
        to_admins=False,
        targets={target_id} if target_id else {deal["seller_id"], deal["buyer_id"]},
    )
    await message.answer(t(lang, "admin_wrote"), reply_markup=dispute_admin_kb(lang, theme, deal_id))
