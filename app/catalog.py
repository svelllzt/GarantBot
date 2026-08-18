from __future__ import annotations

from app.storage import KIND_GOODS, KIND_TON_RUB

CATS = (
    "nft",
    "acc_rbx",
    "acc_stm",
    "acc_epic",
    "acc_dsc",
    "acc_tg",
    "acc_soc",
    "acc_game",
    "goods",
    "ton",
    "other",
)

_LABEL = {
    "nft": {"ru": "🎁 NFT-подарок Telegram", "en": "🎁 Telegram NFT gift"},
    "acc_rbx": {"ru": "🎮 Аккаунт Roblox", "en": "🎮 Roblox account"},
    "acc_stm": {"ru": "🎯 Аккаунт Steam", "en": "🎯 Steam account"},
    "acc_epic": {"ru": "🟣 Аккаунт Epic Games", "en": "🟣 Epic Games account"},
    "acc_dsc": {"ru": "💬 Аккаунт Discord", "en": "💬 Discord account"},
    "acc_tg": {"ru": "✈️ Аккаунт Telegram", "en": "✈️ Telegram account"},
    "acc_soc": {"ru": "📱 Соцсеть / почта", "en": "📱 Social / email account"},
    "acc_game": {"ru": "🕹️ Игровой аккаунт", "en": "🕹️ Game account"},
    "goods": {"ru": "📦 Товар / услуга", "en": "📦 Goods / service"},
    "ton": {"ru": "💎 TON → рубли", "en": "💎 TON → RUB"},
    "other": {"ru": "✨ Другое", "en": "✨ Other"},
}

_MANUAL = {
    "nft": {
        "ru": (
            "<b>Памятка · NFT-подарок</b>\n\n"
            "1. Продавец сначала отправляет уникальный подарок на банковский аккаунт бота. Без NFT в инвентаре сделку создать нельзя.\n"
            "2. Цена в рублях. Оплата идёт по реквизитам продавца, не с баланса бота.\n"
            "3. Покупатель переводит деньги и присылает чек строго файлом PDF. Другие форматы не принимаются.\n"
            "4. Чек уходит продавцу. Если он подтвердил, что деньги пришли, бот сам переводит NFT покупателю (на банке должны быть Stars, обычно 25★).\n"
            "5. Не подтверждайте ничего, пока подарок не появился у вас в Telegram. Если Stars не хватило — бот дошлёт сам после пополнения, иначе спор."
        ),
        "en": (
            "<b>Memo · NFT gift</b>\n\n"
            "1. The seller must send the unique gift to the bot bank account first. No deal without that NFT in inventory.\n"
            "2. The price is in rubles. The buyer pays the seller’s details, not the bot balance.\n"
            "3. The buyer then uploads a PDF receipt only. Photos and other files are rejected.\n"
            "4. The seller checks the PDF. After they confirm the money arrived, the bot transfers the NFT (the bank account needs Stars, usually 25★).\n"
            "5. Do not confirm until the gift is in your Telegram. If Stars run out, the bot will send it after a top-up. Otherwise open a dispute."
        ),
    },
    "acc_rbx": {
        "ru": (
            "<b>Памятка · Roblox</b>\n\n"
            "Чтобы аккаунт не вернули через recovery (не «реснули»):\n\n"
            "1. Зайдите с нового устройства / инкогнито. Не светите свой основной аккаунт.\n"
            "2. Сразу смените пароль. Старый никому не отправляйте в чат сделки.\n"
            "3. Смените email на свой. Подтвердите новый ящик. Старую почту отвяжите.\n"
            "4. Снимите PIN / Parental PIN, если висит. Иначе продавец заберёт аккаунт обратно.\n"
            "5. Отключите старый 2FA и включите свой Authenticator на новый номер/почту.\n"
            "6. Проверьте Billing, подписки, связанные соцсети (Google/Microsoft) — отвяжите.\n"
            "7. Выйдите со всех сессий (Sign out of all sessions), затем зайдите только вы.\n"
            "8. Не подтверждайте сделку, пока почта, пароль и 2FA полностью ваши.\n"
            "9. Если продавец тянет с отвязкой почты — спор, не «товар получен»."
        ),
        "en": (
            "<b>Memo · Roblox</b>\n\n"
            "To stop the seller recovering the account:\n\n"
            "1. Log in from a fresh browser/device.\n"
            "2. Change the password immediately. Never paste the old one in the deal chat.\n"
            "3. Change the email to yours and verify it. Unlink the old mailbox.\n"
            "4. Remove PIN / Parental PIN if it is set.\n"
            "5. Replace 2FA with your own authenticator.\n"
            "6. Unlink Google/Microsoft and check billing.\n"
            "7. Sign out of all sessions, then log in only from your side.\n"
            "8. Do not confirm the deal until email, password and 2FA are yours.\n"
            "9. If the seller stalls on unlinking — open a dispute."
        ),
    },
    "acc_stm": {
        "ru": (
            "<b>Памятка · Steam</b>\n\n"
            "1. Смените пароль и почту аккаунта. Подтвердите новую почту.\n"
            "2. Снимите старый Guard: отключите Steam Guard на старом телефоне, привяжите свой.\n"
            "3. Удалите резервные коды Guard у продавца — сгенерируйте новые себе.\n"
            "4. Проверьте кошелёк, карты, семейный просмотр, ограниченный аккаунт (limited).\n"
            "5. Смените секретный вопрос / телефон в поддержке, если был.\n"
            "6. Выйдите из всех сессий. Не подтверждайте, пока Guard только на вашем телефоне.\n"
            "7. VAC / trade ban смотрите до оплаты. После подтверждения возврата не будет."
        ),
        "en": (
            "<b>Memo · Steam</b>\n\n"
            "1. Change password and account email, then verify the new mailbox.\n"
            "2. Remove the old Steam Guard and attach yours.\n"
            "3. Regenerate Guard backup codes.\n"
            "4. Check wallet, cards, family view, limited status.\n"
            "5. Sign out everywhere. Confirm only when Guard is on your phone only."
        ),
    },
    "acc_epic": {
        "ru": (
            "<b>Памятка · Epic Games</b>\n\n"
            "1. Смените пароль и email, подтвердите ящик.\n"
            "2. Отвяжите PSN / Xbox / Nintendo / Facebook / Google, привяжите свои.\n"
            "3. Включите свой 2FA, старый выключите.\n"
            "4. Проверьте возвраты Fortnite и привязанные карты.\n"
            "5. Не подтверждайте, пока все внешние входы не ваши."
        ),
        "en": (
            "<b>Memo · Epic Games</b>\n\n"
            "1. Change password and email.\n"
            "2. Unlink PSN / Xbox / Nintendo / social logins, then add yours.\n"
            "3. Replace 2FA.\n"
            "4. Confirm only when every linked login is yours."
        ),
    },
    "acc_dsc": {
        "ru": (
            "<b>Памятка · Discord</b>\n\n"
            "1. Смените пароль и email, подтвердите почту.\n"
            "2. Отключите старый 2FA, включите свой. Сохраните свои backup-коды.\n"
            "3. Смотрите авторизованные приложения и сессии — сбросьте все.\n"
            "4. Нитро и платежи: уберите карты продавца.\n"
            "5. Не подтверждайте, пока 2FA и почта только ваши. Иначе аккаунт вернут через SMS."
        ),
        "en": (
            "<b>Memo · Discord</b>\n\n"
            "1. Change password and email.\n"
            "2. Replace 2FA and keep your own backup codes.\n"
            "3. Revoke sessions and authorized apps.\n"
            "4. Remove the seller's payment methods.\n"
            "5. Confirm only when 2FA and email are yours."
        ),
    },
    "acc_tg": {
        "ru": (
            "<b>Памятка · Telegram-аккаунт</b>\n\n"
            "1. Номер должен перейти вам: SIM / перенос номера, не «облачный» доступ продавца.\n"
            "2. Сразу поставьте облачный пароль 2FA (Settings → Privacy → Two-Step) на свой.\n"
            "3. Отключите старые сессии: Privacy → Active sessions → Terminate others.\n"
            "4. Смените username, если он был. Проверьте почту для входа.\n"
            "5. Пока облачный пароль знает продавец — он заберёт аккаунт. Не подтверждайте раньше."
        ),
        "en": (
            "<b>Memo · Telegram account</b>\n\n"
            "1. You must control the phone number, not a shared login.\n"
            "2. Set your own two-step cloud password immediately.\n"
            "3. Terminate every other session.\n"
            "4. Change the username. Confirm only when the seller cannot sign back in."
        ),
    },
    "acc_soc": {
        "ru": (
            "<b>Памятка · Соцсеть / почта</b>\n\n"
            "1. Смените пароль. Отвяжите старый телефон и почту, привяжите свои.\n"
            "2. Выключите старый 2FA, включите свой.\n"
            "3. Сбросьте сессии, приложения, резервные входы (Google / Apple / VK).\n"
            "4. Проверьте восстановление: контрольные вопросы, доверенные контакты.\n"
            "5. Не подтверждайте, пока вход возможен только с ваших данных."
        ),
        "en": (
            "<b>Memo · Social / email</b>\n\n"
            "1. Change the password. Replace phone and recovery email.\n"
            "2. Replace 2FA.\n"
            "3. Revoke sessions and third-party logins.\n"
            "4. Confirm only when recovery options are yours."
        ),
    },
    "acc_game": {
        "ru": (
            "<b>Памятка · Игровой аккаунт</b>\n\n"
            "1. Смените пароль, почту, телефон, секретный вопрос.\n"
            "2. Отвяжите старый 2FA / Guard / Authenticator, поставьте свой.\n"
            "3. Проверьте привязки магазинов (PlayStation, Xbox, Google Play).\n"
            "4. Выйдите со всех устройств. Не подтверждайте, пока продавец может зайти обратно.\n"
            "5. Баны и регион смотрите до оплаты."
        ),
        "en": (
            "<b>Memo · Game account</b>\n\n"
            "1. Change password, email, phone and security questions.\n"
            "2. Replace 2FA / authenticator.\n"
            "3. Unlink store accounts. Sign out everywhere.\n"
            "4. Confirm only when the seller cannot log in."
        ),
    },
    "goods": {
        "ru": (
            "<b>Памятка · Товар / услуга</b>\n\n"
            "1. Покупатель оплачивает с баланса бота. Деньги у гаранта до кнопки «Товар получен».\n"
            "2. Условия и способ передачи фиксируйте в сделке до оплаты.\n"
            "3. Не подтверждайте, пока товар у вас и вы его проверили.\n"
            "4. Если продавец пропал или товар не тот — спор.\n"
            "5. После подтверждения деньги уходят продавцу за вычетом комиссии. Откатить нельзя."
        ),
        "en": (
            "<b>Memo · Goods / service</b>\n\n"
            "1. The buyer pays from the bot balance. Funds stay in escrow until confirmation.\n"
            "2. Write delivery terms before paying.\n"
            "3. Do not confirm until you have checked the item.\n"
            "4. If something is wrong, open a dispute.\n"
            "5. After confirmation the seller is paid minus the fee. This cannot be undone."
        ),
    },
    "ton": {
        "ru": (
            "<b>Памятка · TON → рубли</b>\n\n"
            "1. Продавец кладёт TON на кошелёк V4 гаранта с комментарием из сделки.\n"
            "2. Покупатель переводит рубли по реквизитам продавца (карта / телефон).\n"
            "3. Продавец подтверждает, что рубли пришли — бот сам шлёт TON на ваш адрес.\n"
            "4. Покупатель заранее указывает TON-адрес получения.\n"
            "5. Если TON уже на гаранте, а рубли не дошли — спор. Не подтверждайте вслепую."
        ),
        "en": (
            "<b>Memo · TON → RUB</b>\n\n"
            "1. The seller deposits TON to the escrow V4 wallet with the deal memo.\n"
            "2. The buyer pays rubles to the seller's card/phone.\n"
            "3. When the seller confirms, the bot sends TON to the buyer address.\n"
            "4. The buyer must set a receive address first.\n"
            "5. If TON is locked and rubles did not arrive, open a dispute."
        ),
    },
    "other": {
        "ru": (
            "<b>Памятка · Сделка</b>\n\n"
            "1. Оплата через баланс бота. Гарант держит сумму до подтверждения.\n"
            "2. Опишите, что передаёте, и как проверите факт передачи.\n"
            "3. Не подтверждайте до проверки. Сомнения — спор.\n"
            "4. Комиссия снимается с продавца при закрытии."
        ),
        "en": (
            "<b>Memo · Deal</b>\n\n"
            "1. Pay via the bot balance. Escrow holds funds until confirmation.\n"
            "2. Write what is transferred and how you will verify it.\n"
            "3. Do not confirm early. Use a dispute if needed.\n"
            "4. The fee is taken from the seller on close."
        ),
    },
}


def known(category: str | None) -> bool:
    return (category or "") in _LABEL


def normalize(category: str | None) -> str:
    if category in _LABEL:
        return category
    return "goods"


def label(category: str | None, lang: str) -> str:
    row = _LABEL.get(normalize(category))
    return row.get(lang) or row["ru"]


_PAY_HINT = {
    "ru": (
        "Оплата: если у продавца заполнены реквизиты (карта или телефон и банк) — "
        "покупатель переводит туда и присылает чек PDF. Баланс бота в этом случае не нужен. "
        "Если реквизитов нет — оплата с баланса гаранта."
    ),
    "en": (
        "Payment: if the seller has payout details (card, or phone plus bank), the buyer pays "
        "those details and uploads a PDF receipt. The bot balance is not used then. "
        "If there are no details, pay from the escrow balance."
    ),
}


def manual(category: str | None, lang: str) -> str:
    row = _MANUAL.get(normalize(category)) or _MANUAL["other"]
    body = row.get(lang) or row["ru"]
    cat = normalize(category)
    if cat in {"nft", "ton"}:
        return body
    hint = _PAY_HINT.get(lang) or _PAY_HINT["ru"]
    return hint + "\n\n" + body


def payment_kind(category: str | None) -> str:
    if normalize(category) == "ton":
        return KIND_TON_RUB
    return KIND_GOODS


def needs_nft(category: str | None) -> bool:
    return normalize(category) == "nft"


def listing_allowed(category: str | None) -> bool:
    return normalize(category) != "ton"


GROUPS = (
    ("acc", ("acc_rbx", "acc_stm", "acc_epic", "acc_dsc", "acc_tg", "acc_soc", "acc_game")),
    ("crypto", ("ton",)),
    ("nft", ("nft",)),
    ("goods", ("goods",)),
    ("other", ("other",)),
)

_GROUP_LABEL = {
    "acc": {"ru": "🎮 Аккаунты", "en": "🎮 Accounts"},
    "crypto": {"ru": "💎 Крипта", "en": "💎 Crypto"},
    "nft": {"ru": "🎁 NFT-подарки", "en": "🎁 NFT gifts"},
    "goods": {"ru": "📦 Товар / услуга", "en": "📦 Goods / service"},
    "other": {"ru": "✨ Другое", "en": "✨ Other"},
}


def group_label(key: str, lang: str) -> str:
    row = _GROUP_LABEL.get(key) or _GROUP_LABEL["other"]
    return row.get(lang) or row["ru"]


def group_cats(key: str) -> tuple[str, ...]:
    for name, cats in GROUPS:
        if name == key:
            return cats
    return ()


def is_group(key: str | None) -> bool:
    return any(name == key for name, _ in GROUPS)
