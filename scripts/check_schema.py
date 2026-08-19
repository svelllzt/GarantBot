import asyncio
import os
import tempfile
from pathlib import Path

from app.i18n import EN, RU
from app.services.ton import ton_to_currency
from app.storage import DEAL_CLOSED, DEAL_LISTED, DEAL_OPEN, NFT_AVAILABLE, NFT_LOCKED, NFT_TRANSFERRED, Storage
from app.util import seller_payout


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
        await db.set_requisite(1, "ton_address", "UQD" + "A" * 45)
        await db.upsert_user(2, "buyer", "Пётр")
        deal_id = await db.create_deal(1, 2, currency="TON", secret="login:pass")
        await db.touch_deal(deal_id, amount=1.5)
        deal = await db.get_deal(deal_id)
        assert deal["currency"] == "TON"
        assert deal["secret"] == "login:pass"
        assert float(deal["amount"]) == 1.5
        row = await db.get_user(1)
        assert row["ton_address"].startswith("UQD")
        cols = await db._columns("users")
        for name in ("user_id", "nick", "username", "deals_count", "ton_address", "lang", "balance", "balance_ton", "frozen_usdt", "frozen_ton"):
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
            currency="USDT",
            secret="mail:pass",
        )
        listed = await db.get_deal(lid)
        assert listed["status"] == "listed"
        assert listed["category"] == "acc_rbx"
        assert listed["title"] == "Roblox"
        assert listed["buyer_id"] == 0
        assert listed["currency"] == "USDT"
        assert listed["secret"] == "mail:pass"
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
        open_nft = await db.create_deal(1, 2, category="nft", title="gift nft")
        await db.touch_deal(open_nft, nft_id=nft_id, status=DEAL_OPEN, amount=10)
        pending = await db.pending_nft_sends()
        assert any(r["id"] == open_nft for r in pending)
        await db.touch_deal(open_nft, nft_sent=1)
        assert not any(r["id"] == open_nft for r in await db.pending_nft_sends())
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
        for name in ("category", "title", "channel_msg_id", "kind", "dispute_reason", "dispute_by", "nft_sent", "currency", "secret"):
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

        await db.credit_asset(2, "USDT", 50)
        paid = await db.create_deal(1, 2, status=DEAL_OPEN, amount=10)
        assert await db.claim_deal(paid, DEAL_OPEN, status=DEAL_CLOSED)
        assert not await db.claim_deal(paid, DEAL_OPEN, status=DEAL_CLOSED)
        dep = await db.create_deposit(2, 5, "G2test1", asset="USDT")
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
        from app.keyboards import CatCB, NavCB, main_menu
        packed = CatCB(k="acc", g=1).pack()
        assert ":" not in CatCB(k="acc", g=1).k
        assert packed.startswith("cat:")
        parsed = CatCB.unpack(packed)
        assert parsed.k == "acc" and parsed.g == 1
        theme = Theme({})
        admin_cbs = [btn.callback_data or "" for row in main_menu("ru", theme, admin=True).inline_keyboard for btn in row]
        user_cbs = [btn.callback_data or "" for row in main_menu("ru", theme, admin=False).inline_keyboard for btn in row]
        assert NavCB(a="admin").pack() in admin_cbs
        assert NavCB(a="admin").pack() not in user_cbs

        from app.services import deals as dsvc
        from app.services.deals import DealError as DealErr

        for row in await db.fetchall("SELECT id FROM deals"):
            await db.touch_deal(row["id"], status=DEAL_CLOSED)
        await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)
        await db.credit_asset(2, "USDT", -float((await db.get_user(2))["balance"]))
        assert float((await db.get_user(2))["balance"]) == 0
        listed_nft = await dsvc.create_listing(
            db, 1, "nft", "Gift", 15, "unique gift", nft_id=nft_id, currency="USDT", secret="gift"
        )
        listed_row = await db.get_deal(listed_nft)
        assert listed_row["status"] == DEAL_LISTED
        assert listed_row["nft_id"] == nft_id
        assert listed_row["currency"] == "USDT"
        locked = await db.get_nft(nft_id)
        assert locked["status"] == NFT_LOCKED
        try:
            await dsvc.take_listing(db, listed_nft, 2)
            raise AssertionError("buyer without funds must fail")
        except DealErr as exc:
            assert exc.key == "deal_need_deposit"
        await db.credit_asset(2, "USDT", 20)
        await dsvc.take_listing(db, listed_nft, 2)
        taken = await db.get_deal(listed_nft)
        assert taken["status"] == DEAL_OPEN
        assert taken["buyer_id"] == 2
        buyer_row = await db.get_user(2)
        assert abs(db.available(buyer_row, "USDT") - 5) < 1e-9
        assert abs(db.frozen_of(buyer_row, "USDT") - 15) < 1e-9
        try:
            await db.spend_available(2, "USDT", 6)
            raise AssertionError("frozen funds must not be spendable")
        except ValueError:
            pass
        await db.spend_available(2, "USDT", 5)
        buyer_row = await db.get_user(2)
        assert abs(db.available(buyer_row, "USDT")) < 1e-9
        assert abs(db.frozen_of(buyer_row, "USDT") - 15) < 1e-9
        settings = Settings(dict(DEFAULTS), Path("config.ini"))
        try:
            await dsvc.complete(db, settings, listed_nft, 2)
            raise AssertionError("nft complete before send must fail")
        except DealErr as exc:
            assert exc.key == "deal_nft_wait_send"
        await db.touch_deal(listed_nft, nft_sent=1)
        try:
            await dsvc.cancel_mutual(db, listed_nft)
            raise AssertionError("cancel after nft send must fail")
        except DealErr as exc:
            assert exc.key == "deal_cancel_denied"
        payout = await dsvc.complete(db, settings, listed_nft, 2)
        assert abs(payout - seller_payout(15, settings.commission_percent, "USDT")) < 1e-9
        seller_row = await db.get_user(1)
        buyer_row = await db.get_user(2)
        assert abs(db.frozen_of(buyer_row, "USDT")) < 1e-9
        assert abs(db.available(seller_row, "USDT") - payout) < 1e-9
        assert (await db.get_nft(nft_id))["status"] == NFT_TRANSFERRED
        await db.touch_deal(listed_nft, status=DEAL_CLOSED)
        await db.set_nft_status(nft_id, NFT_AVAILABLE, deal_id=None)

        try:
            await dsvc.create_listing(db, 2, "nft", "Want gift", 20, "buy", as_buyer=True)
            raise AssertionError("buyer listings must fail")
        except DealErr as exc:
            assert exc.key == "deal_seller_only"

        await db.upsert_user(4, "accseller", "Акк")
        acc_id = await dsvc.create_listing(db, 4, "acc_rbx", "Roblox", 8, "mail unbound", currency="TON", secret="rbx:mail")
        acc = await db.get_deal(acc_id)
        assert not acc["nft_id"]
        assert acc["currency"] == "TON"
        try:
            await dsvc.take_listing(db, acc_id, 2)
            raise AssertionError("account listing without TON must fail")
        except DealErr as exc:
            assert exc.key == "deal_need_deposit"
        await db.credit_asset(2, "TON", 10)
        await dsvc.take_listing(db, acc_id, 2)
        opened_acc = await db.get_deal(acc_id)
        assert opened_acc["status"] == DEAL_OPEN
        assert opened_acc["buyer_id"] == 2
        buyer_row = await db.get_user(2)
        assert abs(db.available(buyer_row, "TON") - 2) < 1e-9
        assert abs(db.frozen_of(buyer_row, "TON") - 8) < 1e-9
        from app.keyboards import deal_kb
        from app.catalog import needs_nft
        assert not needs_nft("acc_rbx")
        seller4 = await db.get_user(4)
        seller_kb = deal_kb("ru", theme, opened_acc, 4, seller4)
        seller_cb = [btn.callback_data or "" for row in seller_kb.inline_keyboard for btn in row]
        assert not any(cb.startswith("deal:nft") for cb in seller_cb)
        assert any(cb.startswith("deal:dis") for cb in seller_cb)
        buyer_kb = deal_kb("ru", theme, opened_acc, 2, seller4)
        buyer_cb = [btn.callback_data or "" for row in buyer_kb.inline_keyboard for btn in row]
        assert any(cb.startswith("deal:ok") for cb in buyer_cb)
        assert any(cb.startswith("deal:dis") for cb in buyer_cb)
        assert not any(cb.startswith("deal:pdf") for cb in buyer_cb)
        assert not any(cb.startswith("deal:pay") for cb in buyer_cb)
        try:
            await dsvc.attach_nft(db, acc_id, 4, nft_id)
            raise AssertionError("account deal must not attach nft")
        except DealErr:
            pass
        payout_ton = await dsvc.complete(db, settings, acc_id, 2)
        assert abs(payout_ton - seller_payout(8, settings.commission_percent, "TON")) < 1e-9
        seller4 = await db.get_user(4)
        buyer_row = await db.get_user(2)
        assert abs(db.frozen_of(buyer_row, "TON")) < 1e-9
        assert abs(db.available(seller4, "TON") - payout_ton) < 1e-9
        await db.touch_deal(acc_id, status=DEAL_CLOSED)

        nft_d = await db.add_nft(1, gift_id="g5", slug="giftd", title="D", num=5, msg_id=102, from_user_id=1, is_unique=True)
        offer = await dsvc.open_offer(db, 1, 2, category="nft", title="GiftD", nft_id=nft_d, amount=3, currency="USDT")
        assert (await db.get_nft(nft_d))["status"] == NFT_LOCKED
        await dsvc.decline(db, offer, 2)
        assert (await db.get_nft(nft_d))["status"] == NFT_AVAILABLE
        await db.credit_asset(2, "USDT", 10)
        listed2 = await dsvc.create_listing(db, 1, "nft", "Gift2", 4, "x", nft_id=nft_d, currency="USDT")
        await dsvc.take_listing(db, listed2, 2)
        await db.touch_deal(listed2, nft_sent=1)
        await dsvc.open_dispute(db, listed2, 2, "bad")
        await dsvc.verdict_buyer(db, listed2)
        nft_after = await db.get_nft(nft_d)
        assert nft_after["status"] == NFT_TRANSFERRED
        assert nft_after["owner_id"] == 2

        cfg_fd, cfg_path = tempfile.mkstemp(suffix=".ini")
        os.close(cfg_fd)
        try:
            Path(cfg_path).write_text("[bot]\nadmin_ids = 1\n", encoding="utf-8")
            cfg = Settings(dict(DEFAULTS), Path(cfg_path))
            cfg.patch("admin_ids", "1")
            assert cfg.admins == frozenset({1})
            cfg.patch("admin_ids", "1,42")
            assert 42 in cfg.admins
            cfg.patch("ton_address", "EQDtestaddress")
            assert cfg.ton_address == "EQDtestaddress"
            cfg.patch("bank_session", "sess-value")
            assert cfg.bank_session == "sess-value"
        finally:
            os.unlink(cfg_path)

        await db.close()
        print("ok")
    finally:
        os.unlink(path)


if __name__ == "__main__":
    asyncio.run(main())
