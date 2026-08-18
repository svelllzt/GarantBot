import asyncio
import os
import tempfile

from app.i18n import EN, RU
from app.services.ton import ton_to_currency
from app.storage import DEAL_CLOSED, DEAL_LISTED, DEAL_OPEN, DEAL_PAID, KIND_TON_RUB, NFT_AVAILABLE, NFT_LOCKED, Storage


async def main() -> None:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        db = Storage(path)
        await db.connect()
        user = await db.upsert_user(1, "seller", "Иван")
        assert user["user_id"] == 1
        assert user["nick"] == "Иван"
        assert user["username"] == "seller"
        assert user["deals_count"] == 0
        await db.set_requisite(1, "card", "4111111111111111")
        await db.set_requisite(1, "ton_address", "UQD" + "A" * 45)
        await db.upsert_user(2, "buyer", "Пётр")
        deal_id = await db.create_deal(1, 2, KIND_TON_RUB)
        await db.touch_deal(deal_id, ton_amount=1.5, rub_amount=10000, buyer_ton="UQ" + "B" * 46)
        deal = await db.get_deal(deal_id)
        assert deal["kind"] == KIND_TON_RUB
        assert float(deal["ton_amount"]) == 1.5
        assert float(deal["rub_amount"]) == 10000
        row = await db.get_user(1)
        assert row["card"] == "4111111111111111"
        assert row["ton_address"].startswith("UQD")
        cols = await db._columns("users")
        for name in ("user_id", "nick", "username", "deals_count", "card", "phone", "bank_name", "ton_address", "lang"):
            assert name in cols, name
        await db.set_lang(1, "en")
        again = await db.upsert_user(1, "seller", "Иван")
        assert again["lang"] == "en"
        lid = await db.create_deal(
            1,
            0,
            category="acc_rbx",
            title="Roblox",
            status="listed",
            amount=12.5,
            description="mail unbound",
        )
        listed = await db.get_deal(lid)
        assert listed["status"] == "listed"
        assert listed["category"] == "acc_rbx"
        assert listed["title"] == "Roblox"
        assert listed["buyer_id"] == 0
        feed = await db.listed_deals()
        assert feed and feed[0]["id"] == lid
        nft_id = await db.add_nft(
            1,
            gift_id="g1",
            slug="slug",
            title="Gift",
            num=7,
            msg_id=42,
            from_user_id=1,
            is_unique=True,
        )
        paid_id = await db.create_deal(1, 2, category="nft", title="gift nft")
        await db.touch_deal(paid_id, nft_id=nft_id, status="paid", amount=10)
        pending = await db.pending_nft_sends()
        assert any(r["id"] == paid_id for r in pending)
        await db.touch_deal(paid_id, nft_sent=1)
        assert not any(r["id"] == paid_id for r in await db.pending_nft_sends())
        await db.set_banned(1, True, "test")
        banned = await db.banned_users()
        assert banned and banned[0]["user_id"] == 1
        assert banned[0]["ban_reason"] == "test"
        await db.set_banned(1, False)
        assert not await db.banned_users()
        faq_id = await db.add_faq("Как оплатить", "How to pay", "С баланса", "From balance")
        await db.set_faq_photo(faq_id, "file123")
        item = await db.get_faq(faq_id)
        assert item["title_ru"] == "Как оплатить"
        assert item["photo_id"] == "file123"
        await db.set_screen("menu", "AgPHOTO")
        assert (await db.screen_map())["menu"] == "AgPHOTO"
        await db.add_dispute_msg(lid, 2, "не отвязал почту", is_admin=False)
        msgs = await db.dispute_messages(lid)
        assert msgs and msgs[0]["text"] == "не отвязал почту"
        info = await db.stats()
        assert info["users"] >= 2
        assert "deals" in info
        deal_cols = await db._columns("deals")
        for name in ("category", "title", "channel_msg_id", "kind", "dispute_reason", "dispute_by", "nft_sent", "receipt_id"):
            assert name in deal_cols, name

        missing = set(RU) - set(EN)
        extra = set(EN) - set(RU)
        assert not missing, missing
        assert not extra, extra
        from app.i18n import t
        from app.util import ban_notice
        from app.buttons import EMOJI, Theme
        from app.config import DEFAULTS, Settings
        from app.services.fragment import StarsBuyer, cookies_line, parse_cookies
        from pathlib import Path
        assert "menu" in t("ru", "admin_screen_ask", key="menu")
        assert "Иван" in t("ru", "welcome", name="Иван")
        assert "Phantom OTC" in t("ru", "welcome", name="Иван")
        assert "Phantom OTC" in t("en", "welcome", name="Ivan")
        assert parse_cookies("stel_ssid=a; stel_dt=b; stel_token=c") == {
            "stel_ssid": "a",
            "stel_dt": "b",
            "stel_token": "c",
        }
        assert parse_cookies('{"stel_ssid": "a", "stel_token": "b"}') == {"stel_ssid": "a", "stel_token": "b"}
        assert cookies_line({"a": "1", "b": "2"}) == "a=1; b=2"
        buyer = StarsBuyer(Settings(dict(DEFAULTS), Path("config.ini")))
        assert buyer.pack() == 100
        assert not buyer.enabled()
        assert buyer.status_key() == "admin_fragment_off"
        assert "btn_deal" in t("ru", "admin_btn_card", title="x", key="btn_deal", ru="a", en="b", style="s", emoji="e")
        notice = ban_notice("ru", "спам", "support")
        assert "спам" in notice and "support" in notice and "Доступ закрыт" in notice
        themed = Theme({"btn_deal": {"emoji_id": "123456789012345", "label_ru": "Сделка", "label_en": "Deal"}})
        labeled = themed.text("btn_deal", "ru")
        assert labeled == "Сделка"
        assert EMOJI["btn_deal"] not in labeled
        assert EMOJI["btn_deal"] in Theme({}).text("btn_deal", "ru")

        class _Rate:
            ton_rate = 0.0

        assert ton_to_currency(10.0, _Rate(), 100.0) is None
        _Rate.ton_rate = 10.0
        assert ton_to_currency(10.0, _Rate(), 100.0) == 100.0
        assert ton_to_currency(5.0, _Rate(), 100.0) is None

        await db.change_balance(2, 50)
        paid = await db.create_deal(1, 2, status=DEAL_OPEN, amount=10)
        assert await db.claim_deal(paid, DEAL_OPEN, status=DEAL_PAID)
        assert not await db.claim_deal(paid, DEAL_OPEN, status=DEAL_PAID)
        dep = await db.create_deposit(2, 5, "G2test1")
        assert await db.claim_deposit(dep, "done")
        assert not await db.claim_deposit(dep, "done")
        other = await db.add_nft(1, gift_id="g2", slug="slug", title="Dup", num=1, msg_id=99, from_user_id=1, is_unique=True)
        assert other is None
        nft_b = await db.add_nft(1, gift_id="g3", slug="other", title="B", num=2, msg_id=100, from_user_id=1, is_unique=True)
        assert nft_b
        assert await db.claim_nft(nft_b, NFT_AVAILABLE, NFT_LOCKED, deal_id=paid)
        assert not await db.claim_nft(nft_b, NFT_AVAILABLE, NFT_LOCKED, deal_id=paid)
        exclusive = await db.create_deal(1, 2, exclusive=True)
        assert exclusive is None
        from app.keyboards import CatCB
        packed = CatCB(k="acc", g=1).pack()
        assert ":" not in CatCB(k="acc", g=1).k
        assert packed.startswith("cat:")
        parsed = CatCB.unpack(packed)
        assert parsed.k == "acc" and parsed.g == 1

        from app.services import deals as dsvc
        from app.services.deals import DealError as DealErr

        for row in await db.fetchall("SELECT id FROM deals"):
            await db.touch_deal(row["id"], status=DEAL_CLOSED)
        await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)
        await db.change_balance(2, -float((await db.get_user(2))["balance"]))
        assert float((await db.get_user(2))["balance"]) == 0
        listed_nft = await dsvc.create_listing(
            db, 1, "nft", "Gift", 1500, "unique gift", nft_id=nft_id
        )
        listed_row = await db.get_deal(listed_nft)
        assert listed_row["status"] == DEAL_LISTED
        assert listed_row["nft_id"] == nft_id
        locked = await db.get_nft(nft_id)
        assert locked["status"] == NFT_LOCKED
        await dsvc.take_listing(db, listed_nft, 2)
        taken = await db.get_deal(listed_nft)
        assert taken["status"] == DEAL_OPEN
        assert taken["buyer_id"] == 2
        assert float((await db.get_user(2))["balance"]) == 0
        await db.touch_deal(listed_nft, receipt_id="pdf-file")
        assert (await db.get_deal(listed_nft))["receipt_id"] == "pdf-file"
        try:
            await dsvc.pay(db, listed_nft, 2)
            raise AssertionError("nft pay must fail")
        except DealErr as exc:
            assert exc.key == "deal_nft_no_pay"
        await db.touch_deal(listed_nft, status=DEAL_CLOSED)
        await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)
        await db.upsert_user(3, "seller2", "Оля")
        await db.set_requisite(3, "card", "5555555555554444")
        nft_c = await db.add_nft(3, gift_id="g4", slug="giftc", title="C", num=3, msg_id=101, from_user_id=3, is_unique=True)
        buy_ad = await dsvc.create_listing(
            db, 2, "nft", "Want gift", 2000, "buy", as_buyer=True
        )
        assert buy_ad
        want = await db.get_deal(buy_ad)
        assert want["seller_id"] == 0
        assert want["buyer_id"] == 2
        await dsvc.take_listing(db, buy_ad, 3, nft_id=nft_c)
        opened = await db.get_deal(buy_ad)
        assert opened["seller_id"] == 3
        assert opened["nft_id"] == nft_c

        await db.close()
        print("ok")
    finally:
        os.unlink(path)


if __name__ == "__main__":
    asyncio.run(main())
