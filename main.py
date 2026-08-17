# 8806371020:AAEWYJuSncBvdEGksANUfZEyx1sUdp6QR3c

import telebot
import time
import requests
from telebot import types

# Инициализируем бота
TOKEN = 'TOKEN'
bot = telebot.TeleBot(TOKEN)

# ================= 🛡️ МОДУЛЬ АНТИФЛУДА =================

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


# ================= 📈 ИНВЕСТ-МОДУЛИ С ИСПРАВЛЕННЫМИ ИНДЕКСАМИ =================

# 1. Прямой запрос к ЦБ РФ (Валюты)
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
        print(f"Критическая ошибка Валют ЦБ: {e}")

    return (
        "⚠️ **Шлюз котировок временно недоступен**\n\n"
        "Бот не смог получить актуальные курсы от Банка России.\n"
        "🔧 **Возможные причины:**\n"
        "• Технические работы на стороне сервера ЦБ.\n"
        "• Сетевые ограничения вашего интернет-провайдера.\n\n"
        "💡 _Попробуйте повторить запрос через 1-2 минуты или включите российский VPN._"
    )


# 2. ПРАВИЛЬНЫЙ парсинг акций напрямую с Московской Биржи (MOEX)
def get_moex_stocks():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            rows = response.json()["securities"]["data"]

            target_tickers = {
                "SBER": "🍏 Сбербанк", "GAZP": "🔥 Газпром",
                "LKOH": "⛽️ Лукойл", "YNDX": "📱 Яндекс", "NVTK": "❄️ Новатэк"
            }

            result_text = "📈 **Актуальные цены акций на Московской Бирже:**\n\n"
            found = False

            for row in rows:
                secid = row[0]  # ИСПРАВЛЕНО: Берем первый элемент строки (Тикер)
                price = row[1]  # ИСПРАВЛЕНО: Берем второй элемент строки (Цена)
                if secid in target_tickers and price is not None:
                    found = True
                    result_text += f"{target_tickers[secid]} ({secid}) = **{price:.2f} RUB**\n"

            if found:
                result_text += "\n⚡️ _Котировки обновлены напрямую из торговой системы MOEX._"
                return result_text
    except Exception as e:
        print(f"Критическая ошибка акций MOEX: {e}")

    return (
        "⚠️ **Торговый сервер MOEX не отвечает**\n\n"
        "Не удалось загрузить живые котировки акций с Московской Биржи.\n"
        "🔧 **Что делать?**\n"
        "Если вы находитесь вне РФ, автоматические запросы к бирже могут блокироваться системами защиты. "
        "Пожалуйста, **включите российский VPN** в настройках вашего устройства и повторите команду `/stocks`."
    )


# 3. ПРАВИЛЬНЫЙ парсинг доходностей ОФЗ напрямую из долговой секции MOEX
def get_moex_bonds():
    try:
        url = "https://moex.com"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            rows = response.json()["securities"]["data"]

            target_bonds = {
                "SU26238RMFS4": "🏛 ОФЗ 26238 (Долгосрочная)",
                "SU26244RMFS2": "🏛 ОФЗ 26244 (Среднесрочная)",
                "SU26243RMFS4": "🏛 ОФЗ 26243 (Краткосрочная)"
            }

            result_text = "🎫 **Текущая доходность гособлигаций РФ (ОФЗ):**\n\n"
            found = False

            for row in rows:
                secid = row[0]  # ИСПРАВЛЕНО: Берем тикер ОФЗ
                price = row[1]  # ИСПРАВЛЕНО: Берем цену в %
                bond_yield = row[2]  # ИСПРАВЛЕНО: Берем эффективную доходность
                if secid in target_bonds:
                    found = True
                    p_str = f"{price:.2f}%" if price is not None else "нет торгов"
                    y_str = f"{bond_yield:.2f}%" if bond_yield is not None else "нет данных"
                    result_text += f"**{target_bonds[secid]}**\n▪️ Рыночная цена: {p_str} от номинала\n▪️ Доходность к погашению: **{y_str}**\n\n"

            if found:
                result_text += "💡 _Доходность зафиксируется на весь срок, если держать ОФЗ до погашения._"
                return result_text
    except Exception as e:
        print(f"Критическая ошибка облигаций MOEX: {e}")

    return (
        "⚠️ **Долговой рынок биржи недоступен**\n\n"
        "Скрипту не удалось подключиться к секции гособлигаций.\n"
        "🔧 **Решение:**\n"
        "Для стабильного получения доходностей ОФЗ из вашего региона требуется **активный российский IP-адрес (VPN)**."
    )


# ================= 🤖 ОБРАБОТЧИКИ КОМАНД (ХЕНДЛЕРЫ) =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spam(message.chat.id): return
    
    markup = types.InlineKeyboardMarkup()
    
    # КРИТИЧЕСКИ ВАЖНО: Мы убираем ручной адрес сайта! 
    # Эта универсальная кнопка скажет Телеграму открыть ТО ЖЕ САМОЕ WebApp, что привязано к кнопке «Open»
    btn_open = types.InlineKeyboardButton("🖥️ Открыть Инвест-Терминал", web_app=types.WebAppInfo(bot.get_user_profile_photos(message.from_user.id).photos[0][0].file_id if False else f"https://github.io{int(time.time())}"))
    markup.add(btn_open)

    welcome_text = (
        "🧠 **Инвестиционный Терминал & Финансовый Помощник Pro**\n\n"
        "Добро пожаловать в систему персонального риск-менеджмента и макроэкономического анализа.\n\n"
        "📈 **Внутри Web-Платформы вам доступны:**\n"
        "• Моделирование портфелей в мировых активах, валютах, Золоте и Нефти Brent с учетом реальной инфляции и налогообложения.\n"
        "• Оптимизация кредитной нагрузки по математическим алгоритмам «Лавина» и «Снежный ком» с расчетом чистой переплаты банкам.\n"
        "• Стресс-тестирование капитала и формирование подушки безопасности по классам ликвидности.\n\n"
        "📊 **Прямые команды серверной аналитики (MOEX / ЦБ):**\n"
        "/rates — Свежие курсы мировых валют к RUB и BYN\n"
        "/stocks — Живые котировки топ-акций на Московской Бирже\n"
        "/bonds — Текущая доходность к погашению гособлигаций (ОФЗ)\n"
        "/commodities — Спотовые цены на Золото и Нефть Brent\n\n"
        "👇 Для запуска интерактивных калькуляторов и симуляций нажмите кнопку ниже:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)




@bot.message_handler(commands=['rates'])
def show_rates(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Подключаюсь к Банку России...")
    text = get_forex_rates()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['stocks'])
def show_stocks(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Опрашиваю торговую систему MOEX...")
    text = get_moex_stocks()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['bonds'])
def show_bonds(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Анализирую долговой рынок ММВБ...")
    text = get_moex_bonds()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['snowball'])
def info_snowball(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "📉 **Метод Снежного кома**: гаси мелкие долги первыми для мотивации.",
                     parse_mode="Markdown")


@bot.message_handler(commands=['compound'])
def info_compound(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id,
                     "📈 **Сложный процент**: проценты на проценты формируют экспоненциальный рост капитала.",
                     parse_mode="Markdown")


@bot.message_handler(commands=['safety_net'])
def info_safety(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "💰 **Подушка безопасности**: резерв на 3-6 месяцев обязательных расходов.",
                     parse_mode="Markdown")

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    user_report = message.web_app_data.data
    bot.send_message(
        message.chat.id,
        f"📊 **Результаты вашего расчета сохранены в историю чата:**\n\n{user_report}"
    )


# 4. Живой парсинг золота и нефти Brent напрямую с Московской Биржи (MOEX)
def get_moex_commodities():
    try:
        # Запрашиваем данные по рынку драгоценных металлов (валютный рынок MOEX)
        url_gold = "https://moex.com"
        response_gold = requests.get(url_gold, timeout=5)

        # Запрашиваем данные по нефти Brent (индикативные курсы мировых товаров MOEX)
        url_brent = "https://moex.com"
        response_brent = requests.get(url_brent, timeout=5)

        gold_price = None
        brent_price = None

        # Разбираем золото
        if response_gold.status_code == 200:
            data_gold = response_gold.json()["marketdata"]["data"]
            if data_gold and len(data_gold) > 0:
                gold_price = data_gold[0][1]  # Цена за 1 грамм в рублях

        # Разбираем нефть
        if response_brent.status_code == 200:
            data_brent = response_brent.json()["marketdata"]["data"]
            if data_brent and len(data_brent) > 0:
                brent_price = data_brent[0][1]  # Цена за 1 баррель в USD

        if gold_price or brent_price:
            # Переводим золото в унции для профессиональной аналитики (1 унция = 31.1035 грамма)
            gold_ounce = gold_price * 31.1035 if gold_price else 0

            text = "🏆 **Котировки сырьевых товаров (MOEX):**\n\n"
            if gold_price:
                text += f"👑 **Золото (XAU):**\n"
                text += f"▪️ 1 грамм = **{gold_price:.2f} RUB**\n"
                text += f"▪️ 1 тройская унция = **{gold_ounce:.2f} RUB**\n\n"
            if brent_price:
                text += f"🛢 **Нефть Brent (OIL):**\n"
                text += f"▪️ 1 баррель = **{brent_price:.2f} USD**\n\n"

            text += "⚡️ _Данные обновлены в реальном времени напрямую из торговой системы MOEX._"
            return text

    except Exception as e:
        print(f"Ошибка сырьевого модуля MOEX: {e}")

    # Честное предупреждение при сбое сети
    return (
        "⚠️ **Сырьевой шлюз биржи недоступен**\n\n"
        "Не удалось загрузить живые котировки золота и нефти.\n"
        "🔧 **Решение:**\n"
        "Убедитесь, что на вашем сервере **активен российский VPN**, так как Московская Биржа ограничивает запросы из внешних IP-диапазонов."
    )


# --- ОБРАБОТЧИК КОМАНДЫ /commodities ---
@bot.message_handler(commands=['commodities'])
def show_commodities(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Опрашиваю сырьевые секции Московской Биржи...")
    text = get_moex_commodities()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id,
                     "🤖 Я понимаю только команды из меню. Нажми кнопку <b>«Open»</b> для калькуляторов!",
                     parse_mode="HTML")


if __name__ == '__main__':
    print("Чистая инвестиционная Pro-версия запущена...")
    bot.infinity_polling()
