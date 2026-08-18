# Phantom OTC

Escrow-бот **Phantom OTC** на aiogram 3. Банковский аккаунт для NFT-подарков — pyrogram (pyrofork).

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.ini.example config.ini
```

Нужен **pyrofork**, не пакет `pyrogram`. Если стоит обычный pyrogram, логин банка падает на Python 3.12+ (`There is no current event loop`). Исправление:

```bash
pip uninstall -y pyrogram
pip install -U "pyrofork>=2.3.45"
```

Удобнее Python 3.11–3.13. На 3.14 тоже должно работать с pyrofork.

В `config.ini` заполните `[bot] token` и `admin_ids`. Если рядом лежит старый `.env`, при первом запуске он сам превратится в `config.ini`.

```bash
python main.py
```

`/admin` открывает панель только для ID из `[bot] admin_ids`.

Все кнопки инлайн. В админке → «Кнопки» можно сменить название (RU/EN), цвет (`primary` синий, `success` зелёный, `danger` красный) и премиум-эмодзи. Цвет и эмодзи клиент рисует, если у владельца бота Telegram Premium или у бота куплен username на Fragment. Иконку задают, отправив кастомный эмодзи в чат.

## Банковский аккаунт (NFT)

Это **отдельный юзер-аккаунт** (не токен гарант-бота). На него шлют NFT-подарки.

Куда пишется сессия: `config.ini` → `[bank]` → `session`. Pyrogram патчить не нужно.

**Первый вход по телефону** — запустите бота в консоли:

```bash
python main.py
```

Если `[bank] session` пустой, бот сам спросит `api_id` / `api_hash` (https://my.telegram.org), затем телефон и код из Telegram/SMS. После этого session попадёт в ini, бот продолжит работу.

**Без телефона** новая юзер-сессия не создаётся — так устроен Telegram. Варианты:

1. Уже есть selfbot на Pyrogram/pyrofork — скопируйте строку session в `[bank] session`, плюс `api_id` / `api_hash`.
2. Импорт из файла/папки:

```bash
python scripts/login_bank.py --from C:\Users\...\selfbot\config\config.json
python scripts/login_bank.py --from C:\Users\...\selfbot\xxx.session
python scripts/login_bank.py
```

Без аргументов скрипт печатает, куда писать сессию. `login_bank.py --user` больше не логинит — вход в `python main.py`.

Telethon-сессия сюда не подойдёт, только Pyrogram/pyrofork.

Без `[bank] session` гарант работает, инвентарь NFT сам не наполняется. Если бот запущен не из консоли (нет TTY), первый вход пропускается.

`tgcrypto` ставить не обязательно: без него pyrogram чуть медленнее, на логике это не сказывается.

Передача уникального подарка списывает Telegram Stars с банковского аккаунта (обычно 25★). В `/admin` → Статистика видно текущий баланс, сколько передач ещё хватит и сколько NFT ждут отправки. Если Stars мало, бот докупает **100★ за TON** через Fragment на username банка (отдельный кошелёк в `[fragment]`, не эскроу `[ton] mnemonic`). Если автопокупка не сработала — админам приходит алерт. После появления Stars бот сам дошлёт зависшие подарки.

В `config.ini` `[bank]`:

```
transfer_stars = 25
min_stars = 50
```

## Fragment — автопокупка Stars

Библиотека `fragment-api-py`. Кошелёк **только для Stars**, не путать с TON-эскроу.

```
[fragment]
mnemonic =
api_key =
cookies =
wallet = V4R2
stars = 100
provider = toncenter
```

- `mnemonic` — seed кошелька, с которого платят TON за Stars (12/18/24 слова).
- `api_key` — tonconsole.com (`provider = tonapi`) или toncenter. Пустой ключ берётся из `[ton] api_key`.
- `cookies` — сессия Fragment: JSON или `stel_ssid=...; stel_dt=...; stel_token=...; stel_ton_token=...`.
- Если `mnemonic` задан, cookies пустые и бот запущен в консоли — `python main.py` сам логинит Fragment (телефон или QR) и запишет cookies в ini.
- Получатель пакета — `[bank] username`. Покупка: 100★, `payment_method=ton`.

Без `[fragment] mnemonic` автопокупка выключена, NFT-гарант работает как раньше.

## База пользователей

SQLite `data/garant.db`, таблица `users`. Создаётся при старте (`Storage.connect`):

- `user_id` — Telegram ID
- `nick` — ник (имя из Telegram)
- `username`
- `deals_count` — сколько сделок закрыто
- реквизиты: `card`, `phone`, `bank_name`, `ton_address`
- `balance`, `lang` (выбор языка запоминается), `banned`

Профиль показывает эти поля. Старая база подтягивает новые колонки сама.

## Меню

Главный экран: **Начать сделку**, **F.A.Q**, **Профиль**, **Поддержка**.

Сделка начинается с категории: аккаунты, крипта, NFT-подарки, товар, другое. Дальше — напрямую с человеком или объявление в канал.

F.A.Q и картинки экранов задаёт админ в `/admin`.

## Сделка

Категории: NFT-подарки, аккаунты (Roblox, Steam, Epic, Discord, Telegram, соцсети, игры), товар, TON → рубли, другое.

При открытии сделки обоим приходит **памятка** по категории. Для Roblox — как сменить почту/2FA/PIN, чтобы аккаунт не вернули.

Можно открыть с человеком по username или **выложить в канал**. В `config.ini`:

```
[bot]
deals_channel = @your_deals_channel
```

Бот должен быть админом канала с правом писать. В посте кнопка «Открыть в боте» (`/start d123`). Покупатель пополняет баланс и открывает сделку.

**Оплата с баланса.** Комиссия `[bot] commission_percent` с продавца.

**TON → рубли** только напрямую, не в канал. Продавец кладёт TON на V4, покупатель шлёт рубли, после подтверждения бот отправляет TON.

**Спор:** причина и доказательства (текст/фото), переписка сторон и админа, вердикт в пользу покупателя или продавца.

## Картинки меню

Админка → «Картинки меню»: пришлите фото на экран (menu, profile, deal, faq…). Либо файлы в `assets/` — см. `assets/README.txt`. Фото из бота важнее файла на диске.

## Пополнение

Если задан `[ton] address`, пользователь получает memo и жмёт «Проверить» — сверка идёт через toncenter. `rate` переводит TON в валюту бота. Админ может подтвердить заявку вручную.

## Старый USA GARANT

Лежит как образец. В нём был скрытый слив токена на чужой чат — в этот код это не переносилось. Токены из `config.py` лучше сразу отозвать.
