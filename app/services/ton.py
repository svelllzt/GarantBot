from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Optional

import aiohttp

from app.config import Settings

log = logging.getLogger("ton")


def ton_comment_total(payload, comment: str) -> Optional[float]:
    if not isinstance(payload, dict):
        return None
    want = (comment or "").strip()
    if not want:
        return None
    total = 0
    found = False
    seen: set = set()
    for tx in payload.get("result") or []:
        if not isinstance(tx, dict):
            continue
        inn = tx.get("in_msg") or {}
        if not isinstance(inn, dict):
            continue
        msg = (inn.get("message") or inn.get("comment") or "").strip()
        if msg != want:
            continue
        try:
            nano = int(inn.get("value") or 0)
        except (TypeError, ValueError):
            continue
        if nano <= 0:
            continue
        tid = tx.get("transaction_id")
        if isinstance(tid, dict):
            key = (tid.get("hash"), tid.get("lt"))
        else:
            key = tx.get("hash") or tid
        if key is None:
            key = ("anon", id(tx))
        if key in seen:
            continue
        seen.add(key)
        total += nano
        found = True
    if not found:
        return None
    return total / 1_000_000_000


async def incoming_by_comment(settings: Settings, comment: str, address: str | None = None) -> Optional[float]:
    target = (address or settings.ton_address or "").strip()
    if not target or not comment:
        return None
    params = {"address": target, "limit": 40}
    headers = {}
    if settings.ton_api_key:
        headers["X-API-Key"] = settings.ton_api_key
    url = "https://testnet.toncenter.com/api/v2/getTransactions" if settings.ton_network.lower() == "testnet" else "https://toncenter.com/api/v2/getTransactions"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=20) as resp:
                payload = await resp.json()
    except Exception:
        log.exception("toncenter request failed")
        return None
    if not payload.get("ok"):
        return None
    return ton_comment_total(payload, comment)


USDT_MASTER = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
USDT_DECIMALS = 6


def _payload_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("comment", "text", "decoded", "value"):
            raw = value.get(key)
            if raw:
                return str(raw).strip()
        return ""
    return str(value).strip()


def _usdt_rows(payload) -> list:
    if not isinstance(payload, dict):
        return []
    rows = payload.get("jetton_transfers") or payload.get("transfers") or payload.get("result") or []
    if isinstance(rows, dict):
        rows = rows.get("jetton_transfers") or rows.get("transfers") or []
    return list(rows or [])


def _usdt_row_matches(row: dict, want: str) -> bool:
    msg = " ".join(
        part
        for part in (
            _payload_text(row.get("comment")),
            _payload_text(row.get("decoded_comment")),
            _payload_text(row.get("decoded_forward_payload")),
            _payload_text(row.get("forward_payload")),
        )
        if part
    )
    return (
        want in msg.split()
        or want == _payload_text(row.get("comment"))
        or want == _payload_text(row.get("decoded_comment"))
        or want == _payload_text(row.get("decoded_forward_payload"))
    )


def usdt_comment_total(payload, comment: str) -> Optional[float]:
    want = (comment or "").strip()
    if not want:
        return None
    total = 0
    found = False
    seen: set = set()
    for row in _usdt_rows(payload):
        if not isinstance(row, dict):
            continue
        if not _usdt_row_matches(row, want):
            continue
        raw_amt = row.get("amount") or row.get("jetton_amount") or 0
        try:
            units = int(str(raw_amt).split(".")[0])
        except (TypeError, ValueError):
            continue
        if units <= 0:
            continue
        key = row.get("transaction_hash") or row.get("query_id") or row.get("trace_id")
        if key is None:
            key = ("anon", id(row))
        if key in seen:
            continue
        seen.add(key)
        total += units
        found = True
    if not found:
        return None
    return total / (10 ** USDT_DECIMALS)


async def incoming_usdt_by_comment(settings: Settings, comment: str, address: str | None = None) -> Optional[float]:
    target = (address or settings.ton_address or "").strip()
    master = (getattr(settings, "usdt_master", None) or USDT_MASTER).strip() or USDT_MASTER
    if not target or not comment:
        return None
    host = "https://testnet.toncenter.com" if settings.ton_network.lower() == "testnet" else "https://toncenter.com"
    url = f"{host}/api/v3/jetton/transfers"
    params = {
        "owner_address": target,
        "jetton_master": master,
        "direction": "in",
        "limit": 50,
    }
    headers = {}
    if settings.ton_api_key:
        headers["X-API-Key"] = settings.ton_api_key
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=20) as resp:
                payload = await resp.json()
    except Exception:
        log.exception("toncenter jetton request failed")
        return None
    return usdt_comment_total(payload, comment)


def ton_to_currency(ton_amount: float, settings: Settings, requested: float) -> Optional[float]:
    if settings.ton_rate > 0:
        credited = round(ton_amount * settings.ton_rate, 2)
        if credited + 0.01 >= requested:
            return requested
        return None
    return None


def enough_ton(got: float, need: float) -> bool:
    return got + 1e-9 >= max(need - 0.001, 0)


def payout_ton(amount: float, commission: float, received: float, gas: float) -> float:
    payout = round(float(amount) * (100 - commission) / 100, 9)
    room = round(float(received) - max(gas, 0), 9)
    if room < payout:
        payout = room
    return max(payout, 0)


class TonEscrow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._wallet = None
        self._client = None
        self.address = (settings.ton_address or "").strip()
        self.can_send = False
        self._nano = False
        self._send_lock = asyncio.Lock()

    async def connect(self) -> None:
        mnemonic = (self.settings.ton_mnemonic or "").strip()
        if not mnemonic:
            return
        words = mnemonic.split()
        if len(words) not in (12, 24):
            log.warning("ton mnemonic must be 12 or 24 words")
            return
        is_testnet = self.settings.ton_network.lower() == "testnet"
        wallet = None
        nano = False
        try:
            from ton_core import NetworkGlobalID
            from tonutils.clients import ToncenterClient
            from tonutils.contracts import WalletV4R2

            net = NetworkGlobalID.TESTNET if is_testnet else NetworkGlobalID.MAINNET
            kwargs = {"network": net}
            if self.settings.ton_api_key:
                kwargs["api_key"] = self.settings.ton_api_key
            client = ToncenterClient(**kwargs)
            if hasattr(client, "connect"):
                await client.connect()
            result = WalletV4R2.from_mnemonic(client, words)
            if inspect.isawaitable(result):
                result = await result
            wallet, *_ = result
            self._client = client
            nano = True
        except Exception:
            try:
                from tonutils.client import ToncenterV3Client
                from tonutils.wallet import WalletV4R2

                kwargs = {"is_testnet": is_testnet, "rps": 1, "max_retries": 1}
                if self.settings.ton_api_key:
                    kwargs["api_key"] = self.settings.ton_api_key
                try:
                    client = ToncenterV3Client(**kwargs)
                except TypeError:
                    kwargs.pop("api_key", None)
                    client = ToncenterV3Client(**kwargs)
                result = WalletV4R2.from_mnemonic(client, words)
                if inspect.isawaitable(result):
                    result = await result
                wallet, *_ = result
                self._client = client
            except Exception:
                log.exception("ton V4 wallet init failed")
                return
        self._wallet = wallet
        self._nano = nano
        self.can_send = True
        derived = ""
        try:
            derived = wallet.address.to_str(is_user_friendly=True, is_bounceable=False)
        except TypeError:
            try:
                derived = wallet.address.to_str()
            except Exception:
                derived = str(wallet.address)
        if self.address and derived and self.address != derived:
            log.warning("TON address differs from WalletV4R2: ini=%s derived=%s", self.address, derived)
        if derived:
            self.address = derived
            if self.settings.ton_address != derived:
                try:
                    self.settings.patch("ton_address", derived)
                except Exception:
                    self.settings.ton_address = derived
                    log.exception("failed to write [ton] address")
        log.info("ton escrow %s send=%s", self.address, self.can_send)

    async def incoming(self, comment: str) -> Optional[float]:
        return await incoming_by_comment(self.settings, comment, address=self.address)

    def _tx_id(self, tx) -> Optional[str]:
        if tx is None:
            return None
        for attr in ("normalized_hash", "hash", "msg_hash"):
            value = getattr(tx, attr, None)
            if value and not callable(value):
                return str(value)
        text = str(tx).strip()
        return text or None

    def _gas_nano(self) -> int:
        gas = float(self.settings.ton_gas or 0.05)
        if gas <= 0:
            gas = 0.05
        try:
            from ton_core import to_nano

            return int(to_nano(str(gas)))
        except Exception:
            return int(round(gas * 1_000_000_000))

    async def send(self, dest: str, amount: float, comment: str = "") -> Optional[str]:
        if not self._wallet or amount <= 0:
            return None
        payload = amount
        if self._nano:
            try:
                from ton_core import to_nano

                payload = to_nano(amount)
            except Exception:
                payload = int(round(amount * 1_000_000_000))
        async with self._send_lock:
            try:
                tx = await self._wallet.transfer(
                    destination=dest,
                    amount=payload,
                    body=comment or None,
                )
            except Exception:
                log.exception("ton transfer failed")
                return None
        return self._tx_id(tx)

    async def send_usdt(self, dest: str, amount: float, comment: str = "") -> Optional[str]:
        if not self._wallet or amount <= 0:
            return None
        units = int(round(float(amount) * (10 ** USDT_DECIMALS)))
        if units <= 0:
            return None
        master = (self.settings.usdt_master or USDT_MASTER).strip() or USDT_MASTER
        builder_cls = None
        try:
            from tonutils.contracts.wallet import JettonTransferBuilder as builder_cls
        except Exception:
            builder_cls = None
        async with self._send_lock:
            try:
                if builder_cls is not None:
                    tx = await self._wallet.transfer_message(
                        builder_cls(
                            destination=dest,
                            jetton_amount=units,
                            jetton_master_address=master,
                            forward_payload=comment or None,
                            amount=self._gas_nano(),
                        )
                    )
                else:
                    fn = getattr(self._wallet, "transfer_jetton", None)
                    if fn is None:
                        return None
                    try:
                        tx = await fn(
                            destination=dest,
                            jetton_master_address=master,
                            jetton_amount=units,
                            jetton_decimals=USDT_DECIMALS,
                            forward_payload=comment or None,
                        )
                    except TypeError:
                        tx = await fn(
                            destination=dest,
                            jetton_master_address=master,
                            jetton_amount=float(amount),
                            jetton_decimals=USDT_DECIMALS,
                        )
            except Exception:
                log.exception("usdt transfer failed")
                return None
        return self._tx_id(tx)

    async def payout(self, dest: str, amount: float, asset: str, comment: str = "") -> Optional[str]:
        if (asset or "").upper() == "TON":
            return await self.send(dest, amount, comment)
        return await self.send_usdt(dest, amount, comment)

    async def close(self) -> None:
        client = self._client
        self._wallet = None
        self._client = None
        self.can_send = False
        self._nano = False
        if client is None:
            return
        closer = getattr(client, "close", None) or getattr(client, "aclose", None)
        if closer is None:
            return
        try:
            result = closer()
            if inspect.isawaitable(result):
                await result
        except Exception:
            pass
