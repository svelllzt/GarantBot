from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any, Awaitable, Callable, Optional

from app.config import Settings

log = logging.getLogger("fragment")

try:
    from FragmentAPI import FragmentClient
except Exception:
    FragmentClient = None

COOLDOWN = 90
NEED_COOKIES = ("stel_ssid", "stel_dt", "stel_token")


def parse_cookies(raw: str) -> dict[str, str]:
    text = (raw or "").strip()
    if not text:
        return {}
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(k): str(v) for k, v in data.items() if str(v).strip()}
    out: dict[str, str] = {}
    for part in text.split(";"):
        name, sep, value = part.strip().partition("=")
        if sep and name.strip():
            out[name.strip()] = value.strip()
    return out


def cookies_line(cookies: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in cookies.items() if value)


class StarsBuyer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.on_event: Optional[Callable[..., Awaitable[Any]]] = None
        self._lock = asyncio.Lock()
        self._next = 0.0

    def pack(self) -> int:
        n = int(self.settings.fragment_stars or 0)
        return n if n >= 50 else 100

    def username(self) -> str:
        return (self.settings.bank_username or "").lstrip("@")

    def mnemonic(self) -> str:
        return " ".join((self.settings.fragment_mnemonic or "").split())

    def api_key(self) -> str:
        return (self.settings.fragment_api_key or self.settings.ton_api_key or "").strip()

    def cookies(self) -> dict[str, str]:
        return parse_cookies(self.settings.fragment_cookies)

    def wallet_version(self) -> str:
        raw = (self.settings.fragment_wallet or "V4R2").strip().upper()
        return raw if raw in {"V4R2", "V5R1"} else "V4R2"

    def provider(self) -> str:
        raw = (self.settings.fragment_provider or "toncenter").strip().lower()
        return raw if raw in {"toncenter", "tonapi"} else "toncenter"

    def enabled(self) -> bool:
        if FragmentClient is None:
            return False
        words = self.mnemonic().split()
        cookies = self.cookies()
        return bool(
            len(words) in (12, 18, 24)
            and self.api_key()
            and self.username()
            and all(cookies.get(name) for name in NEED_COOKIES)
        )

    def status_key(self) -> str:
        if self.enabled():
            return "admin_fragment_on"
        if self.mnemonic():
            return "admin_fragment_wait"
        return "admin_fragment_off"

    def _persist_cookies(self, cookies: Any) -> bool:
        if isinstance(cookies, str):
            parsed = parse_cookies(cookies)
        elif isinstance(cookies, dict):
            parsed = {str(k): str(v) for k, v in cookies.items() if str(v).strip()}
        else:
            return False
        if not parsed:
            return False
        self.settings.patch("fragment_cookies", cookies_line(parsed))
        return True

    async def start(self) -> None:
        if not self.mnemonic():
            return
        if FragmentClient is None:
            log.warning("pip install fragment-api-py — автопокупка Stars выключена")
            return
        words = self.mnemonic().split()
        if len(words) not in (12, 18, 24):
            log.warning("fragment mnemonic must be 12, 18 or 24 words")
            return
        if not self.enabled() and sys.stdin.isatty() and not all(self.cookies().get(name) for name in NEED_COOKIES):
            await self._first_login()
        if self.enabled():
            if not self.cookies().get("stel_ton_token"):
                log.warning("fragment cookies without stel_ton_token — TON purchase may fail")
            log.info("fragment stars buyer @%s pack=%s★ %s", self.username(), self.pack(), self.wallet_version())
            return
        log.warning("fragment wallet is set, but cookies / api_key / [bank] username are missing")

    async def _ask(self, prompt: str) -> str:
        return (await asyncio.to_thread(input, prompt)).strip()

    async def _first_login(self) -> None:
        if FragmentClient is None:
            return
        print("\nFragment: кошелёк для автопокупки Telegram Stars за TON.")
        print("Ключ API: tonconsole.com или toncenter. Cookies сохранятся в [fragment] cookies.\n")
        try:
            if not self.api_key():
                raw = await self._ask("Tonconsole/Toncenter api_key (Enter — пропуск): ")
                if raw:
                    self.settings.patch("fragment_api_key", raw)
            phone = await self._ask("Телефон Telegram для Fragment (+7…) или Enter для QR: ")
            cookies = await FragmentClient.authenticate(
                seed=self.mnemonic(),
                wallet_version=self.wallet_version(),
                phone=phone or None,
                print_qr=not phone,
            )
            if not self._persist_cookies(cookies):
                print("Fragment не вернул cookies. Автопокупка Stars выключена.")
                return
            print("Fragment cookies сохранены.\n")
        except Exception:
            log.exception("fragment login failed")
            print("Fragment не вошёл. Бот запустится, Stars при нехватке сам не докупит.")

    async def _tell(self, key: str, **kwargs: Any) -> None:
        if self.on_event is None:
            return
        try:
            await self.on_event(key, **kwargs)
        except Exception:
            log.exception("fragment notify failed")

    async def buy_for_bank(self) -> bool:
        async with self._lock:
            return await self._buy()

    async def _buy(self) -> bool:
        now = asyncio.get_running_loop().time()
        if now < self._next:
            return False
        if not self.enabled():
            return False
        self._next = now + COOLDOWN
        user = self.username()
        amount = self.pack()
        try:
            async with FragmentClient(
                cookies=self.cookies(),
                seed=self.mnemonic(),
                api_key=self.api_key(),
                api_provider=self.provider(),
                wallet_version=self.wallet_version(),
            ) as client:
                result = await client.purchase_stars(
                    user,
                    amount,
                    show_sender=False,
                    payment_method="ton",
                )
        except Exception as exc:
            log.exception("fragment purchase_stars @%s %s failed", user, amount)
            await self._tell("admin_stars_buy_fail", user=user, error=str(exc)[:300] or exc.__class__.__name__)
            return False
        if result is None or result.__class__.__name__ == "EvmPaymentResult":
            log.warning("fragment purchase returned invoice instead of on-chain tx")
            await self._tell("admin_stars_buy_fail", user=user, error="invoice instead of TON tx")
            return False
        tx = getattr(result, "transaction_id", None) or "—"
        log.info("bought %s stars for @%s tx=%s", amount, user, tx)
        await self._tell("admin_stars_bought", user=user, amount=amount, tx=tx)
        return True
