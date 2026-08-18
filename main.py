

import telebot
import time
import requests
import sqlite3

# Инициализируем бота
TOKEN = 'TOKEN'
bot = telebot.TeleBot(TOKEN)


# ================= 🗄️ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ SQLite =================

def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    # Таблица 1: Реестр кредитных обязательств
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            debt_name TEXT,
            balance REAL,
            rate REAL,
            min_payment REAL
        )
    ''')
    # Таблица 2: Ежедневные расходы инвестора
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            amount REAL,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()


# Автоматически создаем базу данных при старте скрипта
init_db()

# ================= 🛡️ МОДУЛЬ АНТИФЛУДА (ЗАЩИТА ОТ СПАМА) =================

last_message_time = {}


def is_spam(chat_id):
    current_time = time.time()
    if chat_id not in last_message_time:
        last_message_time[chat_id] = current_time
        return False
    time_passed = current_time - last_message_time[chat_id]
    last_message_time[chat_id] = current_time
    if time_passed < 1.5:
        return True
    return False


# ================= 📈 СЕТЕВЫЕ ИНВЕСТ-МОДУЛИ (ММВБ / ЦБ) =================

def get_forex_rates():
    try:
        url = "https://cbr-xml-daily.ru"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            valute = response.json()["Valute"]
            usd_rub = valute["USD"]["Value"]
            eur_rub = valute["EUR"]["Value"]
            cny_rub = valute["CNY"]["Value"] / valute["CNY"]["Nominal"]
            byn_rub = valute["BYN"]["Value"]

            usd_byn = usd_rub / byn_rub if byn_rub else 0
            eur_byn = eur_rub / byn_rub if byn_rub else 0
            cny_byn = (cny_rub * 10) / byn_rub if byn_rub else 0

            return (
                "💵 **Официальные курсы валют Центробанка РФ:**\n\n"
                "📊 **К российскому рублю (RUB):**\n"
                f"🇺🇸 1 USD = {usd_rub:.2f} RUB\n"
                f"🇪🇺 1 EUR = {eur_rub:.2f} RUB\n"
                f"🇨🇳 10 CNY = {cny_rub * 10:.2f} RUB\n\n"
                "🇧🇾 **К белорусскому рублю (BYN):**\n"
                f"🇺🇸 1 USD = {usd_byn:.4f} BYN\n"
                f"🇪🇺 1 EUR = {eur_byn:.4f} BYN\n"
                f"🇨🇳 10 CNY = {cny_byn:.4f} BYN\n\n"
                "🏛 _Источник данных: Центральный Банк РФ_"
            )
    except Exception as e:
        print(f"Ошибка валют ЦБ: {e}")
    return "⚠️ Шлюз валютных котировок временно недоступен. Включите российский VPN."


def get_moex_stocks():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            rows = response.json()["securities"]["data"]
            target_tickers = {"SBER": "🍏 Сбербанк", "GAZP": "🔥 Газпром", "LKOH": "⛽️ Лукойл", "YNDX": "📱 Яндекс",
                              "NVTK": "❄️ Новатэк"}
            result_text = "📈 **Актуальные цены акций на Московской Бирже:**\n\n"
            found = False
            for row in rows:
                secid, price = row[0], row[1]
                if secid in target_tickers and price is not None:
                    found = True
                    result_text += f"{target_tickers[secid]} ({secid}) = **{price:.2f} RUB**\n"
            if found:
                result_text += "\n⚡️ _Котировки обновлены в реальном времени из MOEX._"
                return result_text
    except Exception as e:
        print(f"Ошибка акций MOEX: {e}")
    return "⚠️ Торговый сервер MOEX не отвечает. Включите российский VPN."


def get_moex_bonds():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            rows = response.json()["securities"]["data"]
            target_bonds = {"SU26238RMFS4": "🏛 ОФЗ 26238 (Долгосрочная)", "SU26244RMFS2": "🏛 ОФЗ 26244 (Среднесрочная)",
                            "SU26243RMFS4": "🏛 ОФЗ 26243 (Краткосрочная)"}
            result_text = "🎫 **Текущая доходность гособлигаций РФ (ОФЗ):**\n\n"
            found = False
            for row in rows:
                secid, price, bond_yield = row[0], row[1], row[2]
                if secid in target_bonds:
                    found = True
                    p_str = f"{price:.2f}%" if price is not None else "нет торгов"
                    y_str = f"{bond_yield:.2f}%" if bond_yield is not None else "нет данных"
                    result_text += f"**{target_bonds[secid]}**\n▪️ Цена: {p_str} от номинала\n▪️ Доходность: **{y_str}**\n\n"
            if found:
                result_text += "💡 _Доходность зафиксируется на весь срок, если держать ОФЗ до погашения._"
                return result_text
    except Exception as e:
        print(f"Ошибка облигаций MOEX: {e}")
    return "⚠️ Долговой рынок биржи недоступен. Включите российский VPN."


def get_moex_commodities():
    try:
        url_gold = "https://moex.com"
        url_brent = "https://moex.com"
        response_gold = requests.get(url_gold, timeout=5)
        response_brent = requests.get(url_brent, timeout=5)
        gold_price = None
        brent_price = None
        if response_gold.status_code == 200:
            data = response_gold.json()["marketdata"]["data"]
            if data: gold_price = data[0][1]
        if response_brent.status_code == 200:
            data = response_brent.json()["marketdata"]["data"]
            if data: brent_price = data[0][1]
        if gold_price or brent_price:
            text = "🏆 **Котировки сырьевых товаров (MOEX):**\n\n"
            if gold_price:
                gold_ounce = gold_price * 31.1035
                text += f"👑 **Золото (XAU):**\n▪️ 1 грамм = **{gold_price:.2f} RUB**\n▪️ 1 тройская унция = **{gold_ounce:.2f} RUB**\n\n"
            if brent_price:
                text += f"🛢 **Нефть Brent (OIL):**\n▪️ 1 баррель = **{brent_price:.2f} USD**\n\n"
            text += "⚡️ _Данные обновлены напрямую из торгового ядра MOEX._"
            return text
    except Exception as e:
        print(f"Ошибка товаров: {e}")
    return "⚠️ Сырьевой шлюз биржи недоступен. Включите российский VPN."


# ================= 🤖 ОБРАБОТЧИКИ КОМАНД (ХЕНДЛЕРЫ) =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spam(message.chat.id): return

    # Защищаем имя пользователя от ломаных символов
    user_name = message.from_user.first_name or "Инвестор"

    welcome_text = (
        f"🧠 <b>Инвестиционный Терминал & Финансовый Помощник Pro</b>\n\n"
        f"Приветствуем, {user_name}! Система персонального риск-менеджмента успешно развернута.\n\n"
        f"🖥️ <b>Интерактивная Web-Платформа:</b>\n"
        f"Для запуска симуляторов и профессиональных калькуляторов нажмите синюю кнопку Open в левом нижнем углу экрана.\n\n"
        f"📊 <b>Прямые команды серверной аналитики (MOEX / ЦБ):</b>\n"
        f"/rates — Курсы мировых валют к RUB и BYN\n"
        f"/stocks — Живые котировки акций на МосБирже\n"
        f"/bonds — Текущая доходность гособлигаций ОФЗ\n"
        f"/commodities — Цены на Золото и Нефть Brent\n\n"
        f"📉 <b>Учет ежедневных расходов прямо в чате:</b>\n"
        f"Просто напишите мне сообщение в формате: Категория Сумма\n"
        f"(Например: Еда 1200 или Бензин 3000), и я автоматически внесу транзакцию в учет ваших расходов.\n\n"
        f"🗒️ /report — Сформировать актуальный отчет по расходам\n"
        f"🗑️ /clear_expenses — Полностью очистить историю трат"
    )
    # Используем стабильный HTML-режим вместо Markdown
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")


@bot.message_handler(commands=['rates'])
def show_rates(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Подключаюсь к Банку России...")
    bot.send_message(message.chat.id, get_forex_rates(), parse_mode="Markdown")
    bot.delete_message(message.chat.id, waiting_msg.message_id)


@bot.message_handler(commands=['stocks'])
def show_stocks(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Опрашиваю торговую систему MOEX...")
    bot.send_message(message.chat.id, get_moex_stocks(), parse_mode="Markdown")
    bot.delete_message(message.chat.id, waiting_msg.message_id)


@bot.message_handler(commands=['bonds'])
def show_bonds(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Анализирую долговой рынок ММВБ...")
    bot.send_message(message.chat.id, get_moex_bonds(), parse_mode="Markdown")
    bot.delete_message(message.chat.id, waiting_msg.message_id)


@bot.message_handler(commands=['commodities'])
def show_commodities(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Запрашиваю цены металлов и сырья на MOEX...")
    bot.send_message(message.chat.id, get_moex_commodities(), parse_mode="Markdown")
    bot.delete_message(message.chat.id, waiting_msg.message_id)


# Команда генерации текстового отчета по расходам из базы данных
@bot.message_handler(commands=['report'])
def show_finance_report(message):
    if is_spam(message.chat.id): return
    try:
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM user_expenses WHERE user_id = ? GROUP BY category",
                       (message.chat.id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            bot.send_message(message.chat.id,
                             "📊 **Ваш финансовый отчет пуст.**\nВнесите первый расход, написав в чат, например: `Еда 500`",
                             parse_mode="Markdown")
            return

        report_text = "📊 **Ваш актуальный отчет по расходам:**\n\n"
        total_sum = 0
        for row in rows:
            report_text += f"▪️ {row[0]}: **{row[1]:.2f} руб.**\n"
            total_sum += row[1]

        report_text += f"\n🏆 **ИТОГО ПОТРАЧЕНО: {total_sum:.2f} руб.**"
        bot.send_message(message.chat.id, report_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отчета: {e}")
        bot.send_message(message.chat.id, "❌ Не удалось сформировать отчет.")


# Команда полной очистки истории трат пользователя
@bot.message_handler(commands=['clear_expenses'])
def clear_expenses(message):
    if is_spam(message.chat.id): return
    try:
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_expenses WHERE user_id = ?", (message.chat.id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "🗑️ **Вся история ваших расходов успешно удалена из базы данных!**",
                         parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка очистки: {e}")


# ИНТЕЛЛЕКТУАЛЬНЫЙ АНАЛИЗАТОР ЧАТА (ВСЕГДА В САМОМ НИЗУ ХЕНДЛЕРОВ)
@bot.message_handler(func=lambda message: True)
def handle_incoming_text(message):
    if is_spam(message.chat.id): return
    text = message.text.strip()

    # Проверяем, ввел ли пользователь расход формата "Еда 500"
    try:
        parts = text.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].replace('.', '', 1).isdigit():
            category = parts[0]
            amount = float(parts[1])

            # Записываем транзакцию в базу данных SQLite
            conn = sqlite3.connect('finance.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_expenses (user_id, category, amount, date) VALUES (?, ?, ?, date('now'))",
                (message.chat.id, category, amount)
            )
            conn.commit()
            conn.close()

            bot.send_message(message.chat.id,
                             f"✅ **Успешно записано в фин-трекер!**\n📥 Категория: `{category}`\n💰 Сумма: **{amount:.2f} руб.**",
                             parse_mode="Markdown")
            return
    except Exception as e:
        print(f"Ошибка парсинга: {e}")

    # Если это простое текстовое сообщение — выдаем умное меню-инструкцию
    bot.send_message(
        message.chat.id,
        "🤖 **Инвестиционный Помощник Pro**\n\n"
        "📥 **Чтобы внести новый расход в базу данных, напишите мне в чат:**\n"
        "`Название_категории Сумма` (например: *Продукты 1500* или *Такси 450*)\n\n"
        "🗒️ Используйте меню или команду /report для выгрузки статистики.\n"
        "🖥️ Нажмите кнопку **«Open»** для запуска визуального инвест-терминала!",
        parse_mode="Markdown"
    )


if __name__ == '__main__':
    print("Профессиональное мультиядро фин-учета запущено...")
    bot.infinity_polling()


  
