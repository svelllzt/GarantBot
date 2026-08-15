from typing import Any

RU = {
    "choose_lang": "Выберите язык / Choose language",
    "welcome": "Добро пожаловать, {name}.\nГарант удерживает оплату до подтверждения сделки.",
    "banned": "Аккаунт заблокирован.",
    "need_username": "Укажите username в настройках Telegram, без него сделки недоступны.",
    "menu": "Главное меню",
    "btn_profile": "Профиль",
    "btn_deal": "Сделка",
    "btn_inventory": "Инвентарь",
    "btn_history": "История",
    "btn_about": "О сервисе",
    "btn_menu": "Меню",
    "lang_ru": "Русский",
    "lang_en": "English",
    "btn_cancel": "Отмена",
    "btn_back": "Назад",
    "btn_yes": "Да",
    "btn_no": "Нет",
    "cancelled": "Отменено.",
    "error": "Не получилось. Попробуйте ещё раз.",
    "profile": (
        "<b>Профиль</b>\n\n"
        "ID: <code>{id}</code>\n"
        "Username: @{username}\n"
        "Сделок: {deals}\n"
        "Баланс: <b>{balance} {currency}</b>\n\n"
        "Карта: {card}\n"
        "Телефон: {phone}\n"
        "Банк: {bank}\n"
        "TON: {ton}"
    ),
    "not_set": "не указан",
    "btn_req": "Реквизиты",
    "req_menu": "Реквизиты для вывода. Их видите только вы и администратор.",
    "req_card": "Карта",
    "req_phone": "Телефон и банк",
    "req_ton": "TON-адрес",
    "req_ask_card": "Номер карты, только цифры.",
    "req_ask_phone": "Номер телефона, например +79991234567.",
    "req_ask_bank": "Название банка.",
    "req_ask_ton": "TON-адрес (UQ… / EQ…).",
    "req_saved": "Реквизиты сохранены.",
    "req_bad": "Неверный формат.",
    "lang_changed": "Язык обновлён.",
    "deposit": "Пополнение",
    "withdraw": "Вывод",
    "change_lang": "Язык",
    "deposit_ask": "Сумма пополнения в {currency}. Минимум {min}.",
    "deposit_created": (
        "Заявка #{id}\n"
        "Сумма: <b>{amount} {currency}</b>\n"
        "Комментарий: <code>{comment}</code>\n\n"
        "{extra}\n"
        "После перевода нажмите «Проверить» или дождитесь подтверждения администратора."
    ),
    "deposit_ton": "Переведите на TON-адрес:\n<code>{address}</code>\nВ комментарии укажите код выше.",
    "deposit_manual": "Перевод подтверждает администратор. Напишите @{support}, если платёж уже ушёл.",
    "deposit_check": "Проверить",
    "deposit_wait": "Платёж ещё не найден.",
    "deposit_ok": "Баланс пополнен на {amount} {currency}.",
    "withdraw_ask": "Сумма вывода в {currency}. Минимум {min}. Комиссия сервиса на вывод не берётся.",
    "withdraw_method": "Куда вывести?",
    "withdraw_no_req": "Сначала заполните реквизиты в профиле.",
    "withdraw_ok": "Заявка на вывод #{id}: {amount} {currency} на {details}. Администратор обработает её вручную.",
    "withdraw_low": "Недостаточно средств.",
    "min_amount": "Минимум {min} {currency}.",
    "about": (
        "Гарант для безопасных сделок.\n\n"
        "Покупатель переводит сумму на баланс бота. Продавец передаёт товар "
        "(обычный или NFT из инвентаря). Деньги уходят продавцу после подтверждения.\n\n"
        "Комиссия: {commission}% с суммы сделки, удерживается с продавца.\n"
        "Поддержка: @{support}\n"
        "{chat}"
    ),
    "deal_role": "Кем вы будете в сделке?",
    "deal_buyer": "Покупатель",
    "deal_seller": "Продавец",
    "deal_ask_user": "Username второй стороны, без @.",
    "deal_self": "С самим собой сделку открыть нельзя.",
    "deal_missing": "Пользователь не запускал бота.",
    "deal_busy_you": "У вас уже есть активная сделка #{id}.",
    "deal_busy_them": "У этого пользователя уже есть активная сделка.",
    "deal_preview": (
        "Контрагент:\n"
        "ID <code>{id}</code>\n"
        "@{username}\n"
        "Сделок: {deals}\n"
        "Роль: {role}"
    ),
    "deal_send": "Отправить предложение",
    "deal_reviews": "Отзывы",
    "deal_sent": "Предложение отправлено. Ждём ответа.",
    "deal_offer_in": (
        "Предложение сделки #{id}\n"
        "От @{username} (ID <code>{uid}</code>)\n"
        "Сделок у него: {deals}\n"
        "Вы: {role}"
    ),
    "deal_accept": "Принять",
    "deal_decline": "Отклонить",
    "deal_declined": "Предложение отклонено.",
    "deal_declined_peer": "Вторая сторона отклонила предложение.",
    "deal_opened": (
        "Сделка #{id}\n"
        "Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "Сумма: {amount}\n"
        "NFT: {nft}\n"
        "Условия: {desc}\n"
        "Статус: {status}"
    ),
    "deal_status_pending": "ожидает принятия",
    "deal_status_open": "открыта",
    "deal_status_paid": "оплачена",
    "deal_status_dispute": "спор",
    "deal_status_review": "завершена, отзыв",
    "deal_status_closed": "закрыта",
    "deal_status_cancelled": "отменена",
    "deal_set_price": "Указать сумму",
    "deal_set_nft": "Прикрепить NFT",
    "deal_set_desc": "Условия",
    "deal_pay": "Оплатить",
    "deal_confirm": "Товар получен",
    "deal_dispute": "Спор",
    "deal_cancel": "Отменить",
    "deal_ask_price": "Сумма сделки в {currency}.",
    "deal_price_set": "Сумма установлена: {amount} {currency}.",
    "deal_price_locked": "Сумму уже нельзя менять.",
    "deal_ask_desc": "Кратко опишите товар и условия передачи.",
    "deal_desc_set": "Условия сохранены.",
    "deal_nft_pick": "Выберите NFT из инвентаря. Он будет заморожен до конца сделки.",
    "deal_nft_empty": "В инвентаре нет свободных NFT.",
    "deal_nft_set": "NFT прикреплён: {title}.",
    "deal_nft_none": "не прикреплён",
    "deal_pay_no_amount": "Продавец ещё не указал сумму.",
    "deal_pay_low": "Недостаточно средств. Нужно {need} {currency}, на балансе {have}.",
    "deal_paid": "Оплата прошла. Продавец передаёт товар.",
    "deal_paid_seller": "Покупатель оплатил сделку #{id}. Передайте товар.",
    "deal_nft_sent": "NFT отправлен покупателю через банковский аккаунт.",
    "deal_nft_fail": "Не удалось отправить NFT. Откройте спор, администратор разберёт вручную.",
    "deal_confirm_ask": "Подтверждаете получение и валидность товара?",
    "deal_done_buyer": "Сделка закрыта. Можете оставить отзыв продавцу.",
    "deal_done_seller": "Сделка закрыта. На баланс зачислено {amount} {currency} (комиссия {commission}%).",
    "deal_review_ask": "Напишите отзыв или нажмите «Пропустить».",
    "deal_review_skip": "Пропустить",
    "deal_review_saved": "Отзыв сохранён.",
    "deal_review_empty": "Отзывов нет.",
    "deal_cancel_ask": "Отменить сделку?",
    "deal_cancel_sent": "Запрос на отмену отправлен второй стороне.",
    "deal_cancel_ok": "Сделка отменена.",
    "deal_cancel_denied": "В этой стадии отмена только через спор.",
    "deal_agree": "Согласиться",
    "deal_refuse": "Отказаться",
    "deal_dispute_ok": "Спор открыт. Администратор получил уведомление.",
    "deal_dispute_admin": (
        "Спор по сделке #{id}\n"
        "Покупатель: @{buyer} (<code>{buyer_id}</code>)\n"
        "Продавец: @{seller} (<code>{seller_id}</code>)\n"
        "Сумма: {amount} {currency}\n"
        "NFT: {nft}"
    ),
    "no_reviews": "Отзывов пока нет.",
    "history_empty": "Пусто.",
    "history_role": "Показать сделки, где вы…",
    "history_line": "#{id} · {role} · {amount} · {status}\nКонтрагент: @{peer}",
    "inv_empty": "Инвентарь пуст.",
    "inv_how": (
        "Отправьте NFT-подарок на аккаунт банка: {bank}\n"
        "Подарок появится здесь автоматически и привяжется к вашему Telegram ID."
    ),
    "inv_item": "{title}\nСтатус: {status}\nID: {id}",
    "inv_status_available": "доступен",
    "inv_status_locked": "в сделке",
    "inv_status_transferred": "передан",
    "inv_new": "В инвентарь добавлен подарок: {title}",
    "admin_only": "Нет доступа.",
    "admin_menu": "Админка",
    "admin_stats": "Статистика",
    "admin_ban": "Бан",
    "admin_unban": "Разбан",
    "admin_balance": "Баланс",
    "admin_mail": "Рассылка",
    "admin_buttons": "Кнопки",
    "admin_btn_pick": "Выберите кнопку.",
    "admin_btn_card": (
        "<b>{title}</b>\n<code>{key}</code>\n\n"
        "RU: {ru}\nEN: {en}\n"
        "Цвет: {style}\nЭмодзи: {emoji}\n\n"
        "Цвет и премиум-эмодзи видны, если у владельца бота есть Telegram Premium "
        "или у бота куплен username на Fragment."
    ),
    "admin_btn_name": "Название",
    "admin_btn_color": "Цвет",
    "admin_btn_emoji": "Эмодзи",
    "admin_btn_reset": "Сбросить",
    "admin_btn_ask_ru": "Русское название кнопки.",
    "admin_btn_ask_en": "English label. «-» копирует русское.",
    "admin_btn_ask_emoji": "Пришлите премиум-эмодзи или numeric id. «-» снимает иконку.",
    "admin_btn_style_primary": "Синий",
    "admin_btn_style_success": "Зелёный",
    "admin_btn_style_danger": "Красный",
    "admin_btn_style_none": "Без цвета",
    "admin_btn_saved": "Кнопка обновлена.",
    "admin_btn_no_emoji": "не задан",
    "admin_disputes": "Споры",
    "admin_deposits": "Пополнения",
    "admin_withdraws": "Выводы",
    "admin_stats_text": "Пользователей: {users}\nЗакрытых сделок: {deals}\nОборот: {volume} {currency}",
    "admin_ask_id": "Telegram ID пользователя.",
    "admin_ask_balance": "Новый баланс в {currency}.",
    "admin_ask_mail": "Текст рассылки. HTML можно.",
    "admin_done": "Готово.",
    "admin_user_missing": "Пользователь не найден.",
    "admin_no_disputes": "Открытых споров нет.",
    "admin_buyer": "Покупатель прав",
    "admin_seller": "Продавец прав",
    "admin_verdict_buyer": "Вердикт: деньги возвращены покупателю.",
    "admin_verdict_seller": "Вердикт: деньги переведены продавцу.",
    "admin_empty_list": "Заявок нет.",
    "admin_dep_line": "#{id} · {amount} {currency} · {comment}\nID {user}",
    "admin_wd_line": "#{id} · {amount} {currency} · {method}\n{details}\nID {user}",
    "admin_confirm": "Подтвердить",
    "admin_reject": "Отклонить",
    "admin_dep_ok": "Пополнение подтверждено.",
    "admin_dep_no": "Пополнение отклонено.",
    "admin_wd_ok": "Вывод отмечен как выплаченный.",
    "admin_wd_no": "Вывод отклонён, сумма возвращена на баланс.",
    "mail_started": "Рассылка пошла.",
    "mail_done": "Рассылка закончена: {ok} доставлено, {fail} ошибок.",
    "active_deal_btn": "К сделке #{id}",
}

EN = {
    "choose_lang": "Choose language / Выберите язык",
    "welcome": "Welcome, {name}.\nThe escrow holds payment until the deal is confirmed.",
    "banned": "This account is banned.",
    "need_username": "Set a Telegram username first. Deals are unavailable without it.",
    "menu": "Main menu",
    "btn_profile": "Profile",
    "btn_deal": "Deal",
    "btn_inventory": "Inventory",
    "btn_history": "History",
    "btn_about": "About",
    "btn_menu": "Menu",
    "lang_ru": "Русский",
    "lang_en": "English",
    "btn_cancel": "Cancel",
    "btn_back": "Back",
    "btn_yes": "Yes",
    "btn_no": "No",
    "cancelled": "Cancelled.",
    "error": "Something went wrong. Try again.",
    "profile": (
        "<b>Profile</b>\n\n"
        "ID: <code>{id}</code>\n"
        "Username: @{username}\n"
        "Deals: {deals}\n"
        "Balance: <b>{balance} {currency}</b>\n\n"
        "Card: {card}\n"
        "Phone: {phone}\n"
        "Bank: {bank}\n"
        "TON: {ton}"
    ),
    "not_set": "not set",
    "btn_req": "Payout details",
    "req_menu": "Payout details. Visible only to you and the admin.",
    "req_card": "Card",
    "req_phone": "Phone and bank",
    "req_ton": "TON address",
    "req_ask_card": "Card number, digits only.",
    "req_ask_phone": "Phone number, e.g. +19995550100.",
    "req_ask_bank": "Bank name.",
    "req_ask_ton": "TON address (UQ… / EQ…).",
    "req_saved": "Details saved.",
    "req_bad": "Invalid format.",
    "lang_changed": "Language updated.",
    "deposit": "Deposit",
    "withdraw": "Withdraw",
    "change_lang": "Language",
    "deposit_ask": "Deposit amount in {currency}. Minimum {min}.",
    "deposit_created": (
        "Request #{id}\n"
        "Amount: <b>{amount} {currency}</b>\n"
        "Memo: <code>{comment}</code>\n\n"
        "{extra}\n"
        "After sending, tap Check or wait for an admin confirmation."
    ),
    "deposit_ton": "Send TON to:\n<code>{address}</code>\nUse the memo above as the comment.",
    "deposit_manual": "An admin confirms the transfer. Message @{support} if it is already sent.",
    "deposit_check": "Check",
    "deposit_wait": "Payment not found yet.",
    "deposit_ok": "Balance credited with {amount} {currency}.",
    "withdraw_ask": "Withdrawal amount in {currency}. Minimum {min}. No extra fee on payout.",
    "withdraw_method": "Where should we send it?",
    "withdraw_no_req": "Fill in payout details in your profile first.",
    "withdraw_ok": "Withdrawal #{id}: {amount} {currency} to {details}. An admin will process it.",
    "withdraw_low": "Insufficient balance.",
    "min_amount": "Minimum {min} {currency}.",
    "about": (
        "Escrow for peer-to-peer deals.\n\n"
        "The buyer funds the bot balance. The seller delivers the item "
        "(regular goods or an NFT from inventory). Funds are released after confirmation.\n\n"
        "Fee: {commission}% of the deal, taken from the seller.\n"
        "Support: @{support}\n"
        "{chat}"
    ),
    "deal_role": "Your role in this deal?",
    "deal_buyer": "Buyer",
    "deal_seller": "Seller",
    "deal_ask_user": "Counterparty username, without @.",
    "deal_self": "You cannot open a deal with yourself.",
    "deal_missing": "This user has never started the bot.",
    "deal_busy_you": "You already have an active deal #{id}.",
    "deal_busy_them": "That user already has an active deal.",
    "deal_preview": (
        "Counterparty:\n"
        "ID <code>{id}</code>\n"
        "@{username}\n"
        "Deals: {deals}\n"
        "Your role: {role}"
    ),
    "deal_send": "Send offer",
    "deal_reviews": "Reviews",
    "deal_sent": "Offer sent. Waiting for a reply.",
    "deal_offer_in": (
        "Deal offer #{id}\n"
        "From @{username} (ID <code>{uid}</code>)\n"
        "Their deals: {deals}\n"
        "You are: {role}"
    ),
    "deal_accept": "Accept",
    "deal_decline": "Decline",
    "deal_declined": "Offer declined.",
    "deal_declined_peer": "The other party declined the offer.",
    "deal_opened": (
        "Deal #{id}\n"
        "Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "Seller: @{seller} (<code>{seller_id}</code>)\n"
        "Amount: {amount}\n"
        "NFT: {nft}\n"
        "Terms: {desc}\n"
        "Status: {status}"
    ),
    "deal_status_pending": "waiting",
    "deal_status_open": "open",
    "deal_status_paid": "paid",
    "deal_status_dispute": "dispute",
    "deal_status_review": "completed, review",
    "deal_status_closed": "closed",
    "deal_status_cancelled": "cancelled",
    "deal_set_price": "Set amount",
    "deal_set_nft": "Attach NFT",
    "deal_set_desc": "Terms",
    "deal_pay": "Pay",
    "deal_confirm": "Item received",
    "deal_dispute": "Dispute",
    "deal_cancel": "Cancel",
    "deal_ask_price": "Deal amount in {currency}.",
    "deal_price_set": "Amount set: {amount} {currency}.",
    "deal_price_locked": "The amount can no longer be changed.",
    "deal_ask_desc": "Describe the item and how it will be delivered.",
    "deal_desc_set": "Terms saved.",
    "deal_nft_pick": "Pick an NFT from inventory. It will be locked until the deal ends.",
    "deal_nft_empty": "No free NFTs in inventory.",
    "deal_nft_set": "NFT attached: {title}.",
    "deal_nft_none": "not attached",
    "deal_pay_no_amount": "The seller has not set the amount yet.",
    "deal_pay_low": "Not enough funds. Need {need} {currency}, have {have}.",
    "deal_paid": "Payment received. The seller should deliver now.",
    "deal_paid_seller": "The buyer paid deal #{id}. Deliver the item.",
    "deal_nft_sent": "NFT sent to the buyer via the bank account.",
    "deal_nft_fail": "NFT transfer failed. Open a dispute so an admin can handle it.",
    "deal_confirm_ask": "Confirm that you received a valid item?",
    "deal_done_buyer": "Deal closed. You can leave a review for the seller.",
    "deal_done_seller": "Deal closed. Credited {amount} {currency} (fee {commission}%).",
    "deal_review_ask": "Write a review or tap Skip.",
    "deal_review_skip": "Skip",
    "deal_review_saved": "Review saved.",
    "deal_review_empty": "No reviews.",
    "deal_cancel_ask": "Cancel this deal?",
    "deal_cancel_sent": "Cancel request sent to the other party.",
    "deal_cancel_ok": "Deal cancelled.",
    "deal_cancel_denied": "At this stage cancellation goes through a dispute.",
    "deal_agree": "Agree",
    "deal_refuse": "Refuse",
    "deal_dispute_ok": "Dispute opened. An admin has been notified.",
    "deal_dispute_admin": (
        "Dispute on deal #{id}\n"
        "Buyer: @{buyer} (<code>{buyer_id}</code>)\n"
        "Seller: @{seller} (<code>{seller_id}</code>)\n"
        "Amount: {amount} {currency}\n"
        "NFT: {nft}"
    ),
    "no_reviews": "No reviews yet.",
    "history_empty": "Nothing here.",
    "history_role": "Show deals where you were the…",
    "history_line": "#{id} · {role} · {amount} · {status}\nPeer: @{peer}",
    "inv_empty": "Inventory is empty.",
    "inv_how": (
        "Send an NFT gift to the bank account: {bank}\n"
        "It will show up here and bind to your Telegram ID."
    ),
    "inv_item": "{title}\nStatus: {status}\nID: {id}",
    "inv_status_available": "available",
    "inv_status_locked": "in a deal",
    "inv_status_transferred": "transferred",
    "inv_new": "Gift added to inventory: {title}",
    "admin_only": "No access.",
    "admin_menu": "Admin",
    "admin_stats": "Stats",
    "admin_ban": "Ban",
    "admin_unban": "Unban",
    "admin_balance": "Balance",
    "admin_mail": "Broadcast",
    "admin_buttons": "Buttons",
    "admin_btn_pick": "Pick a button.",
    "admin_btn_card": (
        "<b>{title}</b>\n<code>{key}</code>\n\n"
        "RU: {ru}\nEN: {en}\n"
        "Color: {style}\nEmoji: {emoji}\n\n"
        "Color and premium emoji show up if the bot owner has Telegram Premium "
        "or the bot bought a username on Fragment."
    ),
    "admin_btn_name": "Label",
    "admin_btn_color": "Color",
    "admin_btn_emoji": "Emoji",
    "admin_btn_reset": "Reset",
    "admin_btn_ask_ru": "Russian button label.",
    "admin_btn_ask_en": "English label. Send - to copy the Russian one.",
    "admin_btn_ask_emoji": "Send a premium emoji or its numeric id. - removes the icon.",
    "admin_btn_style_primary": "Blue",
    "admin_btn_style_success": "Green",
    "admin_btn_style_danger": "Red",
    "admin_btn_style_none": "No color",
    "admin_btn_saved": "Button updated.",
    "admin_btn_no_emoji": "not set",
    "admin_disputes": "Disputes",
    "admin_deposits": "Deposits",
    "admin_withdraws": "Withdrawals",
    "admin_stats_text": "Users: {users}\nClosed deals: {deals}\nVolume: {volume} {currency}",
    "admin_ask_id": "User Telegram ID.",
    "admin_ask_balance": "New balance in {currency}.",
    "admin_ask_mail": "Broadcast text. HTML is fine.",
    "admin_done": "Done.",
    "admin_user_missing": "User not found.",
    "admin_no_disputes": "No open disputes.",
    "admin_buyer": "Buyer wins",
    "admin_seller": "Seller wins",
    "admin_verdict_buyer": "Verdict: funds returned to the buyer.",
    "admin_verdict_seller": "Verdict: funds released to the seller.",
    "admin_empty_list": "No requests.",
    "admin_dep_line": "#{id} · {amount} {currency} · {comment}\nID {user}",
    "admin_wd_line": "#{id} · {amount} {currency} · {method}\n{details}\nID {user}",
    "admin_confirm": "Confirm",
    "admin_reject": "Reject",
    "admin_dep_ok": "Deposit confirmed.",
    "admin_dep_no": "Deposit rejected.",
    "admin_wd_ok": "Withdrawal marked as paid.",
    "admin_wd_no": "Withdrawal rejected, funds returned.",
    "mail_started": "Broadcast started.",
    "mail_done": "Broadcast finished: {ok} delivered, {fail} failed.",
    "active_deal_btn": "Open deal #{id}",
}

LOCALES = {"ru": RU, "en": EN}


def t(lang: str, key: str, **kwargs: Any) -> str:
    table = LOCALES.get(lang) or RU
    text = table.get(key) or RU.get(key) or key
    if kwargs:
        return text.format(**kwargs)
    return text
