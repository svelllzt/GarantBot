from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.buttons import Theme
from app.config import Settings
from app.i18n import t
from app.catalog import group_cats, label, manual, needs_nft, normalize
from app.keyboards import (
    AdminCB,
    CatCB,
    DealCB,
    NavCB,
    cancel_kb,
    category_kb,
    confirm_kb,
    currency_kb,
    deal_kb,
    deal_mode_kb,
    evidence_kb,
    group_kb,
    history_kb,
    home_kb,
    nft_pick_kb,
    offer_kb,
    peer_cancel_kb,
    preview_kb,
    skip_review_kb,
    take_kb,
    dispute_admin_kb,
)
from app.services import channel as ch
from app.services import deals as svc
from app.services.deals import DealError
from app.states import DealFlow
from app.storage import DEAL_CANCELLED, DEAL_CLOSED, DEAL_DISPUTE, DEAL_LISTED, DEAL_OPEN, DEAL_PENDING, DEAL_REVIEW, NFT_AVAILABLE, NFT_TRANSFERRED, Storage
from app.util import (
    deal_asset,
    history_line,
    is_cancel,
    is_nft_deal,
    listing_owner,
    money_asset,
    nft_title,
    parse_amount,
    parse_ton,
    paint,
    render_deal,
    username_of,
    h,
)

router = Router()


async def _show_deal(bot, db: Storage, deal, user_id: int, lang: str, settings: Settings, theme: Theme, event=None, message=None, ton=None):
    escrow = ton.address if ton is not None else settings.ton_address
    text = await render_deal(
        db,
        deal,
        lang,
        settings.currency,
        escrow=escrow or "",
        viewer_id=user_id,
        reveal_secret=settings.is_admin(user_id),
    )
    seller_row = await db.get_user(deal["seller_id"]) if deal["seller_id"] else None
    markup = deal_kb(lang, theme, deal, user_id, seller_row)
    screen = "listing" if deal["status"] == DEAL_LISTED else "deal"
    target = event if event is not None else message
    if target is not None:
        await paint(target, text, markup, screen=screen, settings=settings)
        return
    from app.media import send_screen

    await send_screen(bot, user_id, text, markup, screen, settings)


async def _send_manual(bot, user_id: int, lang: str, deal, *, buyer_only: bool = True, as_buyer: bool | None = None) -> None:
    if buyer_only:
        is_buyer = as_buyer
        if is_buyer is None:
            try:
                is_buyer = int(deal["buyer_id"] or 0) == int(user_id)
            except (KeyError, IndexError, TypeError):
                is_buyer = False
        if not is_buyer:
            return
    cat = deal["category"] if deal.keys() and "category" in deal.keys() else "goods"
    text = manual(cat, lang)
    try:
        await bot.send_message(user_id, text)
    except Exception:
        pass


async def _publish_listing(bot, user_id: int, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    data = await state.get_data()
    category = data.get("category", "goods")
    try:
        deal_id = await svc.create_listing(
            db,
            user_id,
            category,
            data.get("title") or label(category, lang),
            float(data.get("amount") or 0),
            data.get("description") or "",
            nft_id=int(data.get("nft_id") or 0),
            currency=data.get("currency") or "USDT",
            secret=data.get("secret") or "",
        )
    except DealError as exc:
        await bot.send_message(user_id, svc.err_text(lang, exc))
        await state.clear()
        return
    await state.clear()
    deal = await db.get_deal(deal_id)
    poster = await db.get_user(user_id)
    posted = await ch.publish(bot, settings, db, deal, poster)
    extra = t(lang, "deal_list_ok", id=deal_id)
    if not posted:
        extra = extra + "\n" + t(lang, "deal_list_no_channel")
    await bot.send_message(user_id, extra)
    await _show_deal(bot, db, deal, user_id, lang, settings, theme)


async def present_start_deal(event, db: Storage, lang: str, settings: Settings, theme: Theme, ton, payload: str) -> bool:
    raw = (payload or "").strip()
    if raw.lower().startswith("deal"):
        raw = raw[4:].lstrip("_")
    if raw.lower().startswith("d"):
        raw = raw[1:]
    if not raw.isdigit():
        return False
    deal = await db.get_deal(int(raw))
    if deal is None:
        return False
    user_id = event.from_user.id
    if deal["status"] == DEAL_LISTED and listing_owner(deal) != user_id:
        text = await render_deal(db, deal, lang, settings.currency, viewer_id=user_id)
        markup = take_kb(lang, theme, deal["id"])
        await paint(event, text, markup, screen="listing", settings=settings)
        return True
    if user_id not in (deal["seller_id"], deal["buyer_id"]) and not settings.is_admin(user_id):
        await paint(event, t(lang, "deal_listed_taken"), screen="listing", settings=settings)
        return True
    await _show_deal(event.bot, db, deal, user_id, lang, settings, theme, event=event, ton=ton)
    return True


async def _maybe_send_nft(bot, db: Storage, bank, deal, lang: str) -> str | None:
    if not deal or not is_nft_deal(deal) or not deal["nft_id"] or deal["nft_sent"] or not deal["buyer_id"]:
        return None
    nft = await db.get_nft(deal["nft_id"])
    if not await db.claim_nft_sent(deal["id"]):
        return None
    result = await bank.transfer(nft, deal["buyer_id"]) if nft else "fail"
    if result == "ok":
        return "deal_nft_sent"
    await db.revert_nft_sent(deal["id"])
    if result in {"no_stars", "offline"}:
        return "deal_nft_no_stars"
    return "deal_nft_fail"


async def _ask_currency(event, lang: str, theme: Theme, settings: Settings) -> None:
    await paint(event, t(lang, "deal_ask_currency"), currency_kb(lang, theme), screen="deal", settings=settings)


async def _ask_price(message_or_call, state: FSMContext, lang: str, theme: Theme) -> None:
    data = await state.get_data()
    asset = data.get("currency") or "USDT"
    await state.set_state(DealFlow.price)
    await message_or_call.answer(t(lang, "deal_ask_price", currency=asset), reply_markup=cancel_kb(lang, theme))


async def _after_category(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings) -> None:
    data = await state.get_data()
    category = data.get("category") or "goods"
    if needs_nft(category):
        items = await db.nfts_of(call.from_user.id, NFT_AVAILABLE)
        if not items:
            await call.answer(t(lang, "deal_nft_need_item"), show_alert=True)
            return
        await paint(
            call,
            t(lang, "deal_nft_pick"),
            nft_pick_kb(lang, theme, 0, items, action="nftflow"),
            screen="deal",
            settings=settings,
        )
        return
    await _ask_currency(call, lang, theme, settings)


@router.callback_query(NavCB.filter(F.a == "deal"))
async def new_deal(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    await state.clear()
    if not call.from_user.username:
        await call.answer(t(lang, "need_username"), show_alert=True)
        return
    active = await db.active_deal(call.from_user.id)
    if active:
        await _show_deal(call.bot, db, active, call.from_user.id, lang, settings, theme, event=call, ton=ton)
        return
    await paint(
        call,
        t(lang, "deal_ask_group"),
        group_kb(lang, theme),
        screen="deal",
        settings=settings,
    )


@router.callback_query(DealCB.filter(F.a == "mode"))
async def pick_mode(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    listing = bool(callback_data.x)
    await state.update_data(listing=listing, as_buyer=False)
    if listing:
        await _publish_listing(call.bot, call.from_user.id, state, db, lang, settings, theme)
        await call.answer()
        return
    await state.set_state(DealFlow.username)
    await call.message.answer(t(lang, "deal_ask_user"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.callback_query(CatCB.filter())
async def pick_cat(call: CallbackQuery, callback_data: CatCB, state: FSMContext, db: Storage, lang: str, theme: Theme, ton, settings: Settings):
    raw = callback_data.k
    if callback_data.g:
        group = raw
        cats = group_cats(group)
        if len(cats) > 1:
            await paint(call, t(lang, "deal_ask_cat"), category_kb(lang, theme, group), screen="deal", settings=settings)
            return
        if not cats:
            await call.answer(t(lang, "error"), show_alert=True)
            return
        category = cats[0]
    else:
        category = normalize(raw)
    await state.update_data(category=category, as_buyer=False, title=label(category, lang))
    await _after_category(call, state, db, lang, theme, settings)


@router.callback_query(DealCB.filter(F.a == "nftflow"))
async def pick_nft_flow(call: CallbackQuery, callback_data: DealCB, state: FSMContext, lang: str, theme: Theme, settings: Settings):
    await state.update_data(nft_id=callback_data.x)
    await _ask_currency(call, lang, theme, settings)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "cur"))
async def pick_currency(call: CallbackQuery, callback_data: DealCB, state: FSMContext, lang: str, theme: Theme):
    currency = "TON" if callback_data.x else "USDT"
    await state.update_data(currency=currency)
    await _ask_price(call.message, state, lang, theme)
    await call.answer()


@router.message(DealFlow.username)
async def find_peer(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    username = (message.text or "").strip().lstrip("@")
    me = await db.get_user(message.from_user.id)
    if me is None:
        await message.answer(t(lang, "error"))
        return
    if username.lower() == (me["username"] or "").lower():
        await message.answer(t(lang, "deal_self"))
        return
    peer = await db.get_user_by_username(username)
    if peer is None:
        await message.answer(t(lang, "deal_missing"))
        return
    data = await state.get_data()
    category = data.get("category", "goods")
    await state.update_data(peer_id=peer["user_id"])
    await state.set_state(None)
    kind_label = label(category, lang)
    await message.answer(
        t(
            lang,
            "deal_preview",
            id=peer["user_id"],
            nick=h(peer["nick"] or peer["first_name"] or "-"),
            username=username_of(peer),
            deals=peer["deals_count"],
            role=t(lang, "deal_seller"),
            kind=kind_label,
        ),
        reply_markup=preview_kb(lang, theme),
    )


@router.callback_query(DealCB.filter(F.a == "abort"))
async def abort_preview(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    await state.clear()
    await paint(call, t(lang, "cancelled"), await home_kb(db, call.from_user.id, lang, theme), screen="menu", settings=settings)


@router.message(DealFlow.price)
async def save_create_price(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    if data.get("deal_id"):
        amount = parse_amount(message.text or "") if data.get("currency") != "TON" else parse_ton(message.text or "")
        if data.get("currency") == "TON":
            amount = parse_ton(message.text or "")
        else:
            amount = parse_amount(message.text or "")
        if amount is None:
            await message.answer(t(lang, "req_bad"))
            return
        try:
            await svc.set_price(db, data["deal_id"], message.from_user.id, amount)
        except DealError as exc:
            await message.answer(svc.err_text(lang, exc))
            await state.clear()
            return
        await state.clear()
        deal = await db.get_deal(data["deal_id"])
        asset = deal_asset(deal)
        await message.answer(t(lang, "deal_price_set", amount=money_asset(amount, asset), currency=asset))
        await _show_deal(message.bot, db, deal, message.from_user.id, lang, settings, theme, message=message)
        return
    asset = data.get("currency") or "USDT"
    amount = parse_ton(message.text or "") if asset == "TON" else parse_amount(message.text or "")
    if amount is None:
        await message.answer(t(lang, "req_bad"))
        return
    await state.update_data(amount=amount)
    if needs_nft(data.get("category")):
        await state.set_state(DealFlow.description)
        await message.answer(t(lang, "deal_ask_desc"), reply_markup=cancel_kb(lang, theme))
        return
    await state.set_state(DealFlow.secret)
    await message.answer(t(lang, "deal_ask_secret"), reply_markup=cancel_kb(lang, theme))


@router.message(DealFlow.secret)
async def save_secret(message: Message, state: FSMContext, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    secret = (message.text or "").strip()
    if len(secret) < 2:
        await message.answer(t(lang, "req_bad"))
        return
    await state.update_data(secret=secret[:2000])
    await state.set_state(DealFlow.description)
    await message.answer(t(lang, "deal_ask_desc"), reply_markup=cancel_kb(lang, theme))


@router.callback_query(NavCB.filter(F.a == "feed"))
async def feed(call: CallbackQuery, db: Storage, lang: str, settings: Settings, theme: Theme):
    rows = await db.listed_deals()
    if not rows:
        await call.answer(t(lang, "deal_feed_empty"), show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    lines = []
    for deal in rows:
        seller = await db.get_user(deal["seller_id"]) if deal["seller_id"] else await db.get_user(deal["buyer_id"])
        cat = label(deal["category"] if "category" in deal.keys() else None, lang)
        title = deal["title"] or cat
        asset = deal_asset(deal)
        lines.append(
            t(
                lang,
                "deal_feed_line",
                id=deal["id"],
                cat=cat,
                amount=f"{money_asset(deal['amount'], asset)} {asset}" if deal["amount"] is not None else "—",
                title=title,
                seller=username_of(seller) if seller else "-",
            )
        )
        kb.button(text=f"#{deal['id']} {title[:28]}", style="primary", callback_data=DealCB(a="card", i=deal["id"]).pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    await paint(call, "\n\n".join(lines), kb.as_markup(), screen="listing", settings=settings)


@router.callback_query(DealCB.filter(F.a == "card"))
async def listing_card(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["status"] == DEAL_LISTED and listing_owner(deal) != call.from_user.id:
        text = await render_deal(db, deal, lang, settings.currency, viewer_id=call.from_user.id)
        await paint(call, text, take_kb(lang, theme, deal["id"]), screen="listing", settings=settings)
        return
    if call.from_user.id not in (deal["seller_id"], deal["buyer_id"]) and not settings.is_admin(call.from_user.id):
        await call.answer(t(lang, "deal_listed_taken"), show_alert=True)
        return
    await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, event=call, ton=ton)


async def _after_take(call: CallbackQuery, db: Storage, deal, lang: str, settings: Settings, theme: Theme, ton, bank=None) -> None:
    await ch.mark(call.bot, settings, deal, "channel_taken")
    user = await db.get_user(call.from_user.id)
    if call.from_user.id == deal["seller_id"]:
        peer_id = deal["buyer_id"]
        key = "deal_taken_buyer"
    else:
        peer_id = deal["seller_id"]
        key = "deal_taken_seller"
    peer = await db.get_user(peer_id) if peer_id else None
    peer_lang = (peer["lang"] if peer else None) or "ru"
    await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, event=call, ton=ton)
    await _send_manual(call.bot, call.from_user.id, lang, deal)
    if peer and user and peer_id != call.from_user.id:
        try:
            await call.bot.send_message(
                peer_id,
                t(peer_lang, key, username=username_of(user), id=deal["id"]),
            )
            await _show_deal(call.bot, db, deal, peer_id, peer_lang, settings, theme, ton=ton)
        except Exception:
            pass
    if bank is not None:
        note = await _maybe_send_nft(call.bot, db, bank, deal, lang)
        if note:
            try:
                await call.message.answer(t(lang, note))
            except Exception:
                pass
            if deal["buyer_id"] and deal["buyer_id"] != call.from_user.id:
                buyer = await db.get_user(deal["buyer_id"])
                if buyer:
                    try:
                        await call.bot.send_message(deal["buyer_id"], t(buyer["lang"] or "ru", note))
                    except Exception:
                        pass


@router.callback_query(DealCB.filter(F.a == "take"))
async def take_deal(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton, bank):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    try:
        await svc.take_listing(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    await _after_take(call, db, deal, lang, settings, theme, ton, bank=bank)


@router.callback_query(DealCB.filter(F.a == "memo"))
async def show_memo(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["status"] != DEAL_LISTED and deal["buyer_id"] != call.from_user.id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await call.message.answer(manual(deal["category"] if "category" in deal.keys() else "goods", lang))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "rev_peer"))
async def preview_reviews(call: CallbackQuery, state: FSMContext, db: Storage, lang: str):
    data = await state.get_data()
    peer_id = data.get("peer_id")
    if not peer_id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    rows = await db.reviews_for(peer_id)
    if not rows:
        await call.answer(t(lang, "no_reviews"), show_alert=True)
        return
    text = "\n\n".join(f"• {r['text']}" for r in rows)
    await call.message.answer(text)
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "send"))
async def send_offer(call: CallbackQuery, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    data = await state.get_data()
    peer_id = data.get("peer_id")
    category = data.get("category", "goods")
    nft_id = int(data.get("nft_id") or 0)
    if not peer_id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    try:
        deal_id = await svc.open_offer(
            db,
            call.from_user.id,
            peer_id,
            False,
            category=category,
            title=data.get("title") or label(category, lang),
            nft_id=nft_id,
            amount=float(data.get("amount") or 0),
            description=data.get("description") or "",
            currency=data.get("currency") or "USDT",
            secret=data.get("secret") or "",
        )
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    await state.clear()
    me = await db.get_user(call.from_user.id)
    peer = await db.get_user(peer_id)
    if me is None or peer is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    peer_lang = peer["lang"] or "ru"
    kind_label = label(category, peer_lang)
    await paint(
        call,
        t(lang, "deal_sent"),
        await home_kb(db, call.from_user.id, lang, theme),
        screen="menu",
        settings=settings,
    )
    try:
        await call.bot.send_message(
            peer_id,
            t(
                peer_lang,
                "deal_offer_in",
                id=deal_id,
                username=username_of(me),
                uid=me["user_id"],
                deals=me["deals_count"],
                role=t(peer_lang, "deal_buyer"),
                kind=kind_label,
            ),
            reply_markup=offer_kb(peer_lang, theme, deal_id),
        )
    except Exception:
        pass


@router.callback_query(DealCB.filter(F.a == "acc"))
async def accept_offer(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton, bank):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    try:
        await svc.accept(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    try:
        await call.message.edit_reply_markup()
    except Exception:
        pass
    for uid in (deal["seller_id"], deal["buyer_id"]):
        if not uid:
            continue
        user = await db.get_user(uid)
        if not user:
            continue
        user_lang = user["lang"] or "ru"
        try:
            await _show_deal(call.bot, db, deal, uid, user_lang, settings, theme, ton=ton)
            await _send_manual(call.bot, uid, user_lang, deal)
        except Exception:
            pass
    note = await _maybe_send_nft(call.bot, db, bank, deal, lang)
    if note and deal["buyer_id"]:
        buyer = await db.get_user(deal["buyer_id"])
        if buyer:
            try:
                await call.bot.send_message(deal["buyer_id"], t(buyer["lang"] or "ru", note))
            except Exception:
                pass
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "nftacc"))
async def accept_with_nft(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    try:
        title = await svc.attach_nft(db, callback_data.i, call.from_user.id, callback_data.x)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    await call.answer(t(lang, "deal_nft_set", title=title), show_alert=True)
    if deal:
        await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, event=call, ton=ton)


@router.callback_query(DealCB.filter(F.a == "dec"))
async def decline_offer(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme, settings: Settings):
    deal = await db.get_deal(callback_data.i)
    try:
        await svc.decline(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    await paint(
        call,
        t(lang, "deal_declined"),
        await home_kb(db, call.from_user.id, lang, theme),
        screen="menu",
        settings=settings,
    )
    other = deal["seller_id"] if deal["buyer_id"] == call.from_user.id else deal["buyer_id"]
    other_user = await db.get_user(other) if other else None
    if other and other_user:
        other_lang = other_user["lang"] or "ru"
        try:
            await call.bot.send_message(other, t(other_lang, "deal_declined_peer"), reply_markup=await home_kb(db, other, other_lang, theme))
        except Exception:
            pass


@router.callback_query(DealCB.filter(F.a == "open"))
async def reopen(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if call.from_user.id not in (deal["seller_id"], deal["buyer_id"]) and not settings.is_admin(call.from_user.id):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, event=call, ton=ton)


@router.callback_query(DealCB.filter(F.a == "price"))
async def ask_price(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["status"] != DEAL_LISTED:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if listing_owner(deal) != call.from_user.id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.price)
    await state.update_data(deal_id=deal["id"], currency=deal_asset(deal))
    await call.message.answer(t(lang, "deal_ask_price", currency=deal_asset(deal)), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "desc"))
async def ask_desc(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["status"] != DEAL_LISTED:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if listing_owner(deal) != call.from_user.id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.description)
    await state.update_data(deal_id=deal["id"])
    await call.message.answer(t(lang, "deal_ask_desc"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


@router.message(DealFlow.description)
async def save_desc(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    text = (message.text or "").strip()
    if len(text) < 2:
        await message.answer(t(lang, "req_bad"))
        return
    data = await state.get_data()
    if not data.get("deal_id"):
        await state.update_data(description=text)
        await state.set_state(None)
        await message.answer(
            t(lang, "deal_mode"),
            reply_markup=deal_mode_kb(lang, theme, ch.public_url(settings), public=True),
        )
        return
    try:
        await svc.set_description(db, data["deal_id"], message.from_user.id, text)
    except DealError as exc:
        await message.answer(svc.err_text(lang, exc))
        await state.clear()
        return
    await state.clear()
    await message.answer(t(lang, "deal_desc_set"))
    deal = await db.get_deal(data["deal_id"])
    await _show_deal(message.bot, db, deal, message.from_user.id, lang, settings, theme, message=message)


@router.callback_query(DealCB.filter(F.a == "nft"))
async def pick_nft(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme, settings: Settings):
    deal = await db.get_deal(callback_data.i)
    if deal is None or not is_nft_deal(deal) or deal["seller_id"] != call.from_user.id:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["nft_sent"]:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    items = await db.nfts_of(call.from_user.id, NFT_AVAILABLE)
    if not items:
        await call.answer(t(lang, "deal_nft_empty"), show_alert=True)
        return
    await paint(
        call,
        t(lang, "deal_nft_pick"),
        nft_pick_kb(lang, theme, callback_data.i, items),
        screen="deal",
        settings=settings,
    )


@router.callback_query(DealCB.filter(F.a == "nftset"))
async def set_nft(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    try:
        title = await svc.attach_nft(db, callback_data.i, call.from_user.id, callback_data.x)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    await call.answer(t(lang, "deal_nft_set", title=title), show_alert=True)
    deal = await db.get_deal(callback_data.i)
    await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, event=call)
    if deal and deal["buyer_id"]:
        buyer = await db.get_user(deal["buyer_id"])
        if buyer:
            try:
                await call.bot.send_message(
                    deal["buyer_id"],
                    t(buyer["lang"] or "ru", "deal_nft_set", title=title),
                )
            except Exception:
                pass


@router.callback_query(DealCB.filter(F.a == "ok"))
async def confirm_ask(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["buyer_id"] != call.from_user.id or deal["status"] != DEAL_OPEN:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if is_nft_deal(deal) and not deal["nft_sent"]:
        await call.answer(t(lang, "deal_nft_wait_send"), show_alert=True)
        return
    await call.message.answer(
        t(lang, "deal_confirm_ask"),
        reply_markup=confirm_kb(lang, theme, "okgo", callback_data.i),
    )
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "okgo"))
async def confirm_go(
    call: CallbackQuery,
    callback_data: DealCB,
    state: FSMContext,
    db: Storage,
    lang: str,
    settings: Settings,
    theme: Theme,
):
    if callback_data.x != 1:
        await call.answer()
        return
    try:
        payout = await svc.complete(db, settings, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    deal = await db.get_deal(callback_data.i)
    seller = await db.get_user(deal["seller_id"])
    seller_lang = (seller["lang"] or "ru") if seller else "ru"
    await state.set_state(DealFlow.review)
    await state.update_data(deal_id=deal["id"])
    await paint(call, t(lang, "deal_done_buyer"), settings=settings)
    try:
        await call.message.answer(t(lang, "deal_review_ask"), reply_markup=skip_review_kb(lang, theme, deal["id"]))
    except Exception:
        pass
    try:
        await call.bot.send_message(
            deal["seller_id"],
            t(
                seller_lang,
                "deal_done_seller",
                amount=money_asset(payout, deal_asset(deal)),
                currency=deal_asset(deal),
                commission=settings.commission_percent,
            ),
            reply_markup=await home_kb(db, deal["seller_id"], seller_lang, theme),
        )
    except Exception:
        pass


@router.message(DealFlow.review)
async def save_review(message: Message, state: FSMContext, db: Storage, lang: str, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    deal = await db.get_deal(data.get("deal_id", 0))
    if deal is None or deal["buyer_id"] != message.from_user.id:
        await state.clear()
        return
    text = (message.text or "").strip()
    if text:
        await db.add_review(deal["seller_id"], deal["buyer_id"], deal["id"], text[:500])
        seller = await db.get_user(deal["seller_id"])
        if seller:
            await message.bot.send_message(
                deal["seller_id"],
                t(seller["lang"] or "ru", "deal_review_saved") + "\n" + h(text),
            )
        await message.answer(t(lang, "deal_review_saved"))
    await svc.close_after_review(db, deal["id"])
    await state.clear()
    await message.answer(t(lang, "menu"), reply_markup=await home_kb(db, message.from_user.id, lang, theme))


@router.callback_query(DealCB.filter(F.a == "skip"))
async def skip_review(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    deal = await db.get_deal(callback_data.i)
    if deal is None or deal["buyer_id"] != call.from_user.id or deal["status"] != DEAL_REVIEW:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await svc.close_after_review(db, callback_data.i)
    await state.clear()
    await paint(
        call,
        t(lang, "deal_done_buyer"),
        await home_kb(db, call.from_user.id, lang, theme),
        screen="menu",
        settings=settings,
    )


@router.callback_query(DealCB.filter(F.a == "can"))
async def cancel_ask(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme, settings: Settings):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["status"] in {DEAL_DISPUTE, DEAL_REVIEW, DEAL_CLOSED}:
        await call.answer(t(lang, "deal_cancel_denied"), show_alert=True)
        return
    if deal["nft_sent"]:
        await call.answer(t(lang, "deal_cancel_denied"), show_alert=True)
        return
    if deal["status"] == DEAL_LISTED:
        if listing_owner(deal) != call.from_user.id:
            await call.answer(t(lang, "error"), show_alert=True)
            return
        try:
            await svc.cancel_mutual(db, deal["id"])
        except DealError as exc:
            await call.answer(svc.err_text(lang, exc), show_alert=True)
            return
        await ch.mark(call.bot, settings, deal, "channel_closed")
        await paint(
            call,
            t(lang, "deal_cancel_ok"),
            await home_kb(db, call.from_user.id, lang, theme),
            screen="menu",
            settings=settings,
        )
        return
    if deal["status"] == DEAL_PENDING:
        try:
            await svc.decline(db, deal["id"], call.from_user.id)
        except DealError as exc:
            await call.answer(svc.err_text(lang, exc), show_alert=True)
            return
        other = deal["seller_id"] if call.from_user.id == deal["buyer_id"] else deal["buyer_id"]
        other_user = await db.get_user(other) if other else None
        await paint(call, t(lang, "deal_cancel_ok"), settings=settings)
        if other and other_user:
            try:
                await call.bot.send_message(other, t(other_user["lang"] or "ru", "deal_declined_peer"), reply_markup=await home_kb(db, other, other_user["lang"] or "ru", theme))
            except Exception:
                pass
        try:
            await call.message.answer(t(lang, "menu"), reply_markup=await home_kb(db, call.from_user.id, lang, theme))
        except Exception:
            pass
        return
    if deal["status"] != DEAL_OPEN or call.from_user.id not in (deal["seller_id"], deal["buyer_id"]):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await call.message.answer(t(lang, "deal_cancel_ask"), reply_markup=confirm_kb(lang, theme, "cansend", deal["id"]))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "cansend"))
async def cancel_send(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme):
    if callback_data.x != 1:
        await call.answer()
        return
    deal = await db.get_deal(callback_data.i)
    if deal is None or call.from_user.id not in (deal["seller_id"], deal["buyer_id"]):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    try:
        result = await svc.request_cancel(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    if result == "done":
        for uid in (deal["seller_id"], deal["buyer_id"]):
            if not uid:
                continue
            user = await db.get_user(uid)
            if not user:
                continue
            try:
                await call.bot.send_message(uid, t(user["lang"] or "ru", "deal_cancel_ok"), reply_markup=await home_kb(db, uid, user["lang"] or "ru", theme))
            except Exception:
                pass
        await call.answer()
        return
    other = deal["seller_id"] if call.from_user.id == deal["buyer_id"] else deal["buyer_id"]
    other_user = await db.get_user(other) if other else None
    await paint(call, t(lang, "deal_cancel_sent"))
    if other_user is None:
        await call.answer()
        return
    other_lang = other_user["lang"] or "ru"
    try:
        await call.bot.send_message(
            other,
            t(other_lang, "deal_cancel_ask"),
            reply_markup=peer_cancel_kb(other_lang, theme, deal["id"]),
        )
    except Exception:
        pass
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "canok"))
async def cancel_ok(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, theme: Theme, ton):
    deal = await db.get_deal(callback_data.i)
    if deal is None or call.from_user.id not in (deal["seller_id"], deal["buyer_id"]):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    try:
        await svc.confirm_cancel(db, callback_data.i, call.from_user.id)
    except DealError as exc:
        await call.answer(svc.err_text(lang, exc), show_alert=True)
        return
    for uid in (deal["seller_id"], deal["buyer_id"]):
        if not uid:
            continue
        user = await db.get_user(uid)
        if not user:
            continue
        try:
            await call.bot.send_message(uid, t(user["lang"] or "ru", "deal_cancel_ok"), reply_markup=await home_kb(db, uid, user["lang"] or "ru", theme))
        except Exception:
            pass
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "canno"))
async def cancel_no(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "cancelled"))
        return
    try:
        asked = await svc.refuse_cancel(db, callback_data.i, call.from_user.id)
    except DealError:
        await call.answer(t(lang, "cancelled"))
        return
    await call.answer(t(lang, "cancelled"))
    if asked and asked != call.from_user.id:
        other = await db.get_user(asked)
        if other:
            try:
                await call.bot.send_message(asked, t(other["lang"] or "ru", "cancelled"))
            except Exception:
                pass


@router.callback_query(DealCB.filter(F.a == "dis"))
async def dispute(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None or call.from_user.id not in (deal["seller_id"], deal["buyer_id"]):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["status"] != DEAL_OPEN:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.dispute_reason)
    await state.update_data(deal_id=deal["id"])
    await call.message.answer(t(lang, "deal_dispute_ask"), reply_markup=cancel_kb(lang, theme))
    await call.answer()


async def _thread_text(db: Storage, deal_id: int, lang: str) -> str:
    rows = await db.dispute_messages(deal_id)
    if not rows:
        return t(lang, "deal_dispute_empty")
    chunks = []
    for row in rows:
        user = await db.get_user(row["user_id"]) if row["user_id"] else None
        if row["is_admin"]:
            who = t(lang, "admin_menu")
        elif user:
            who = "@" + username_of(user)
        else:
            who = str(row["user_id"])
        body = h(row["text"]) if row["text"] else t(lang, "deal_dispute_photo")
        chunks.append(t(lang, "deal_dispute_msg", who=who, text=body))
    return "\n\n".join(chunks)[:3500]


async def _push_dispute(bot, db: Storage, settings: Settings, deal, sender_id: int, text: str, file_id: str | None = None, *, to_admins: bool = True) -> None:
    targets = {deal["seller_id"], deal["buyer_id"]}
    if to_admins:
        targets.update(settings.admins)
    targets.discard(sender_id)
    targets.discard(0)
    for uid in targets:
        try:
            if file_id:
                await bot.send_photo(uid, file_id, caption=text[:1024])
            else:
                await bot.send_message(uid, text)
        except Exception:
            pass


@router.message(DealFlow.dispute_reason)
async def dispute_reason(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    deal_id = int(data.get("deal_id") or 0)
    caption = (message.caption or message.text or "").strip()
    file_id = message.photo[-1].file_id if message.photo else None
    if len(caption) < 2 and not file_id:
        await message.answer(t(lang, "req_bad"))
        return
    try:
        await svc.open_dispute(db, deal_id, message.from_user.id, caption)
    except DealError as exc:
        await message.answer(svc.err_text(lang, exc))
        await state.clear()
        return
    await db.add_dispute_msg(deal_id, message.from_user.id, caption or None, file_id, is_admin=False)
    await state.clear()
    deal = await db.get_deal(deal_id)
    nft = await db.get_nft(deal["nft_id"]) if deal["nft_id"] else None
    buyer = await db.get_user(deal["buyer_id"])
    seller = await db.get_user(deal["seller_id"])
    await message.answer(t(lang, "deal_dispute_ok"))
    peer_text = t(lang, "deal_dispute_peer", id=deal["id"], reason=h(caption) if caption else t(lang, "deal_dispute_photo"))
    await _push_dispute(message.bot, db, settings, deal, message.from_user.id, peer_text, file_id)
    admin_text = t(
        "ru",
        "deal_dispute_admin",
        id=deal["id"],
        buyer=username_of(buyer) if buyer else "-",
        buyer_id=deal["buyer_id"],
        seller=username_of(seller) if seller else "-",
        seller_id=deal["seller_id"],
        amount=f"{money_asset(deal['amount'], deal_asset(deal))} {deal_asset(deal)}",
        currency=deal_asset(deal),
        nft=nft_title(nft) if nft else t("ru", "deal_nft_none"),
    )
    if caption:
        admin_text = admin_text + "\n\n" + caption
    for admin_id in settings.admins:
        try:
            await message.bot.send_message(admin_id, admin_text, reply_markup=dispute_admin_kb("ru", theme, deal["id"]))
        except Exception:
            pass
    await _show_deal(message.bot, db, deal, message.from_user.id, lang, settings, theme, message=message)


@router.callback_query(DealCB.filter(F.a.in_({"photo", "disev"})))
async def deal_photo_start(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, theme: Theme, settings: Settings):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    party = call.from_user.id in (deal["seller_id"], deal["buyer_id"])
    admin = settings.is_admin(call.from_user.id)
    if deal["status"] == DEAL_OPEN and not party:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["status"] == DEAL_DISPUTE and not party and not admin:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if deal["status"] not in {DEAL_OPEN, DEAL_DISPUTE}:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    await state.set_state(DealFlow.dispute_evidence)
    await state.update_data(deal_id=deal["id"])
    ask = t(lang, "deal_dispute_evidence_ask") if deal["status"] == DEAL_DISPUTE else t(lang, "deal_photo_ask")
    await call.message.answer(ask, reply_markup=evidence_kb(lang, theme, deal["id"]))
    await call.answer()


@router.callback_query(DealCB.filter(F.a == "disdone"))
async def dispute_evidence_done(call: CallbackQuery, callback_data: DealCB, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme, ton):
    data = await state.get_data()
    await state.clear()
    deal_id = int(callback_data.i or data.get("deal_id") or 0)
    deal = await db.get_deal(deal_id)
    if deal:
        if call.from_user.id not in (deal["seller_id"], deal["buyer_id"]) and not settings.is_admin(call.from_user.id):
            await call.answer(t(lang, "error"), show_alert=True)
            return
        await _show_deal(call.bot, db, deal, call.from_user.id, lang, settings, theme, event=call, ton=ton)
        return
    await call.answer()


@router.message(DealFlow.dispute_evidence)
async def dispute_evidence(message: Message, state: FSMContext, db: Storage, lang: str, settings: Settings, theme: Theme):
    if is_cancel(message.text or ""):
        return
    data = await state.get_data()
    deal_id = int(data.get("deal_id") or 0)
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] not in {DEAL_OPEN, DEAL_DISPUTE}:
        await state.clear()
        await message.answer(t(lang, "error"))
        return
    if message.from_user.id not in (deal["seller_id"], deal["buyer_id"]) and not settings.is_admin(message.from_user.id):
        await state.clear()
        await message.answer(t(lang, "error"))
        return
    caption = (message.caption or message.text or "").strip()
    file_id = message.photo[-1].file_id if message.photo else None
    if not caption and not file_id:
        await message.answer(t(lang, "req_bad"))
        return
    is_admin = settings.is_admin(message.from_user.id)
    await db.add_dispute_msg(deal_id, message.from_user.id, caption or None, file_id, is_admin=is_admin)
    who = username_of(await db.get_user(message.from_user.id))
    if deal["status"] == DEAL_DISPUTE:
        note = t(lang, "deal_dispute_new", id=deal_id, who=who, text=h(caption) if caption else t(lang, "deal_dispute_photo"))
        await _push_dispute(message.bot, db, settings, deal, message.from_user.id, note, file_id, to_admins=True)
    else:
        note = t(lang, "deal_photo_peer", id=deal_id, who=who)
        if caption:
            note = note + "\n" + h(caption)
        await _push_dispute(message.bot, db, settings, deal, message.from_user.id, note, file_id, to_admins=False)
    await message.answer(t(lang, "deal_photo_ok"), reply_markup=evidence_kb(lang, theme, deal_id))


@router.callback_query(DealCB.filter(F.a == "disth"))
async def dispute_thread(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    if call.from_user.id not in (deal["seller_id"], deal["buyer_id"]) and not settings.is_admin(call.from_user.id):
        await call.answer(t(lang, "error"), show_alert=True)
        return
    text = await _thread_text(db, deal["id"], lang)
    reason = ""
    try:
        reason = (deal["dispute_reason"] or "").strip()
    except (KeyError, IndexError, TypeError):
        reason = ""
    if reason:
        text = h(reason) + "\n\n" + text
    kb = InlineKeyboardBuilder()
    if deal["status"] == DEAL_DISPUTE:
        theme.add(kb, "deal_dispute_evidence", lang, callback_data=DealCB(a="disev", i=deal["id"]).pack())
        if settings.is_admin(call.from_user.id):
            theme.add(kb, "admin_reply", lang, callback_data=AdminCB(a="disr", i=deal["id"]).pack())
            theme.add(kb, "admin_buyer", lang, callback_data=AdminCB(a="win_b", i=deal["id"]).pack())
            theme.add(kb, "admin_seller", lang, callback_data=AdminCB(a="win_s", i=deal["id"]).pack())
    theme.add(kb, "btn_back", lang, callback_data=DealCB(a="open", i=deal["id"]).pack())
    kb.adjust(1)
    await paint(call, text, kb.as_markup(), screen="deal", settings=settings)


@router.callback_query(DealCB.filter(F.a == "rev"))
async def offer_reviews(call: CallbackQuery, callback_data: DealCB, db: Storage, lang: str):
    deal = await db.get_deal(callback_data.i)
    if deal is None:
        await call.answer(t(lang, "error"), show_alert=True)
        return
    seller_id = deal["seller_id"] if call.from_user.id == deal["buyer_id"] else deal["buyer_id"]
    rows = await db.reviews_for(seller_id)
    if not rows:
        await call.answer(t(lang, "no_reviews"), show_alert=True)
        return
    await call.message.answer("\n\n".join(f"• {r['text']}" for r in rows))
    await call.answer()


@router.callback_query(NavCB.filter(F.a == "hist"))
async def history(call: CallbackQuery, lang: str, theme: Theme, settings: Settings):
    await paint(call, t(lang, "history_role"), history_kb(lang, theme), screen="history", settings=settings)


@router.callback_query(NavCB.filter(F.a.in_({"hist_s", "hist_b"})))
async def history_list(call: CallbackQuery, callback_data: NavCB, db: Storage, lang: str, settings: Settings, theme: Theme):
    role = "seller" if callback_data.a == "hist_s" else "buyer"
    rows = await db.history(call.from_user.id, role)
    if not rows:
        await call.answer(t(lang, "history_empty"), show_alert=True)
        return
    lines = []
    for deal in rows:
        peer_id = deal["buyer_id"] if role == "seller" else deal["seller_id"]
        peer = await db.get_user(peer_id)
        lines.append(history_line(deal, call.from_user.id, username_of(peer) if peer else "-", lang, settings.currency))
    kb = InlineKeyboardBuilder()
    theme.add(kb, "btn_back", lang, callback_data=NavCB(a="hist").pack())
    theme.add(kb, "btn_menu", lang, callback_data=NavCB(a="menu").pack())
    kb.adjust(1)
    await paint(call, "\n\n".join(lines), kb.as_markup(), screen="history", settings=settings)
