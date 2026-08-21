import telebot
import time
import requests
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler


# Инициализируем бота
TOKEN = 'token'
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

# ================= 📈 ПРОКАЧАННЫЕ БИРЖЕВЫЕ МЕДИА-МОДУЛИ =================

def get_forex_rates():
    try:
        # Международный шлюз, отдающий котировки относительно USD для всех стран
        url = "https://er-api.com"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            rates = response.json()["rates"]

            # Рассчитываем кросс-курсы к RUB и BYN на основе доллара
            usd_rub = rates["RUB"]
            usd_byn = rates["BYN"]
            usd_cny = rates["CNY"]

            eur_rub = usd_rub / rates["EUR"]
            eur_byn = usd_byn / rates["EUR"]

            return (
                "📰 <b>МАКРОЭКОНОМИКА: МЕЖДУНАРОДНЫЙ ВАЛЮТНЫЙ ШЛЮЗ</b>\n"
                "📌 <i>Синхронизация курсов в реальном времени (Глобальный API)</i>\n\n"
                "💵 <b>Курсы к российскому рублю (RUB):</b>\n"
                f"▪️ Доллар США (USD): <code>{usd_rub:.2f} RUB</code>\n"
                f"▪️ Еврозона (EUR): <code>{eur_rub:.2f} RUB</code>\n"
                f"▪️ Юань КНР (CNY): <code>{usd_rub / usd_cny:.2f} RUB</code>\n\n"
                "🇧🇾 <b>Курсы к белорусскому рублю (BYN):</b>\n"
                f"▪️ Доллар США (USD): <code>{usd_byn:.4f} BYN</code>\n"
                f"▪️ Еврозона (EUR): <code>{eur_byn:.4f} BYN</code>\n"
                f"▪️ Российский рубль (100 RUB): <code>{(usd_byn / usd_rub) * 100:.4f} BYN</code>\n\n"
                "💡 <b>Аналитическая сводка:</b>\n"
                "Глобальный шлюз работает без геоблокировок и ограничений. Капитал рекомендуется диверсифицировать.\n"
                "📊 <i>Статус: Стабилен. Источник: ExchangeRate Open API.</i>"
            )
    except Exception as e:
        print(f"Ошибка международного шлюза валют: {e}")
    return "⚠️ Валютный шлюз временно перегружен. Повторите попытку позже."


def get_moex_stocks():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            rows = response.json()["securities"]["data"]
            target_tickers = {"SBER": "🍎 Сбербанк", "GAZP": "🔥 Газпром", "LKOH": "⛽ Лукойл", "YNDX": "📱 Яндекс",
                              "NVTK": "❄️ Новатэк"}

            result_text = (
                "📰 <b>ОБЗОР РЫНКА: АКЦИИ МОСКОВСКОЙ БИРЖИ (MOEX)</b>\n"
                "📌 <i id=\"stocks-trend\">Дневной срез капитализации крупнейших эмитентов</i>\n\n"
            )
            found = False
            for row in rows:
                secid, price = row[0], row[1]
                if secid in target_tickers and price is not None:
                    found = True
                    result_text += f"▪️ <b>{target_tickers[secid]}</b> ({secid}): <code>{price:.2f} RUB</code>\n"

            if found:
                result_text += (
                    "\n💡 <b>Рыночный индикатор:</b>\n"
                    "Текущие ценовые уровни голубых фишек отражают баланс корпоративных прибылей и дивидендных ожиданий. "
                    "В периоды высокой ключевой ставки акции требуют жесткого риск-менеджмента. Фокусируйтесь на компаниях с чистой денежной позицией.\n\n"
                    "⚡ <i>Котировки обновлены напрямую из торгового ядра MOEX.</i>"
                )
                return result_text
    except Exception as e:
        print(f"Ошибка акций MOEX: {e}")
    return "⚠️ Торговый сервер MOEX не отвечает. Проверьте подключение к российскому VPN."


def get_moex_bonds():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            rows = response.json()["securities"]["data"]
            target_bonds = {
                "SU26238RMFS4": "🏛️ ОФЗ 26238 (Долгосрочная, 2041 год)",
                "SU26244RMFS2": "🏛️ ОФЗ 26244 (Среднесрочная, 2034 год)",
                "SU26243RMFS4": "🏛️ ОФЗ 26243 (Краткосрочная, 2029 год)"
            }
            result_text = (
                "📰 <b>СТРАТЕГИЯ: РЫНОК ГОСДОЛГА РФ (ОФЗ)</b>\n"
                "📌 <i>Фиксация безрисковой доходности</i>\n\n"
            )
            found = False
            for row in rows:
                secid, price, bond_yield = row[0], row[1], row[2]
                if secid in target_bonds:
                    found = True
                    p_str = f"{price:.2f}%" if price is not None else "нет торгов"
                    y_str = f"{bond_yield:.2f}%" if bond_yield is not None else "нет данных"
                    result_text += f"▪️ <b>{target_bonds[secid]}</b>\n  Текущая цена: <code>{p_str}</code> | <b>Доходность: {y_str} в год</b>\n\n"

            if found:
                result_text += (
                    "💡 <b>Аналитический вердикт:</b>\n"
                    "Государственные облигации (ОФЗ-ПД) позволяют зафиксировать рекордную доходность на годы вперед. "
                    "В сценарии снижения инфляции долгосрочные облигации покажут максимальный прирост тела капитала за счет эффекта переоценки.\n\n"
                    "⚖️ <i>Риск-статус: Минимальный (Суверенный эмитент).</i>"
                )
                return result_text
    except Exception as e:
        print(f"Ошибка облигаций MOEX: {e}")
    return "⚠️ Долговой рынок МосБиржи временно недоступен под VPN."


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
            text = (
                "📰 <b>АНАЛИТИКА: МИРОВЫЕ СЫРЬЕВЫЕ РЫНКИ</b>\n"
                "📌 <i>Защитные активы и энергетический сектор</i>\n\n"
            )
            if gold_price:
                gold_ounce = gold_price * 31.1035
                text += (
                    f"👑 <b>Золото спот (GLDRUB_TOM):</b>\n"
                    f"  Цена за 1 грамм: <code>{gold_price:.2f} RUB</code>\n"
                    f"  Тройская унция: <code>{gold_ounce:.2f} RUB</code>\n\n"
                )
            if brent_price:
                text += f"🛢️ <b>Нефть марки Brent (OIL):</b>\n  Стоимость барреля: <code>{brent_price:.2f} USD</code>\n\n"

            text += (
                "💡 <b>Макро-комментарий:</b>\n"
                "Золото выступает главным глобальным предохранителем от геополитических шоков и инфляции. "
                "Наш симулятор портфеля во вкладке Mini App автоматически рассчитывает реальную покупательскую способность капитала, опираясь на эти базовые сырьевые котировки.\n\n"
                "🏁 <i>Синхронизация с товарной секцией биржи активна.</i>"
            )
            return text
    except Exception as e:
        print(f"Ошибка товаров: {e}")
    return "⚠️ Не удалось связаться с товарной секцией Московской Биржи."


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


# Функция, которая будет отправлять утреннюю сводку
def send_morning_investment_news():
    # Собираем свежие данные из наших прокачанных модулей
    rates_text = get_forex_rates()
    stocks_text = get_moex_stocks()

    # Твой личный ID в Телеграм (или ID базы пользователей)
    # Замени 123456789 на свой реальный Telegram ID, чтобы бот знал кому писать!
    admin_chat_id = 867341337

    morning_report = (
        "☀️ <b>УТРЕННИЙ ФИНАНСОВЫЙ ТЕРМИНАЛ PRO</b>\n"
        "📅 <i>Свежий макроэкономический срез рынков</i>\n\n"
        f"{rates_text}\n\n"
        f"{stocks_text}\n\n"
        "🎯 <b>План на день:</b> Не совершайте импульсивных сделок, придерживайтесь стратегии!"
    )

    try:
        bot.send_message(admin_chat_id, morning_report, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка утренней рассылки: {e}")


# Запуск планировщика задач в фоновом режиме
scheduler = BackgroundScheduler(timezone="Europe/Moscow")

# Настраиваем отправку каждый день строго в 09:00 утра по Минску/Москве
scheduler.add_job(send_morning_investment_news, 'cron', hour=9, minute=0)
scheduler.start()

if __name__ == '__main__':
    print("Профессиональное мультиядро фин-учета запущено...")
    bot.infinity_polling()

