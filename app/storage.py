from __future__ import annotations

import time
from typing import Any, Iterable, Optional

import aiosqlite

DEAL_PENDING = "pending"
DEAL_LISTED = "listed"
DEAL_OPEN = "open"
DEAL_WAIT_TON = "wait_ton"
DEAL_FUNDED = "funded"
DEAL_RUB_SENT = "rub_sent"
DEAL_PAID = "paid"
DEAL_DISPUTE = "dispute"
DEAL_REVIEW = "review"
DEAL_CLOSED = "closed"
DEAL_CANCELLED = "cancelled"

KIND_GOODS = "goods"
KIND_TON_RUB = "ton_rub"

NFT_AVAILABLE = "available"
NFT_LOCKED = "locked"
NFT_TRANSFERRED = "transferred"

ACTIVE_DEALS = (
    DEAL_PENDING,
    DEAL_LISTED,
    DEAL_OPEN,
    DEAL_WAIT_TON,
    DEAL_FUNDED,
    DEAL_RUB_SENT,
    DEAL_PAID,
    DEAL_DISPUTE,
)
DEAL_FIELDS = {
    "status",
    "amount",
    "nft_id",
    "description",
    "nft_sent",
    "kind",
    "ton_amount",
    "rub_amount",
    "buyer_ton",
    "ton_comment",
    "ton_received",
    "rub_marked",
    "payout_hash",
    "category",
    "title",
    "channel_msg_id",
    "buyer_id",
    "dispute_reason",
    "dispute_by",
}
WALLET_PENDING = "pending"
WALLET_DONE = "done"
WALLET_REJECTED = "rejected"


def now() -> int:
    return int(time.time())


class Storage:
    def __init__(self, path: str) -> None:
        self.path = path
        self.db: Optional[aiosqlite.Connection] = None
        self._buttons: Optional[dict[str, dict]] = None
        self._screens: Optional[dict[str, str]] = None

    async def connect(self) -> None:
        self.db = await aiosqlite.connect(self.path)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA foreign_keys=ON")
        await self._schema()

    async def close(self) -> None:
        if self.db:
            await self.db.close()
            self.db = None

    async def _schema(self) -> None:
        await self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                nick TEXT,
                first_name TEXT,
                lang TEXT,
                balance REAL NOT NULL DEFAULT 0,
                deals_count INTEGER NOT NULL DEFAULT 0,
                card TEXT,
                phone TEXT,
                bank_name TEXT,
                ton_address TEXT,
                banned INTEGER NOT NULL DEFAULT 0,
                ban_reason TEXT,
                banned_at INTEGER,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                amount REAL,
                status TEXT NOT NULL,
                nft_id INTEGER,
                description TEXT,
                nft_sent INTEGER NOT NULL DEFAULT 0,
                kind TEXT NOT NULL DEFAULT 'goods',
                category TEXT NOT NULL DEFAULT 'goods',
                title TEXT,
                channel_msg_id INTEGER,
                ton_amount REAL,
                rub_amount REAL,
                buyer_ton TEXT,
                ton_comment TEXT,
                ton_received REAL,
                rub_marked INTEGER NOT NULL DEFAULT 0,
                payout_hash TEXT,
                dispute_reason TEXT,
                dispute_by INTEGER,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_deals_seller ON deals(seller_id, status);
            CREATE INDEX IF NOT EXISTS idx_deals_buyer ON deals(buyer_id, status);

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                gift_id TEXT,
                slug TEXT,
                title TEXT NOT NULL,
                num INTEGER,
                msg_id INTEGER,
                from_user_id INTEGER,
                status TEXT NOT NULL,
                deal_id INTEGER,
                is_unique INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL,
                UNIQUE(msg_id)
            );
            CREATE INDEX IF NOT EXISTS idx_inv_owner ON inventory(owner_id, status);

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                deal_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                comment TEXT NOT NULL UNIQUE,
                tx_hash TEXT,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS buttons (
                key TEXT PRIMARY KEY,
                label_ru TEXT,
                label_en TEXT,
                style TEXT,
                emoji_id TEXT
            );

            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_ru TEXT NOT NULL,
                title_en TEXT,
                body_ru TEXT NOT NULL,
                body_en TEXT,
                photo_id TEXT,
                sort INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS screens (
                key TEXT PRIMARY KEY,
                file_id TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dispute_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                text TEXT,
                file_id TEXT,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_disp_deal ON dispute_messages(deal_id, id);
            """
        )
        await self._migrate()
        await self.db.commit()

    async def _columns(self, table: str) -> set[str]:
        cur = await self.db.execute(f"PRAGMA table_info({table})")
        rows = await cur.fetchall()
        return {row[1] for row in rows}

    async def _add_missing(self, table: str, columns: dict[str, str]) -> None:
        have = await self._columns(table)
        for name, ddl in columns.items():
            if name not in have:
                await self.db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")

    async def _migrate(self) -> None:
        await self._add_missing(
            "users",
            {
                "nick": "TEXT",
                "first_name": "TEXT",
                "username": "TEXT",
                "lang": "TEXT",
                "balance": "REAL NOT NULL DEFAULT 0",
                "deals_count": "INTEGER NOT NULL DEFAULT 0",
                "card": "TEXT",
                "phone": "TEXT",
                "bank_name": "TEXT",
                "ton_address": "TEXT",
                "banned": "INTEGER NOT NULL DEFAULT 0",
                "ban_reason": "TEXT",
                "banned_at": "INTEGER",
                "created_at": "INTEGER NOT NULL DEFAULT 0",
            },
        )
        await self._add_missing(
            "deals",
            {
                "kind": "TEXT NOT NULL DEFAULT 'goods'",
                "ton_amount": "REAL",
                "rub_amount": "REAL",
                "buyer_ton": "TEXT",
                "ton_comment": "TEXT",
                "ton_received": "REAL",
                "rub_marked": "INTEGER NOT NULL DEFAULT 0",
                "payout_hash": "TEXT",
                "category": "TEXT NOT NULL DEFAULT 'goods'",
                "title": "TEXT",
                "channel_msg_id": "INTEGER",
                "dispute_reason": "TEXT",
                "dispute_by": "INTEGER",
            },
        )
        await self.db.execute(
            """
            UPDATE users
            SET nick = COALESCE(NULLIF(nick, ''), first_name, username, CAST(user_id AS TEXT))
            WHERE nick IS NULL OR nick = ''
            """
        )
        await self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_deals_ton_comment ON deals(ton_comment)"
        )

    async def execute(self, sql: str, params: Iterable[Any] = ()) -> aiosqlite.Cursor:
        cur = await self.db.execute(sql, tuple(params))
        await self.db.commit()
        return cur

    async def fetchone(self, sql: str, params: Iterable[Any] = ()) -> Optional[aiosqlite.Row]:
        cur = await self.db.execute(sql, tuple(params))
        return await cur.fetchone()

    async def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[aiosqlite.Row]:
        cur = await self.db.execute(sql, tuple(params))
        return await cur.fetchall()

    async def upsert_user(self, user_id: int, username: Optional[str], first_name: str) -> aiosqlite.Row:
        row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        uname = (username or "").lstrip("@").lower() or None
        nick = (first_name or "").strip() or uname or str(user_id)
        if row is None:
            await self.execute(
                """
                INSERT INTO users (user_id, username, nick, first_name, deals_count, created_at)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (user_id, uname, nick, first_name, now()),
            )
        else:
            await self.execute(
                "UPDATE users SET username = ?, nick = ?, first_name = ? WHERE user_id = ?",
                (uname, nick, first_name, user_id),
            )
        return await self.get_user(user_id)

    async def get_user(self, user_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

    async def get_user_by_username(self, username: str) -> Optional[aiosqlite.Row]:
        clean = username.lstrip("@").lower()
        return await self.fetchone("SELECT * FROM users WHERE username = ?", (clean,))

    async def set_lang(self, user_id: int, lang: str) -> None:
        code = lang if lang in {"ru", "en"} else "ru"
        await self.execute("UPDATE users SET lang = ? WHERE user_id = ?", (code, user_id))

    async def set_banned(self, user_id: int, banned: bool, reason: str | None = None) -> None:
        if banned:
            await self.execute(
                "UPDATE users SET banned = 1, ban_reason = ?, banned_at = ? WHERE user_id = ?",
                ((reason or "").strip()[:500] or None, now(), user_id),
            )
            return
        await self.execute(
            "UPDATE users SET banned = 0, ban_reason = NULL, banned_at = NULL WHERE user_id = ?",
            (user_id,),
        )

    async def banned_users(self) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM users WHERE banned = 1 ORDER BY banned_at DESC, user_id DESC"
        )

    async def set_requisite(self, user_id: int, field: str, value: Optional[str]) -> None:
        if field not in {"card", "phone", "bank_name", "ton_address"}:
            raise ValueError(field)
        await self.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))

    async def change_balance(self, user_id: int, delta: float) -> float:
        cur = await self.db.execute(
            """
            UPDATE users
            SET balance = ROUND(balance + ?, 2)
            WHERE user_id = ? AND ROUND(balance + ?, 2) >= 0
            """,
            (delta, user_id, delta),
        )
        await self.db.commit()
        if cur.rowcount != 1:
            raise ValueError("insufficient")
        row = await self.get_user(user_id)
        return float(row["balance"])

    async def set_balance(self, user_id: int, amount: float) -> None:
        await self.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (round(amount, 2), user_id),
        )

    async def bump_deals(self, *user_ids: int) -> None:
        for uid in user_ids:
            await self.execute(
                "UPDATE users SET deals_count = deals_count + 1 WHERE user_id = ?",
                (uid,),
            )

    async def user_ids(self) -> list[int]:
        rows = await self.fetchall("SELECT user_id FROM users")
        return [r["user_id"] for r in rows]

    async def stats(self) -> dict[str, Any]:
        users = await self.fetchone("SELECT COUNT(*) AS c FROM users")
        banned = await self.fetchone("SELECT COUNT(*) AS c FROM users WHERE banned = 1")
        total = await self.fetchone("SELECT COUNT(*) AS c FROM deals")
        closed = await self.fetchone(
            "SELECT COUNT(*) AS c FROM deals WHERE status = ?",
            (DEAL_CLOSED,),
        )
        volume = await self.fetchone(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM deals WHERE status = ?",
            (DEAL_CLOSED,),
        )
        escrow = await self.fetchone(
            f"""
            SELECT COALESCE(SUM(amount), 0) AS s FROM deals
            WHERE status IN (?, ?, ?, ?)
            """,
            (DEAL_PAID, DEAL_FUNDED, DEAL_RUB_SENT, DEAL_DISPUTE),
        )
        by_status = await self.fetchall(
            "SELECT status, COUNT(*) AS c FROM deals GROUP BY status"
        )
        by_cat = await self.fetchall(
            "SELECT category, COUNT(*) AS c FROM deals GROUP BY category ORDER BY c DESC"
        )
        disputes = await self.fetchone(
            "SELECT COUNT(*) AS c FROM deals WHERE status = ?",
            (DEAL_DISPUTE,),
        )
        return {
            "users": users["c"],
            "banned": banned["c"],
            "deals": total["c"],
            "closed": closed["c"],
            "volume": float(volume["s"]),
            "escrow": float(escrow["s"]),
            "disputes": disputes["c"],
            "by_status": {row["status"]: row["c"] for row in by_status},
            "by_cat": [(row["category"], row["c"]) for row in by_cat],
        }

    async def recent_deals(self, limit: int = 15) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM deals ORDER BY id DESC LIMIT ?",
            (limit,),
        )

    async def create_deal(
        self,
        seller_id: int,
        buyer_id: int,
        kind: str = KIND_GOODS,
        *,
        category: str = "goods",
        title: str = "",
        status: str | None = None,
        amount: float | None = None,
        description: str | None = None,
    ) -> int:
        if kind not in {KIND_GOODS, KIND_TON_RUB}:
            kind = KIND_GOODS
        cur = await self.execute(
            """
            INSERT INTO deals (
                seller_id, buyer_id, status, kind, category, title, amount, description, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seller_id,
                buyer_id,
                status or DEAL_PENDING,
                kind,
                category or "goods",
                (title or "")[:120] or None,
                amount,
                description,
                now(),
                now(),
            ),
        )
        return cur.lastrowid

    async def get_deal(self, deal_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM deals WHERE id = ?", (deal_id,))

    async def listed_deals(self, limit: int = 12) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM deals WHERE status = ? ORDER BY id DESC LIMIT ?",
            (DEAL_LISTED, limit),
        )

    async def active_deal(self, user_id: int) -> Optional[aiosqlite.Row]:
        placeholders = ",".join("?" * len(ACTIVE_DEALS))
        return await self.fetchone(
            f"""
            SELECT * FROM deals
            WHERE (seller_id = ? OR buyer_id = ?) AND status IN ({placeholders})
            ORDER BY id DESC LIMIT 1
            """,
            (user_id, user_id, *ACTIVE_DEALS),
        )

    async def touch_deal(self, deal_id: int, **fields) -> None:
        deal = await self.get_deal(deal_id)
        if deal is None:
            return
        if fields.pop("clear_nft", False):
            fields["nft_id"] = None
        if not fields:
            return
        sets = ["updated_at = ?"]
        values: list[Any] = [now()]
        for key, value in fields.items():
            if key not in DEAL_FIELDS:
                raise ValueError(key)
            sets.append(f"{key} = ?")
            values.append(value)
        values.append(deal_id)
        await self.execute(f"UPDATE deals SET {', '.join(sets)} WHERE id = ?", values)

    async def history(self, user_id: int, role: str, limit: int = 15) -> list[aiosqlite.Row]:
        column = "seller_id" if role == "seller" else "buyer_id"
        return await self.fetchall(
            f"""
            SELECT * FROM deals
            WHERE {column} = ? AND status IN (?, ?)
            ORDER BY id DESC LIMIT ?
            """,
            (user_id, DEAL_CLOSED, DEAL_CANCELLED, limit),
        )

    async def open_disputes(self) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM deals WHERE status = ? ORDER BY id DESC",
            (DEAL_DISPUTE,),
        )

    async def add_review(self, seller_id: int, buyer_id: int, deal_id: int, text: str) -> None:
        await self.execute(
            """
            INSERT INTO reviews (seller_id, buyer_id, deal_id, text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (seller_id, buyer_id, deal_id, text, now()),
        )

    async def reviews_for(self, seller_id: int, limit: int = 10) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM reviews WHERE seller_id = ? ORDER BY id DESC LIMIT ?",
            (seller_id, limit),
        )

    async def add_nft(
        self,
        owner_id: int,
        *,
        gift_id: Optional[str],
        slug: Optional[str],
        title: str,
        num: Optional[int],
        msg_id: Optional[int],
        from_user_id: Optional[int],
        is_unique: bool,
    ) -> Optional[int]:
        if msg_id is not None:
            existing = await self.fetchone("SELECT id FROM inventory WHERE msg_id = ?", (msg_id,))
            if existing:
                return None
        cur = await self.execute(
            """
            INSERT INTO inventory
                (owner_id, gift_id, slug, title, num, msg_id, from_user_id, status, is_unique, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_id,
                gift_id,
                slug,
                title,
                num,
                msg_id,
                from_user_id,
                NFT_AVAILABLE,
                int(is_unique),
                now(),
            ),
        )
        return cur.lastrowid

    async def get_nft(self, nft_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM inventory WHERE id = ?", (nft_id,))

    async def nfts_of(self, owner_id: int, status: Optional[str] = None) -> list[aiosqlite.Row]:
        if status:
            return await self.fetchall(
                "SELECT * FROM inventory WHERE owner_id = ? AND status = ? ORDER BY id DESC",
                (owner_id, status),
            )
        return await self.fetchall(
            "SELECT * FROM inventory WHERE owner_id = ? ORDER BY id DESC",
            (owner_id,),
        )

    async def set_nft_status(
        self,
        nft_id: int,
        status: str,
        *,
        deal_id=...,
        owner_id=...,
    ) -> None:
        nft = await self.get_nft(nft_id)
        if nft is None:
            return
        await self.execute(
            """
            UPDATE inventory SET status = ?, deal_id = ?, owner_id = ?
            WHERE id = ?
            """,
            (
                status,
                nft["deal_id"] if deal_id is ... else deal_id,
                nft["owner_id"] if owner_id is ... else owner_id,
                nft_id,
            ),
        )

    async def create_deposit(self, user_id: int, amount: float, comment: str) -> int:
        cur = await self.execute(
            """
            INSERT INTO deposits (user_id, amount, comment, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, round(amount, 2), comment, WALLET_PENDING, now()),
        )
        return cur.lastrowid

    async def deposit_by_comment(self, comment: str) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM deposits WHERE comment = ?", (comment,))

    async def get_deposit(self, deposit_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM deposits WHERE id = ?", (deposit_id,))

    async def pending_deposits(self) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM deposits WHERE status = ? ORDER BY id DESC",
            (WALLET_PENDING,),
        )

    async def finish_deposit(self, deposit_id: int, status: str, tx_hash: Optional[str] = None) -> None:
        await self.execute(
            "UPDATE deposits SET status = ?, tx_hash = COALESCE(?, tx_hash) WHERE id = ?",
            (status, tx_hash, deposit_id),
        )

    async def create_withdraw(self, user_id: int, amount: float, method: str, details: str) -> int:
        cur = await self.execute(
            """
            INSERT INTO withdrawals (user_id, amount, method, details, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, round(amount, 2), method, details, WALLET_PENDING, now()),
        )
        return cur.lastrowid

    async def get_withdraw(self, withdraw_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM withdrawals WHERE id = ?", (withdraw_id,))

    async def pending_withdraws(self) -> list[aiosqlite.Row]:
        return await self.fetchall(
            "SELECT * FROM withdrawals WHERE status = ? ORDER BY id DESC",
            (WALLET_PENDING,),
        )

    async def finish_withdraw(self, withdraw_id: int, status: str) -> None:
        await self.execute("UPDATE withdrawals SET status = ? WHERE id = ?", (status, withdraw_id))

    async def button_map(self) -> dict[str, dict]:
        if self._buttons is None:
            rows = await self.fetchall("SELECT * FROM buttons")
            self._buttons = {r["key"]: dict(r) for r in rows}
        return self._buttons

    async def patch_button(self, key: str, **fields) -> None:
        row = dict((await self.button_map()).get(key) or {})
        row.update(fields)
        await self.execute(
            """
            INSERT INTO buttons (key, label_ru, label_en, style, emoji_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                label_ru = excluded.label_ru,
                label_en = excluded.label_en,
                style = excluded.style,
                emoji_id = excluded.emoji_id
            """,
            (
                key,
                row.get("label_ru"),
                row.get("label_en"),
                row.get("style"),
                row.get("emoji_id"),
            ),
        )
        self._buttons = None

    async def reset_button(self, key: str) -> None:
        await self.execute("DELETE FROM buttons WHERE key = ?", (key,))
        self._buttons = None

    async def screen_map(self) -> dict[str, str]:
        if self._screens is None:
            rows = await self.fetchall("SELECT key, file_id FROM screens")
            self._screens = {r["key"]: r["file_id"] for r in rows}
        return self._screens

    async def set_screen(self, key: str, file_id: str) -> None:
        await self.execute(
            """
            INSERT INTO screens (key, file_id) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET file_id = excluded.file_id
            """,
            (key, file_id),
        )
        self._screens = None

    async def clear_screen(self, key: str) -> None:
        await self.execute("DELETE FROM screens WHERE key = ?", (key,))
        self._screens = None

    async def faq_all(self) -> list[aiosqlite.Row]:
        return await self.fetchall("SELECT * FROM faq ORDER BY sort, id")

    async def get_faq(self, faq_id: int) -> Optional[aiosqlite.Row]:
        return await self.fetchone("SELECT * FROM faq WHERE id = ?", (faq_id,))

    async def add_faq(self, title_ru: str, title_en: str, body_ru: str, body_en: str) -> int:
        rows = await self.faq_all()
        sort = (rows[-1]["sort"] + 1) if rows else 0
        cur = await self.execute(
            """
            INSERT INTO faq (title_ru, title_en, body_ru, body_en, sort, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title_ru[:120], title_en[:120], body_ru[:3500], body_en[:3500], sort, now()),
        )
        return cur.lastrowid

    async def set_faq_photo(self, faq_id: int, photo_id: str | None) -> None:
        await self.execute("UPDATE faq SET photo_id = ? WHERE id = ?", (photo_id, faq_id))

    async def delete_faq(self, faq_id: int) -> None:
        await self.execute("DELETE FROM faq WHERE id = ?", (faq_id,))

    async def add_dispute_msg(
        self,
        deal_id: int,
        user_id: int,
        text: str | None = None,
        file_id: str | None = None,
        is_admin: bool = False,
    ) -> int:
        cur = await self.execute(
            """
            INSERT INTO dispute_messages (deal_id, user_id, is_admin, text, file_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (deal_id, user_id, int(is_admin), (text or "")[:3500] or None, file_id, now()),
        )
        return cur.lastrowid

    async def dispute_messages(self, deal_id: int, limit: int = 40) -> list[aiosqlite.Row]:
        return await self.fetchall(
            """
            SELECT * FROM (
                SELECT * FROM dispute_messages WHERE deal_id = ? ORDER BY id DESC LIMIT ?
            ) AS t ORDER BY t.id
            """,
            (deal_id, limit),
        )
