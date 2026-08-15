import argparse
import asyncio
import json
import sys
from pathlib import Path

from pyrogram import Client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings


def _help(path: Path) -> str:
    return f"""
Сессия Pyrogram пишется СЮДА, библиотеку патчить не нужно:

  {path}
  секция [bank], ключ session

Новую юзер-сессию без телефона Telegram не выдаёт. Код приходит в SMS / Telegram.

Без телефона можно так:
  • вставить уже готовую строку session в [bank] session
    (из другого pyrogram/pyrofork selfbot, не Telethon)
  • импортировать файл:

      python scripts/login_bank.py --from путь/к/config.json
      python scripts/login_bank.py --from путь/к/имя.session
      python scripts/login_bank.py --from папка_selfbot

Юзер-аккаунт для NFT-банка (нужен телефон один раз):

      python scripts/login_bank.py --user

api_id и api_hash всё равно нужны в [bank] — https://my.telegram.org
""".strip()


def _json_pick(data: dict, *keys: str) -> str:
    lower = {str(k).lower(): v for k, v in data.items()}
    for key in keys:
        value = lower.get(key.lower())
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _read_json(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit(f"{path} — ожидался JSON-объект")
    nested = raw.get("config") if isinstance(raw.get("config"), dict) else {}
    merged = dict(nested)
    merged.update(raw)
    return merged


def _find_in_dir(folder: Path) -> Path:
    names = ("config.json", "session.json", "config.ini")
    for name in names:
        candidate = folder / name
        if candidate.exists():
            return candidate
    sessions = sorted(folder.glob("*.session"))
    if sessions:
        return sessions[0]
    raise SystemExit(f"В {folder} нет config.json и .session")


def _session_from_json(data: dict) -> str:
    return _json_pick(
        data,
        "session",
        "session_string",
        "string_session",
        "pyrogram_session",
        "sessionstring",
    )


async def _export_from_file(settings, session_file: Path) -> tuple[str, str, int]:
    if not settings.bank_api_id or not settings.bank_api_hash:
        raise SystemExit("Для .session нужны api_id и api_hash в config.ini [bank]")
    workdir = session_file.parent
    name = session_file.stem
    async with Client(
        name=name,
        api_id=settings.bank_api_id,
        api_hash=settings.bank_api_hash,
        workdir=str(workdir),
    ) as client:
        me = await client.get_me()
        session = await client.export_session_string()
    return session, me.username or "", me.id


async def _login_user(settings) -> tuple[str, str, int]:
    if not settings.bank_api_id or not settings.bank_api_hash:
        raise SystemExit("Укажите api_id и api_hash в config.ini секция [bank] (my.telegram.org)")
    workdir = ROOT / "data"
    workdir.mkdir(parents=True, exist_ok=True)
    async with Client(
        name="bank_login",
        api_id=settings.bank_api_id,
        api_hash=settings.bank_api_hash,
        workdir=str(workdir),
    ) as client:
        me = await client.get_me()
        session = await client.export_session_string()
    leftover = workdir / "bank_login.session"
    if leftover.exists():
        leftover.unlink()
    journal = workdir / "bank_login.session-journal"
    if journal.exists():
        journal.unlink()
    return session, me.username or "", me.id


def _save(settings, session: str, username: str, user_id: int) -> None:
    settings.patch("bank_session", session)
    if username:
        settings.patch("bank_username", username)
    print(f"logged in as @{username or '-'} id={user_id}")
    print(f"patched {settings.path} [bank] session")


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Пишет Pyrogram-сессию в config.ini [bank] session",
    )
    parser.add_argument("--user", action="store_true", help="войти по номеру телефона (юзер для NFT)")
    parser.add_argument("--from", dest="source", help="готовая session / config.json / папка selfbot / .session")
    args = parser.parse_args()
    if not args.user and not args.source:
        print(_help(settings.path))
        if settings.bank_session:
            print("Сейчас [bank] session уже заполнен.")
        else:
            print("Сейчас [bank] session пустой.")
        return
    if args.source:
        src = Path(args.source).expanduser()
        if not src.exists():
            raise SystemExit(f"Нет файла: {src}")
        if src.is_dir():
            src = _find_in_dir(src)
        if src.suffix.lower() == ".json":
            data = _read_json(src)
            api_id = _json_pick(data, "api_id", "apiid", "app_id")
            api_hash = _json_pick(data, "api_hash", "apihash", "app_hash")
            session = _session_from_json(data)
            username = _json_pick(data, "username", "bank_username")
            if api_id:
                settings.patch("bank_api_id", api_id)
            if api_hash:
                settings.patch("bank_api_hash", api_hash)
            if not session:
                raise SystemExit(
                    f"В {src} нет session-строки Pyrogram.\n"
                    "Telethon-сессия сюда не подходит. Нужен ключ session / session_string."
                )
            settings.patch("bank_session", session)
            if username:
                settings.patch("bank_username", username)
            print(f"импорт из {src}")
            print(f"patched {settings.path} [bank] session")
            return
        if src.suffix.lower() == ".session":
            session, username, user_id = asyncio.run(_export_from_file(settings, src))
            _save(settings, session, username, user_id)
            return
        text = src.read_text(encoding="utf-8").strip()
        if text.startswith("{"):
            data = json.loads(text)
            session = _session_from_json(data) if isinstance(data, dict) else ""
        else:
            session = text.splitlines()[0].strip()
        if not session:
            raise SystemExit("В файле нет session-строки")
        settings.patch("bank_session", session)
        print(f"patched {settings.path} [bank] session")
        return
    session, username, user_id = asyncio.run(_login_user(settings))
    _save(settings, session, username, user_id)


if __name__ == "__main__":
    main()
