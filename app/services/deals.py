from __future__ import annotations

from app.config import Settings
from app.i18n import t
from app.catalog import listing_allowed, needs_nft, normalize, payment_kind
from app.storage import (
    DEAL_CANCELLED,
    DEAL_CLOSED,
    DEAL_DISPUTE,
    DEAL_LISTED,
    DEAL_OPEN,
    DEAL_PENDING,
    DEAL_REVIEW,
    KIND_GOODS,
    NFT_AVAILABLE,
    NFT_LOCKED,
    NFT_TRANSFERRED,
    Storage,
)
from app.util import deal_asset, is_nft_deal, listing_is_buy, listing_owner, nft_title, seller_payout


class DealError(Exception):
    def __init__(self, key: str, **kwargs) -> None:
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)


async def peer_of(deal, user_id: int) -> int:
    return deal["seller_id"] if deal["buyer_id"] == user_id else deal["buyer_id"]


def _norm_asset(currency: str | None) -> str:
    return "TON" if (currency or "").upper() == "TON" else "USDT"


async def _need_buyer_funds(db: Storage, buyer_id: int, deal) -> None:
    amount = float(deal["amount"] or 0)
    if amount <= 0:
        raise DealError("deal_need_price")
    if not buyer_id:
        raise DealError("deal_need_deposit")
    asset = deal_asset(deal)
    buyer = await db.get_user(buyer_id)
    if buyer is None or db.available(buyer, asset) + 1e-12 < amount:
        raise DealError("deal_need_deposit")


async def _freeze_buyer(db: Storage, deal) -> None:
    amount = float(deal["amount"] or 0)
    asset = deal_asset(deal)
    try:
        await db.freeze_asset(deal["buyer_id"], asset, amount)
    except ValueError:
        raise DealError("deal_need_deposit")


async def _unfreeze_buyer(db: Storage, deal) -> None:
    amount = float(deal["amount"] or 0)
    if amount <= 0 or not deal["buyer_id"]:
        return
    await db.unfreeze_asset(deal["buyer_id"], deal_asset(deal), amount)


async def _release_nft(db: Storage, deal) -> None:
    if deal["nft_id"] and not deal["nft_sent"]:
        await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)


async def _capture_and_pay(db: Storage, settings: Settings, deal) -> float:
    amount = float(deal["amount"] or 0)
    asset = deal_asset(deal)
    payout = seller_payout(amount, settings.commission_percent, asset)
    await db.capture_asset(deal["buyer_id"], asset, amount)
    try:
        await db.credit_asset(deal["seller_id"], asset, payout)
    except Exception:
        await db.credit_asset(deal["buyer_id"], asset, amount)
        try:
            await db.freeze_asset(deal["buyer_id"], asset, amount)
        except ValueError:
            pass
        raise
    return payout


async def open_offer(
    db: Storage,
    actor_id: int,
    peer_id: int,
    as_buyer: bool = False,
    kind: str = KIND_GOODS,
    category: str = "goods",
    title: str = "",
    nft_id: int = 0,
    amount: float = 0,
    description: str = "",
    currency: str = "USDT",
    secret: str = "",
) -> int:
    if actor_id == peer_id:
        raise DealError("deal_self")
    if await db.active_deal(actor_id):
        active = await db.active_deal(actor_id)
        raise DealError("deal_busy_you", id=active["id"])
    if await db.active_deal(peer_id):
        active = await db.active_deal(peer_id)
        raise DealError("deal_busy_them")
    category = normalize(category)
    kind = payment_kind(category)
    seller_id = actor_id
    buyer_id = peer_id
    if as_buyer:
        raise DealError("deal_seller_only")
    nft = needs_nft(category)
    if nft and not nft_id:
        raise DealError("deal_nft_need_item")
    if float(amount or 0) <= 0:
        raise DealError("deal_need_price")
    deal_id = await db.create_deal(
        seller_id,
        buyer_id,
        kind,
        category=category,
        title=title or "",
        amount=amount,
        description=(description or "")[:1000],
        currency=_norm_asset(currency),
        secret=(secret or "")[:2000],
        exclusive=True,
    )
    if not deal_id:
        if await db.active_deal(actor_id):
            active = await db.active_deal(actor_id)
            raise DealError("deal_busy_you", id=active["id"])
        raise DealError("deal_busy_them")
    if nft:
        try:
            await attach_nft(db, deal_id, seller_id, nft_id)
        except DealError:
            await db.claim_deal(deal_id, DEAL_PENDING, status=DEAL_CANCELLED)
            deal = await db.get_deal(deal_id)
            if deal:
                await _release_nft(db, deal)
            locked = await db.get_nft(nft_id)
            if locked is not None and locked["status"] == NFT_LOCKED and locked["deal_id"] == deal_id:
                await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)
            raise
    return deal_id


async def create_listing(
    db: Storage,
    actor_id: int,
    category: str,
    title: str,
    amount: float,
    description: str,
    as_buyer: bool = False,
    nft_id: int = 0,
    currency: str = "USDT",
    secret: str = "",
) -> int:
    if as_buyer:
        raise DealError("deal_seller_only")
    if await db.active_deal(actor_id):
        active = await db.active_deal(actor_id)
        raise DealError("deal_busy_you", id=active["id"])
    category = normalize(category)
    if not listing_allowed(category):
        raise DealError("error")
    kind = payment_kind(category)
    title = (title or "").strip()[:120]
    if len(title) < 2:
        raise DealError("req_bad")
    if float(amount or 0) <= 0:
        raise DealError("deal_need_price")
    nft = needs_nft(category)
    if nft and not nft_id:
        raise DealError("deal_nft_need_item")
    deal_id = await db.create_deal(
        actor_id,
        0,
        kind,
        category=category,
        title=title,
        status=DEAL_LISTED,
        amount=amount,
        description=(description or "")[:1000],
        currency=_norm_asset(currency),
        secret=(secret or "")[:2000],
        exclusive=True,
    )
    if not deal_id:
        if await db.active_deal(actor_id):
            active = await db.active_deal(actor_id)
            raise DealError("deal_busy_you", id=active["id"])
        raise DealError("error")
    if nft:
        try:
            await attach_nft(db, deal_id, actor_id, nft_id)
        except DealError:
            await db.claim_deal(deal_id, DEAL_LISTED, status=DEAL_CANCELLED)
            deal = await db.get_deal(deal_id)
            if deal:
                await _release_nft(db, deal)
            locked = await db.get_nft(nft_id)
            if locked is not None and locked["status"] == NFT_LOCKED and locked["deal_id"] == deal_id:
                await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)
            raise
    return deal_id


async def take_listing(db: Storage, deal_id: int, taker_id: int, nft_id: int = 0) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_LISTED:
        raise DealError("deal_listed_taken")
    if taker_id in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("deal_self")
    if listing_is_buy(deal):
        raise DealError("deal_seller_only")
    if await db.active_deal(taker_id):
        active = await db.active_deal(taker_id)
        raise DealError("deal_busy_you", id=active["id"])
    nft = needs_nft(deal["category"] if "category" in deal.keys() else "")
    need = float(deal["amount"] or 0)
    if need <= 0:
        raise DealError("deal_need_price")
    if nft and not deal["nft_id"]:
        raise DealError("deal_nft_need_item")
    await _need_buyer_funds(db, taker_id, deal)
    if not await db.claim_open_for_user(deal_id, DEAL_LISTED, taker_id, buyer_id=taker_id):
        if await db.active_deal(taker_id):
            active = await db.active_deal(taker_id)
            raise DealError("deal_busy_you", id=active["id"])
        raise DealError("deal_listed_taken")
    deal = await db.get_deal(deal_id)
    try:
        await _freeze_buyer(db, deal)
    except DealError:
        await db.claim_deal(deal_id, DEAL_OPEN, status=DEAL_LISTED, buyer_id=0)
        raise


async def accept(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id != deal["buyer_id"]:
        raise DealError("error")
    if is_nft_deal(deal) and not deal["nft_id"]:
        raise DealError("deal_nft_need_item")
    await _need_buyer_funds(db, deal["buyer_id"], deal)
    if not await db.claim_open_for_user(deal_id, DEAL_PENDING, deal["buyer_id"]):
        if await db.active_deal(deal["buyer_id"]):
            active = await db.active_deal(deal["buyer_id"])
            if active and active["id"] != deal_id:
                raise DealError("deal_busy_them")
        raise DealError("error")
    deal = await db.get_deal(deal_id)
    try:
        await _freeze_buyer(db, deal)
    except DealError:
        await db.claim_deal(deal_id, DEAL_OPEN, status=DEAL_PENDING)
        raise


async def decline(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if not await db.claim_deal(deal_id, DEAL_PENDING, status=DEAL_CANCELLED):
        raise DealError("error")
    await _release_nft(db, deal)


async def set_price(db: Storage, deal_id: int, user_id: int, amount: float) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None:
        raise DealError("error")
    if deal["status"] != DEAL_LISTED:
        raise DealError("deal_price_locked")
    if listing_owner(deal) != user_id:
        raise DealError("error")
    await db.touch_deal(deal_id, amount=amount)


async def set_description(db: Storage, deal_id: int, user_id: int, text: str) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_LISTED:
        raise DealError("error")
    if listing_owner(deal) != user_id:
        raise DealError("error")
    await db.touch_deal(deal_id, description=text[:1000])


async def attach_nft(db: Storage, deal_id: int, user_id: int, nft_id: int) -> str:
    deal = await db.get_deal(deal_id)
    nft = await db.get_nft(nft_id)
    if deal is None or nft is None or deal["seller_id"] != user_id:
        raise DealError("error")
    if not is_nft_deal(deal):
        raise DealError("error")
    if deal["status"] not in {DEAL_OPEN, DEAL_LISTED, DEAL_PENDING}:
        raise DealError("error")
    if deal["nft_sent"]:
        raise DealError("error")
    if nft["owner_id"] != user_id:
        raise DealError("error")
    if nft["status"] == NFT_LOCKED and nft["deal_id"] == deal_id:
        await db.touch_deal(deal_id, nft_id=nft_id)
        return nft_title(nft)
    if nft["status"] != NFT_AVAILABLE:
        raise DealError("error")
    old_id = deal["nft_id"]
    if not await db.claim_nft(nft_id, NFT_AVAILABLE, NFT_LOCKED, deal_id=deal_id):
        raise DealError("error")
    if old_id and old_id != nft_id:
        await db.claim_nft(old_id, NFT_LOCKED, NFT_AVAILABLE, deal_id=None)
    await db.touch_deal(deal_id, nft_id=nft_id)
    return nft_title(nft)


async def complete(db: Storage, settings: Settings, deal_id: int, user_id: int) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id or deal["status"] != DEAL_OPEN:
        raise DealError("error")
    if is_nft_deal(deal) and not deal["nft_sent"]:
        raise DealError("deal_nft_wait_send")
    if not await db.claim_deal(deal_id, DEAL_OPEN, status=DEAL_REVIEW):
        raise DealError("error")
    try:
        payout = await _capture_and_pay(db, settings, deal)
    except Exception:
        await db.claim_deal(deal_id, DEAL_REVIEW, status=DEAL_OPEN)
        raise
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    if deal["nft_id"] and deal["nft_sent"]:
        await db.set_nft_status(
            deal["nft_id"],
            NFT_TRANSFERRED,
            owner_id=deal["buyer_id"],
            deal_id=deal_id,
        )
    return payout


async def close_after_review(db: Storage, deal_id: int) -> None:
    await db.claim_deal(deal_id, DEAL_REVIEW, status=DEAL_CLOSED)


async def cancel_mutual(db: Storage, deal_id: int, ton=None, by_user: int | None = None) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None:
        raise DealError("error")
    if deal["status"] in {DEAL_DISPUTE, DEAL_REVIEW, DEAL_CLOSED}:
        raise DealError("deal_cancel_denied")
    if deal["nft_sent"]:
        raise DealError("deal_cancel_denied")
    if deal["status"] == DEAL_LISTED:
        if not await db.claim_deal(deal_id, DEAL_LISTED, status=DEAL_CANCELLED, cancel_by=None):
            raise DealError("error")
        await _release_nft(db, deal)
        return
    if deal["status"] != DEAL_OPEN:
        raise DealError("deal_cancel_denied")
    if by_user is None:
        raise DealError("error")
    if by_user not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    asked = _cancel_asked(deal)
    other = deal["seller_id"] if by_user == deal["buyer_id"] else deal["buyer_id"]
    if not asked or asked != other:
        raise DealError("error")
    frozen = True
    prev = deal["status"]
    if not await db.claim_deal(deal_id, prev, status=DEAL_CANCELLED, cancel_by=None):
        raise DealError("error")
    if frozen:
        try:
            await _unfreeze_buyer(db, deal)
        except Exception:
            await db.claim_deal(deal_id, DEAL_CANCELLED, status=prev, cancel_by=asked)
            raise DealError("error")
    await _release_nft(db, deal)


def _party(deal, user_id: int) -> bool:
    return user_id in (deal["seller_id"], deal["buyer_id"])


def _cancel_asked(deal) -> int:
    try:
        return int(deal["cancel_by"] or 0)
    except (KeyError, IndexError, TypeError, ValueError):
        return 0


async def request_cancel(db: Storage, deal_id: int, user_id: int) -> str:
    deal = await db.get_deal(deal_id)
    if deal is None or not _party(deal, user_id):
        raise DealError("error")
    if deal["status"] in {DEAL_DISPUTE, DEAL_REVIEW, DEAL_CLOSED}:
        raise DealError("deal_cancel_denied")
    if deal["nft_sent"]:
        raise DealError("deal_cancel_denied")
    if deal["status"] == DEAL_LISTED:
        if listing_owner(deal) != user_id:
            raise DealError("error")
        await cancel_mutual(db, deal_id)
        return "done"
    if deal["status"] == DEAL_PENDING:
        await decline(db, deal_id, user_id)
        return "done"
    if deal["status"] != DEAL_OPEN:
        raise DealError("deal_cancel_denied")
    other = deal["seller_id"] if user_id == deal["buyer_id"] else deal["buyer_id"]
    asked = _cancel_asked(deal)
    if asked and asked == other:
        await cancel_mutual(db, deal_id, by_user=user_id)
        return "done"
    await db.touch_deal(deal_id, cancel_by=user_id)
    return "wait"


async def confirm_cancel(db: Storage, deal_id: int, user_id: int) -> None:
    await cancel_mutual(db, deal_id, by_user=user_id)


async def refuse_cancel(db: Storage, deal_id: int, user_id: int) -> int:
    deal = await db.get_deal(deal_id)
    if deal is None or not _party(deal, user_id):
        raise DealError("error")
    asked = _cancel_asked(deal)
    if not asked or asked == user_id:
        raise DealError("error")
    await db.touch_deal(deal_id, cancel_by=None)
    return asked


async def open_dispute(db: Storage, deal_id: int, user_id: int, reason: str = "") -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if deal["status"] == DEAL_DISPUTE:
        return
    if deal["status"] != DEAL_OPEN:
        raise DealError("error")
    if not await db.claim_deal(
        deal_id,
        deal["status"],
        status=DEAL_DISPUTE,
        dispute_reason=(reason or "")[:1000],
        dispute_by=user_id,
    ):
        again = await db.get_deal(deal_id)
        if again is not None and again["status"] == DEAL_DISPUTE:
            return
        raise DealError("error")


async def _settle_nft(db: Storage, deal, to_buyer: bool) -> None:
    if not deal["nft_id"]:
        return
    if deal["nft_sent"]:
        await db.set_nft_status(
            deal["nft_id"],
            NFT_TRANSFERRED,
            owner_id=deal["buyer_id"],
            deal_id=deal["id"],
        )
        return
    if to_buyer:
        return
    await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)


async def verdict_buyer(db: Storage, deal_id: int, ton=None) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    if not await db.claim_deal(deal_id, DEAL_DISPUTE, status=DEAL_CANCELLED):
        raise DealError("error")
    try:
        await _unfreeze_buyer(db, deal)
    except Exception:
        await db.claim_deal(deal_id, DEAL_CANCELLED, status=DEAL_DISPUTE)
        raise
    await _settle_nft(db, deal, to_buyer=False)


async def verdict_seller(db: Storage, settings: Settings, deal_id: int, ton=None) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    if not await db.claim_deal(deal_id, DEAL_DISPUTE, status=DEAL_CLOSED):
        raise DealError("error")
    try:
        payout = await _capture_and_pay(db, settings, deal)
    except Exception:
        await db.claim_deal(deal_id, DEAL_CLOSED, status=DEAL_DISPUTE)
        raise
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    await _settle_nft(db, deal, to_buyer=True)
    return payout


def err_text(lang: str, exc: DealError) -> str:
    return t(lang, exc.key, **exc.kwargs)
