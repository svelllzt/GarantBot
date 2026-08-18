from __future__ import annotations

import os
import shutil
from configparser import ConfigParser
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = ROOT / "config.ini.example"
DEFAULT_PATH = ROOT / "config.ini"

SECTIONS = ("bot", "bank", "ton", "fragment", "db")

FIELDS: dict[tuple[str, str], str] = {
    ("bot", "token"): "bot_token",
    ("bot", "admin_ids"): "admin_ids",
    ("bot", "support_username"): "support_username",
    ("bot", "support_chat"): "support_chat",
    ("bot", "commission_percent"): "commission_percent",
    ("bot", "currency"): "currency",
    ("bot", "min_deposit"): "min_deposit",
    ("bot", "min_withdraw"): "min_withdraw",
    ("bot", "deals_channel"): "deals_channel",
    ("bot", "assets"): "assets_dir",
    ("bank", "api_id"): "bank_api_id",
    ("bank", "api_hash"): "bank_api_hash",
    ("bank", "session"): "bank_session",
    ("bank", "username"): "bank_username",
    ("bank", "transfer_stars"): "bank_transfer_stars",
    ("bank", "min_stars"): "bank_min_stars",
    ("ton", "address"): "ton_address",
    ("ton", "api_key"): "ton_api_key",
    ("ton", "rate"): "ton_rate",
    ("ton", "mnemonic"): "ton_mnemonic",
    ("ton", "network"): "ton_network",
    ("ton", "gas"): "ton_gas",
    ("ton", "min_deal"): "min_ton_deal",
    ("ton", "min_rub"): "min_rub_deal",
    ("fragment", "mnemonic"): "fragment_mnemonic",
    ("fragment", "api_key"): "fragment_api_key",
    ("fragment", "cookies"): "fragment_cookies",
    ("fragment", "wallet"): "fragment_wallet",
    ("fragment", "stars"): "fragment_stars",
    ("fragment", "provider"): "fragment_provider",
    ("db", "path"): "db_path",
}

ATTR_TO_INI = {attr: pair for pair, attr in FIELDS.items()}

DEFAULTS: dict[str, Any] = {
    "bot_token": "",
    "admin_ids": "",
    "support_username": "support",
    "support_chat": "",
    "commission_percent": 2.0,
    "currency": "USDT",
    "min_deposit": 5.0,
    "min_withdraw": 10.0,
    "deals_channel": "",
    "assets_dir": "assets",
    "bank_api_id": 0,
    "bank_api_hash": "",
    "bank_session": "",
    "bank_username": "",
    "bank_transfer_stars": 25,
    "bank_min_stars": 50,
    "ton_address": "",
    "ton_api_key": "",
    "ton_rate": 0.0,
    "ton_mnemonic": "",
    "ton_network": "mainnet",
    "ton_gas": 0.05,
    "min_ton_deal": 0.1,
    "min_rub_deal": 1.0,
    "fragment_mnemonic": "",
    "fragment_api_key": "",
    "fragment_cookies": "",
    "fragment_wallet": "V4R2",
    "fragment_stars": 100,
    "fragment_provider": "toncenter",
    "db_path": "data/garant.db",
}

ENV_TO_ATTR = {
    "BOT_TOKEN": "bot_token",
    "ADMIN_IDS": "admin_ids",
    "SUPPORT_USERNAME": "support_username",
    "SUPPORT_CHAT": "support_chat",
    "COMMISSION_PERCENT": "commission_percent",
    "CURRENCY": "currency",
    "DEALS_CHANNEL": "deals_channel",
    "ASSETS": "assets_dir",
    "MIN_DEPOSIT": "min_deposit",
    "MIN_WITHDRAW": "min_withdraw",
    "BANK_API_ID": "bank_api_id",
    "BANK_API_HASH": "bank_api_hash",
    "BANK_SESSION": "bank_session",
    "BANK_USERNAME": "bank_username",
    "BANK_TRANSFER_STARS": "bank_transfer_stars",
    "BANK_MIN_STARS": "bank_min_stars",
    "TON_ADDRESS": "ton_address",
    "TON_API_KEY": "ton_api_key",
    "TON_RATE": "ton_rate",
    "TON_MNEMONIC": "ton_mnemonic",
    "TON_NETWORK": "ton_network",
    "TON_GAS": "ton_gas",
    "MIN_TON_DEAL": "min_ton_deal",
    "MIN_RUB_DEAL": "min_rub_deal",
    "FRAGMENT_MNEMONIC": "fragment_mnemonic",
    "FRAGMENT_API_KEY": "fragment_api_key",
    "FRAGMENT_COOKIES": "fragment_cookies",
    "FRAGMENT_WALLET": "fragment_wallet",
    "FRAGMENT_STARS": "fragment_stars",
    "FRAGMENT_PROVIDER": "fragment_provider",
    "DB_PATH": "db_path",
}


def config_path() -> Path:
    for env_name in ("PHANTOM_CONFIG", "GARANT_CONFIG"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    return DEFAULT_PATH


def _cast(attr: str, value: str) -> Any:
    sample = DEFAULTS[attr]
    text = (value or "").strip()
    if isinstance(sample, bool):
        return text.lower() in {"1", "true", "yes", "on"}
    if isinstance(sample, int) and not isinstance(sample, bool):
        if text == "":
            return 0
        return int(float(text))
    if isinstance(sample, float):
        if text == "":
            return 0.0
        return float(text.replace(",", "."))
    if attr == "bank_username":
        return text.lstrip("@")
    if attr in {"ton_mnemonic", "fragment_mnemonic"}:
        return " ".join(text.split())
    if attr == "fragment_wallet":
        return text.upper() or "V4R2"
    return text


def _parser() -> ConfigParser:
    parser = ConfigParser(interpolation=None)
    parser.optionxform = lambda s: s.strip().lower()
    return parser


def patch_ini(path: Path, section: str, key: str, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        if EXAMPLE_PATH.exists():
            shutil.copy(EXAMPLE_PATH, path)
        else:
            path.write_text(f"[{section}]\n{key} = {value}\n", encoding="utf-8")
            return
    raw = path.read_text(encoding="utf-8")
    newline = "\n" if "\n" in raw else "\r\n"
    ends = raw.endswith(("\n", "\r"))
    lines = raw.splitlines()
    section_l = section.lower()
    key_l = key.lower()
    current = None
    start = None
    end = len(lines)
    key_at = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            name = stripped[1:-1].strip().lower()
            if current == section_l:
                end = i
                break
            current = name
            if current == section_l:
                start = i
            continue
        if current == section_l:
            name, sep, _ = stripped.partition("=")
            if not sep:
                name, sep, _ = stripped.partition(":")
            if sep and name.strip().lower() == key_l:
                key_at = i
    clean = value.replace("\r", " ").replace("\n", " ").strip()
    if start is None:
        extra = ["", f"[{section}]", f"{key} = {clean}"]
        lines.extend(extra)
    elif key_at is not None:
        src = lines[key_at]
        eq = src.find("=")
        if eq < 0:
            eq = src.find(":")
        left = src[: eq + 1]
        if not left.endswith(" "):
            left += " "
        lines[key_at] = f"{left}{clean}"
    else:
        insert_at = end
        while insert_at > start + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        lines.insert(insert_at, f"{key} = {clean}")
    text = newline.join(lines)
    if ends and not text.endswith(newline):
        text += newline
    path.write_text(text, encoding="utf-8")


def _read_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].strip()
        name, sep, value = line.partition("=")
        if not sep:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        data[name.strip()] = value
    return data


def _write_ini(path: Path, values: dict[str, Any]) -> None:
    by_section: dict[str, list[tuple[str, str]]] = {name: [] for name in SECTIONS}
    for (section, key), attr in FIELDS.items():
        raw = values.get(attr, DEFAULTS[attr])
        if raw is None:
            raw = ""
        by_section[section].append((key, str(raw)))
    chunks = []
    titles = {
        "bot": "Бот",
        "bank": "Pyrogram / NFT-банк",
        "ton": "TON эскроу",
        "fragment": "Fragment / Stars",
        "db": "База",
    }
    for section in SECTIONS:
        chunks.append(f"; {titles[section]}")
        chunks.append(f"[{section}]")
        for key, value in by_section[section]:
            chunks.append(f"{key} = {value}")
        chunks.append("")
    path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")


def ensure_config(path: Path | None = None) -> Path:
    target = path or config_path()
    if target.exists():
        return target
    env_file = ROOT / ".env"
    env_data = _read_env_file(env_file)
    if env_data:
        values = dict(DEFAULTS)
        for env_key, attr in ENV_TO_ATTR.items():
            if env_key in env_data:
                values[attr] = _cast(attr, env_data[env_key])
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_ini(target, values)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    if EXAMPLE_PATH.exists():
        shutil.copy(EXAMPLE_PATH, target)
        return target
    _write_ini(target, dict(DEFAULTS))
    return target


def load_values(path: Path) -> dict[str, Any]:
    values = dict(DEFAULTS)
    parser = _parser()
    read = parser.read(path, encoding="utf-8")
    if not read:
        return values
    for (section, key), attr in FIELDS.items():
        if parser.has_option(section, key):
            values[attr] = _cast(attr, parser.get(section, key, raw=True))
    return values


class Settings:
    bot_token: str
    admin_ids: str
    support_username: str
    support_chat: str
    commission_percent: float
    currency: str
    min_deposit: float
    min_withdraw: float
    deals_channel: str
    assets_dir: str
    bank_api_id: int
    bank_api_hash: str
    bank_session: str
    bank_username: str
    bank_transfer_stars: int
    bank_min_stars: int
    ton_address: str
    ton_api_key: str
    ton_rate: float
    ton_mnemonic: str
    ton_network: str
    ton_gas: float
    min_ton_deal: float
    min_rub_deal: float
    fragment_mnemonic: str
    fragment_api_key: str
    fragment_cookies: str
    fragment_wallet: str
    fragment_stars: int
    fragment_provider: str
    db_path: str
    path: Path
    bot_username: str

    def __init__(self, values: dict[str, Any], path: Path) -> None:
        self.path = path
        self.bot_username = ""
        for key, default in DEFAULTS.items():
            setattr(self, key, values.get(key, default))

    @property
    def admins(self) -> frozenset[int]:
        ids = []
        for chunk in str(self.admin_ids).split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                ids.append(int(chunk))
        return frozenset(ids)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins

    def patch(self, attr: str, value: Any) -> None:
        if attr not in ATTR_TO_INI:
            raise KeyError(attr)
        text = "" if value is None else str(value).strip()
        if attr == "bank_username":
            text = text.lstrip("@")
        setattr(self, attr, _cast(attr, text))
        section, key = ATTR_TO_INI[attr]
        patch_ini(self.path, section, key, text)


@lru_cache
def get_settings() -> Settings:
    path = ensure_config()
    return Settings(load_values(path), path)
