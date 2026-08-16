from __future__ import annotations

import inspect
import logging
from typing import Optional

import aiohttp

from app.config import Settings

log = logging.getLogger("ton")


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
    for tx in payload.get("result") or []:
        inn = tx.get("in_msg") or {}
        msg = (inn.get("message") or inn.get("comment") or "").strip()
        if msg != comment:
            continue
        nano = int(inn.get("value") or 0)
        if nano <= 0:
            continue
        return nano / 1_000_000_000
    return None


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
        try:
            tx = await self._wallet.transfer(
                destination=dest,
                amount=payload,
                body=comment or None,
            )
        except Exception:
            log.exception("ton transfer failed")
            return None
        if tx is None:
            return None
        if hasattr(tx, "normalized_hash"):
            return str(tx.normalized_hash)
        return str(tx)

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
