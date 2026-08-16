import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.buttons import KEYS, Theme
from app.config import Settings
from app.i18n import t
from app.keyboards import (
    AdminCB,
    BtnCB,
    admin_kb,
    bans_kb,
    button_edit_kb,
    button_style_kb,
    buttons_list_kb,
    cancel_kb,
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
from app.storage import WALLET_DONE, WALLET_REJECTED, Storage
from app.util import extract_emoji_id, is_cancel, is_ton_deal, money, money_ton, parse_amount, paint

router = Router()


def _admin(settings: Settings, user_id: int) -> bool:
    return settings.is_admin(user_id)


@router.message(Command("admin"))
async def admin_entry(message: Message, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, message.from_user.id):
        await message.answer(t(lang, "admin_only"))
        return
    await message.answer(t(lang, "admin_menu"), reply_markup=admin_kb(lang, theme))


@router.callback_query(AdminCB.filter(F.a == "stats"))
async def stats(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme, bank: BankAccount):
    if not _admin(settings, call.from_user.id):
        await call.answer(t(lang, "admin_only"), show_alert=True)
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
            fee=fee,
            nft_left=left,
            pending_nft=pending_nft,
            by_status="\n".join(status_lines) or "—",
            by_cat="\n".join(cat_lines) or "—",
            recent="\n".join(recent_lines) or "—",
        ),
        admin_kb(lang, theme),
        settings=settings,
    )


@router.callback_query(AdminCB.filter(F.a == "ban"))
async def ask_ban(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.ban_id)
    await call.message.answer(t(lang, "admin_ask_ban"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "unban"))
async def ask_unban(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.unban_id)
    await call.message.answer(t(lang, "admin_ask_id"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.ban_id)
async def do_ban(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
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
async def do_ban_reason(message: Message, state: FSMContext, db: Storage, lang: str):
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
    extra = f"\n{reason}" if reason else ""
    try:
        user = await db.get_user(uid)
        await message.bot.send_message(uid, t((user["lang"] if user else None) or "ru", "admin_ban_notice", reason=extra))
    except Exception:
        pass


@router.message(AdminFlow.unban_id)
async def do_unban(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    if not (message.text or "").isdigit():
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_banned(int(message.text), False)
    uid = int(message.text)
    await state.clear()
    await message.answer(t(lang, "admin_unbanned", id=uid))


@router.callback_query(AdminCB.filter(F.a == "bal"))
async def ask_balance_id(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.balance_id)
    await call.message.answer(t(lang, "admin_ask_id"))
    await call.answer()


@router.message(AdminFlow.balance_id)
async def ask_balance_amount(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings):
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
    await state.set_state(AdminFlow.balance_amount)
    await message.answer(t(lang, "admin_ask_balance", currency=settings.currency))


@router.message(AdminFlow.balance_amount)
async def set_balance(message: Message, state: FSMContext, db: Storage, lang: str):
    if is_cancel(message.text or ""):
        return
    amount = parse_amount((message.text or "").lstrip("+"))
    if amount is None:
        await message.answer(t(lang, "req_bad"))
        return
    data = await state.get_data()
    await db.set_balance(data["target_id"], amount)
    await state.clear()
    await message.answer(t(lang, "admin_done"))


@router.callback_query(AdminCB.filter(F.a == "mail"))
async def ask_mail(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.mail)
    await call.message.answer(t(lang, "admin_ask_mail"))
    await call.answer()


@router.message(AdminFlow.mail)
async def send_mail(message: Message, state: FSMContext, db: Storage, lang: str):
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
    if not _admin(settings, call.from_user.id):
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
        await call.message.answer(
            t(
                lang,
                "deal_dispute_admin",
                id=deal["id"],
                buyer=buyer["username"] if buyer else "-",
                buyer_id=deal["buyer_id"],
                seller=seller["username"] if seller else "-",
                seller_id=deal["seller_id"],
                amount=money(deal["amount"]) if not is_ton_deal(deal) else f"{money_ton(deal['ton_amount'])} TON / {money(deal['rub_amount'])} ₽",
                currency="" if is_ton_deal(deal) else settings.currency,
                nft="—" if not deal["nft_id"] else str(deal["nft_id"]),
            )
            + extra,
            reply_markup=dispute_admin_kb(lang, theme, deal["id"]),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "win_b"))
async def win_buyer(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, ton):
    if not _admin(settings, call.from_user.id):
        return
    try:
        await svc.verdict_buyer(db, callback_data.i, ton)
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
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "win_s"))
async def win_seller(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, ton):
    if not _admin(settings, call.from_user.id):
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
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "deps"))
async def deposits(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    rows = await db.pending_deposits()
    if not rows:
        await call.answer(t(lang, "admin_empty_list"), show_alert=True)
        return
    for row in rows:
        await call.message.answer(
            t(
                lang,
                "admin_dep_line",
                id=row["id"],
                amount=f"{row['amount']:.2f}",
                currency=settings.currency,
                comment=row["comment"],
                user=row["user_id"],
            ),
            reply_markup=ticket_kb("dep", row["id"], lang, theme),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "wds"))
async def withdraws(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    rows = await db.pending_withdraws()
    if not rows:
        await call.answer(t(lang, "admin_empty_list"), show_alert=True)
        return
    for row in rows:
        await call.message.answer(
            t(
                lang,
                "admin_wd_line",
                id=row["id"],
                amount=f"{row['amount']:.2f}",
                currency=settings.currency,
                method=row["method"],
                details=row["details"],
                user=row["user_id"],
            ),
            reply_markup=ticket_kb("wd", row["id"], lang, theme),
        )
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "dep_ok"))
async def dep_ok(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None or deposit["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_deposit(deposit["id"], WALLET_DONE)
    await db.change_balance(deposit["user_id"], float(deposit["amount"]))
    await paint(call, t(lang, "admin_dep_ok"), settings=settings)
    try:
        user = await db.get_user(deposit["user_id"])
        await call.bot.send_message(
            deposit["user_id"],
            t(user["lang"] or "ru", "deposit_ok", amount=f"{deposit['amount']:.2f}", currency=settings.currency),
        )
    except Exception:
        pass
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "dep_no"))
async def dep_no(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    deposit = await db.get_deposit(callback_data.i)
    if deposit is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_deposit(deposit["id"], WALLET_REJECTED)
    await paint(call, t(lang, "admin_dep_no"), settings=settings)
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "wd_ok"))
async def wd_ok(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    item = await db.get_withdraw(callback_data.i)
    if item is None or item["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_withdraw(item["id"], WALLET_DONE)
    await paint(call, t(lang, "admin_wd_ok"), settings=settings)
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "wd_no"))
async def wd_no(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
        return
    item = await db.get_withdraw(callback_data.i)
    if item is None or item["status"] != "pending":
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await db.finish_withdraw(item["id"], WALLET_REJECTED)
    await db.change_balance(item["user_id"], float(item["amount"]))
    await paint(call, t(lang, "admin_wd_no"), settings=settings)
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "home"))
async def admin_home(call: CallbackQuery, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await paint(call, t(lang, "admin_menu"), admin_kb(lang, theme), settings=settings)


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
    if not _admin(settings, call.from_user.id):
        return
    await paint(call, t(lang, "admin_btn_pick"), buttons_list_kb(lang, theme, callback_data.p), settings=settings)


@router.callback_query(BtnCB.filter(F.a == "open"))
async def btn_open(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    key = callback_data.k
    if key not in KEYS:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await paint(call, _btn_card(lang, theme, key), button_edit_kb(lang, theme, key, callback_data.p), settings=settings)


@router.callback_query(BtnCB.filter(F.a == "color"))
async def btn_color(call: CallbackQuery, callback_data: BtnCB, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await paint(
        call,
        _btn_card(lang, theme, callback_data.k),
        button_style_kb(lang, theme, callback_data.k, callback_data.p),
        settings=settings,
    )


@router.callback_query(BtnCB.filter(F.a == "setst"))
async def btn_set_style(call: CallbackQuery, callback_data: BtnCB, db: Storage, lang: str, settings: Settings):
    if not _admin(settings, call.from_user.id):
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
    if not _admin(settings, call.from_user.id):
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
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.btn_name_ru)
    await state.update_data(btn_key=callback_data.k, btn_page=callback_data.p)
    await call.message.answer(t(lang, "admin_btn_ask_ru"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.btn_name_ru)
async def btn_name_ru(message: Message, state: FSMContext, lang: str, theme: Theme):
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
async def btn_name_en(message: Message, state: FSMContext, db: Storage, lang: str):
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
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.btn_emoji)
    await state.update_data(btn_key=callback_data.k, btn_page=callback_data.p)
    await call.message.answer(t(lang, "admin_btn_ask_emoji"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.btn_emoji)
async def btn_emoji_save(message: Message, state: FSMContext, db: Storage, lang: str):
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
    if not _admin(settings, call.from_user.id):
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
    if not _admin(settings, call.from_user.id):
        return
    await db.set_banned(callback_data.i, False)
    await call.answer(t(lang, "admin_unbanned", id=callback_data.i), show_alert=True)
    rows = await db.banned_users()
    await paint(call, t(lang, "admin_unbanned", id=callback_data.i), bans_kb(lang, theme, rows), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faq"))
async def faq_admin(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    items = await db.faq_all()
    text = t(lang, "admin_faq") if items else t(lang, "admin_faq_empty")
    await paint(call, text, faq_admin_kb(lang, theme, items), screen="faq", settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faqadd"))
async def faq_add(call: CallbackQuery, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.faq_title_ru)
    await call.message.answer(t(lang, "admin_faq_ask_title_ru"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.faq_title_ru)
async def faq_title_ru(message: Message, state: FSMContext, lang: str, theme: Theme):
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
async def faq_title_en(message: Message, state: FSMContext, lang: str, theme: Theme):
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
async def faq_body_ru(message: Message, state: FSMContext, lang: str, theme: Theme):
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
async def faq_body_en(message: Message, state: FSMContext, lang: str, theme: Theme):
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
async def faq_photo_save(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
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
    if not _admin(settings, call.from_user.id):
        return
    item = await db.get_faq(callback_data.i)
    if item is None:
        await call.answer(t(lang, "faq_missing"), show_alert=True)
        return
    text = f"<b>{item['title_ru']}</b>\n\n{item['body_ru']}"
    await paint(call, text, faq_admin_item_kb(lang, theme, item["id"]), screen="faq", settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faqdel"))
async def faq_del(call: CallbackQuery, callback_data: AdminCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await db.delete_faq(callback_data.i)
    items = await db.faq_all()
    await paint(call, t(lang, "admin_faq_deleted"), faq_admin_kb(lang, theme, items), screen="faq", settings=settings)


@router.callback_query(AdminCB.filter(F.a == "faqph"))
async def faq_photo_ask(call: CallbackQuery, callback_data: AdminCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.faq_photo)
    await state.update_data(faq_edit=callback_data.i)
    await call.message.answer(t(lang, "admin_faq_ask_photo"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.callback_query(AdminCB.filter(F.a == "scr"))
async def screens_admin(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    mapping = await db.screen_map()
    lines = [t(lang, "admin_screens_pick"), ""]
    for key in SCREENS:
        mark = "✓" if mapping.get(key) else "—"
        lines.append(f"{mark} {key}")
    await paint(call, "\n".join(lines), screens_admin_kb(lang, theme), settings=settings)


@router.callback_query(AdminCB.filter(F.a == "scrset"))
async def screen_ask(call: CallbackQuery, callback_data: AdminCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    key = callback_data.k
    if key not in SCREENS:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(AdminFlow.screen_photo)
    await state.update_data(screen_key=key)
    await call.message.answer(t(lang, "admin_screen_ask", key=key), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.screen_photo)
async def screen_save(message: Message, state: FSMContext, db: Storage, lang: str):
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
        await message.answer(t(lang, "admin_screen_cleared", key=key))
        return
    if not message.photo:
        await message.answer(t(lang, "req_bad"))
        return
    await db.set_screen(key, message.photo[-1].file_id)
    await state.clear()
    await message.answer(t(lang, "admin_screen_saved", key=key))


@router.callback_query(AdminCB.filter(F.a == "disr"))
async def dispute_reply_ask(call: CallbackQuery, callback_data: AdminCB, state: FSMContext, lang: str, settings: Settings, theme: Theme):
    if not _admin(settings, call.from_user.id):
        return
    await state.set_state(AdminFlow.dispute_reply)
    await state.update_data(deal_id=callback_data.i)
    await call.message.answer(t(lang, "admin_ask_reply", id=callback_data.i), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(AdminFlow.dispute_reply)
async def dispute_reply(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    deal_id = int(data.get("deal_id") or 0)
    deal = await db.get_deal(deal_id)
    if deal is None:
        await state.clear()
        await message.answer(t(lang, "error"))
        return
    caption = (message.caption or message.text or "").strip()
    file_id = message.photo[-1].file_id if message.photo else None
    if not caption and not file_id:
        await message.answer(t(lang, "req_bad"))
        return
    await db.add_dispute_msg(deal_id, message.from_user.id, caption or None, file_id, is_admin=True)
    await state.clear()
    note = t(lang, "deal_dispute_new", id=deal_id, who=t(lang, "admin_menu"), text=caption or t(lang, "deal_dispute_photo"))
    from app.handlers.deals import _push_dispute

    await _push_dispute(message.bot, db, settings, deal, message.from_user.id, note, file_id)
    await message.answer(t(lang, "admin_done"), reply_markup=dispute_admin_kb(lang, theme, deal_id))
