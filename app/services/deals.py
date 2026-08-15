from __future__ import annotations

from app.config import Settings
from app.i18n import t
from app.storage import (
    DEAL_CANCELLED,
    DEAL_CLOSED,
    DEAL_DISPUTE,
    DEAL_OPEN,
    DEAL_PAID,
    DEAL_PENDING,
    DEAL_REVIEW,
    NFT_AVAILABLE,
    NFT_LOCKED,
    NFT_TRANSFERRED,
    Storage,
)
from app.util import nft_title, seller_payout


class DealError(Exception):
    def __init__(self, key: str, **kwargs) -> None:
        self.key = key
        self.kwargs = kwargs
        super().__init__(key)


async def peer_of(deal, user_id: int) -> int:
    return deal["seller_id"] if deal["buyer_id"] == user_id else deal["buyer_id"]


async def open_offer(db: Storage, actor_id: int, peer_id: int, as_buyer: bool) -> int:
    if actor_id == peer_id:
        raise DealError("deal_self")
    if await db.active_deal(actor_id):
        active = await db.active_deal(actor_id)
        raise DealError("deal_busy_you", id=active["id"])
    if await db.active_deal(peer_id):
        raise DealError("deal_busy_them")
    seller_id = peer_id if as_buyer else actor_id
    buyer_id = actor_id if as_buyer else peer_id
    return await db.create_deal(seller_id, buyer_id)


async def accept(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    await db.touch_deal(deal_id, status=DEAL_OPEN)


async def decline(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_PENDING:
        raise DealError("error")
    if user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    await db.touch_deal(deal_id, status=DEAL_CANCELLED)


async def set_price(db: Storage, deal_id: int, user_id: int, amount: float) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id:
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("deal_price_locked")
    await db.touch_deal(deal_id, amount=amount)


async def set_description(db: Storage, deal_id: int, user_id: int, text: str) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["seller_id"] != user_id or deal["status"] != DEAL_OPEN:
        raise DealError("error")
    await db.touch_deal(deal_id, description=text[:1000])


async def attach_nft(db: Storage, deal_id: int, user_id: int, nft_id: int) -> str:
    deal = await db.get_deal(deal_id)
    nft = await db.get_nft(nft_id)
    if deal is None or nft is None or deal["seller_id"] != user_id:
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("error")
    if nft["owner_id"] != user_id or nft["status"] != NFT_AVAILABLE:
        raise DealError("error")
    if deal["nft_id"]:
        old = await db.get_nft(deal["nft_id"])
        if old and old["status"] == NFT_LOCKED:
            await db.set_nft_status(old["id"], NFT_AVAILABLE, deal_id=None)
    await db.set_nft_status(nft_id, NFT_LOCKED, deal_id=deal_id)
    await db.touch_deal(deal_id, nft_id=nft_id)
    return nft_title(nft)


async def pay(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id:
        raise DealError("error")
    if deal["status"] != DEAL_OPEN:
        raise DealError("error")
    if deal["amount"] is None:
        raise DealError("deal_pay_no_amount")
    try:
        await db.change_balance(user_id, -float(deal["amount"]))
    except ValueError:
        buyer = await db.get_user(user_id)
        raise DealError(
            "deal_pay_low",
            need=f"{float(deal['amount']):.2f}",
            have=f"{float(buyer['balance']):.2f}",
        )
    await db.touch_deal(deal_id, status=DEAL_PAID)


async def complete(db: Storage, settings: Settings, deal_id: int, user_id: int) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["buyer_id"] != user_id or deal["status"] != DEAL_PAID:
        raise DealError("error")
    payout = seller_payout(deal["amount"], settings.commission_percent)
    await db.change_balance(deal["seller_id"], payout)
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    await db.touch_deal(deal_id, status=DEAL_CLOSED)
    return payout


async def close_after_review(db: Storage, deal_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None:
        return
    if deal["status"] == DEAL_REVIEW:
        await db.touch_deal(deal_id, status=DEAL_CLOSED)


async def cancel_mutual(db: Storage, deal_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None:
        raise DealError("error")
    if deal["status"] == DEAL_PAID:
        await db.change_balance(deal["buyer_id"], float(deal["amount"]))
    if deal["nft_id"] and not deal["nft_sent"]:
        await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)
    await db.touch_deal(deal_id, status=DEAL_CANCELLED)


async def open_dispute(db: Storage, deal_id: int, user_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or user_id not in (deal["seller_id"], deal["buyer_id"]):
        raise DealError("error")
    if deal["status"] != DEAL_PAID:
        raise DealError("error")
    await db.touch_deal(deal_id, status=DEAL_DISPUTE)


async def verdict_buyer(db: Storage, deal_id: int) -> None:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    if deal["amount"] is not None:
        await db.change_balance(deal["buyer_id"], float(deal["amount"]))
    if deal["nft_id"] and not deal["nft_sent"]:
        await db.set_nft_status(deal["nft_id"], NFT_AVAILABLE, deal_id=None)
    await db.touch_deal(deal_id, status=DEAL_CANCELLED)


async def verdict_seller(db: Storage, settings: Settings, deal_id: int) -> float:
    deal = await db.get_deal(deal_id)
    if deal is None or deal["status"] != DEAL_DISPUTE:
        raise DealError("error")
    payout = seller_payout(deal["amount"] or 0, settings.commission_percent)
    await db.change_balance(deal["seller_id"], payout)
    await db.bump_deals(deal["seller_id"], deal["buyer_id"])
    if deal["nft_id"] and deal["nft_sent"]:
        await db.set_nft_status(
            deal["nft_id"],
            NFT_TRANSFERRED,
            owner_id=deal["buyer_id"],
            deal_id=deal_id,
        )
    await db.touch_deal(deal_id, status=DEAL_CLOSED)
    return payout


def err_text(lang: str, exc: DealError) -> str:
    return t(lang, exc.key, **exc.kwargs)
