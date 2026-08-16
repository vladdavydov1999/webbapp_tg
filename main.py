import os
os.environ['NO_PROXY'] = 'cbr-xml-daily.ru,://moex.com'
import telebot
import time
import requests

# Инициализируем бота
TOKEN = 'ТВОЙ_ТОКЕН_ИЗ_BOTFATHER'
bot = telebot.TeleBot(TOKEN)

# ================= 🛡️ МОДУЛЬ АНТИФЛУДА (ЗАЩИТА ОТ ДВОЙНЫХ КЛИКОВ) =================

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

# ================= 📈 ЧИСТЫЕ СЕТЕВЫЕ ИНВЕСТ-МОДУЛИ =================

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
            
            # Математический кросс-курс для инвесторов из Беларуси на базе данных ЦБ
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
        
    # Понятный пользователю предупредительный сигнал без обмана и ложных цифр
    return (
        "⚠️ **Шлюз котировок временно недоступен**\n\n"
        "Бот не смог получить актуальные курсы от Банка России.\n"
        "🔧 **Возможные причины:**\n"
        "• Технические работы на стороне сервера ЦБ.\n"
        "• Сетевые ограничения вашего интернет-провайдера.\n\n"
        "💡 _Попробуйте повторить запрос через 1-2 минуты или включите российский VPN._"
    )

# 2. Живой парсинг акций напрямую с Московской Биржи (MOEX)
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
                secid = row[0]   # Код бумаги (Тикер)
                price = row[1]   # Цена закрытия/последней сделки
                if secid in target_tickers and price is not None:
                    found = True
                    result_text += f"{target_tickers[secid]} ({secid}) = **{price:.2f} RUB**\n"
            
            if found:
                result_text += "\n⚡️ _Котировки обновлены напрямую из торговой системы MOEX._"
                return result_text
    except Exception as e:
        print(f"Ошибка акций MOEX: {e}")
        
    # Предупредительный сигнал для акций
    return (
        "⚠️ **Торговый сервер MOEX не отвечает**\n\n"
        "Не удалось загрузить живые котировки акций с Московской Биржи.\n"
        "🔧 **Что делать?**\n"
        "Если вы находитесь вне РФ, автоматические запросы к бирже могут блокироваться системами защиты. "
        "Пожалуйста, **включите российский VPN** в настройках вашего устройства и повторите команду `/stocks`."
    )

# 3. Живой парсинг доходностей ОФЗ напрямую из долговой секции MOEX
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
                secid = row[0]       # Код ОФЗ
                price = row[1]       # Рыночная цена в % от номинала
                bond_yield = row[2]  # Эффективная доходность к погашению
                if secid in target_bonds:
                    found = True
                    p_str = f"{price:.2f}%" if price is not None else "нет торгов"
                    y_str = f"{bond_yield:.2f}%" if bond_yield is not None else "нет данных"
                    result_text += f"**{target_bonds[secid]}**\n▪️ Рыночная цена: {p_str} от номинала\n▪️ Доходность к погашению: **{y_str}**\n\n"
            
            if found:
                result_text += "💡 _Доходность зафиксируется на весь срок, если держать ОФЗ до погашения._"
                return result_text
    except Exception as e:
        print(f"Ошибка облигаций MOEX: {e}")
        
    # Предупредительный сигнал для облигаций
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
    welcome_text = (
        "👋 <b>Привет! Я твой личный Финансовый Ассистент Pro.</b>\n\n"
        "🚀 Нажми кнопку <b>«Open»</b> в углу экрана, чтобы открыть визуальный калькулятор!\n\n"
        "📖 <b>Команды финансовой аналитики:</b>\n"
        "/rates — Курсы мировых валют ЦБ\n"
        "/stocks — Котировки акций (MOEX)\n"
        "/bonds — Доходность гособлигаций (ОФЗ)\n\n"
        "🧮 <b>Теория:</b> /snowball | /compound | /safety_net"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")

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
    bot.send_message(message.chat.id, "📉 **Метод Снежного кома**: гаси мелкие долги первыми для мотивации.", parse_mode="Markdown")

@bot.message_handler(commands=['compound'])
def info_compound(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "📈 **Сложный процент**: проценты на проценты формируют экспоненциальный рост капитала.", parse_mode="Markdown")

@bot.message_handler(commands=['safety_net'])
def info_safety(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "💰 **Подушка безопасности**: резерв на 3-6 месяцев обязательных расходов.", parse_mode="Markdown")

# КРИТИЧЕСКИ ВАЖНО: Универсальная заглушка на текст ВСЕГДА В САМОМ НИЗУ ХЕНДЛЕРОВ!
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id, "🤖 Я понимаю только команды из меню. Нажми кнопку <b>«Open»</b> для калькуляторов!", parse_mode="HTML")

if __name__ == '__main__':
    # Очищаем терминал перед запуском
    print("Чистая инвестиционная Pro-версия запущена...")
    bot.infinity_polling()
