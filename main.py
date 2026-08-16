import telebot
import time
import requests

TOKEN = 'TOKEN'
bot = telebot.TeleBot(TOKEN)

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


# Валютный модуль на базе официального API Центробанка РФ
def get_forex_rates():
    try:
        # Используем стабильное JSON-API курсов валют ЦБ РФ
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)
        data = response.json()

        if "Valute" in data:
            valute = data["Valute"]

            # Извлекаем курсы к российскому рублю (RUB)
            usd_rub = valute["USD"]["Value"]
            eur_rub = valute["EUR"]["Value"]
            cny_rub = valute["CNY"]["Value"] / valute["CNY"]["Nominal"]  # с учетом номинала (10 юаней)
            byn_rub = valute["BYN"]["Value"]  # курс 1 белорусского рубля к российскому

            # Рассчитываем кросс-курсы к белорусскому рублю (BYN)
            usd_byn = usd_rub / byn_rub if byn_rub else 0
            eur_byn = eur_rub / byn_rub if byn_rub else 0
            cny_byn = (cny_rub * 10) / byn_rub if byn_rub else 0

            text = (
                "💵 **Официальные курсы валют Центробанка:**\n\n"
                "📊 **К российскому рублю (RUB):**\n"
                f"🇺🇸 1 USD = {usd_rub:.2f} RUB\n"
                f"🇪🇺 1 EUR = {eur_rub:.2f} RUB\n"
                f"🇨🇳 10 CNY = {cny_rub * 10:.2f} RUB\n\n"
                "🇧🇾 **К белорусскому рублю (BYN):**\n"
                f"🇺🇸 1 USD = {usd_byn:.4f} BYN\n"
                f"🇪🇺 1 EUR = {eur_byn:.4f} BYN\n"
                f"🇨🇳 10 CNY = {cny_byn:.4f} BYN\n\n"
                "🏛 _Источник котировок: Банк России_"
            )
            return text
        else:
            return "⚠️ Не удалось разобрать структуру данных Банка России."

    except Exception as e:
        print(f"Ошибка API ЦБ РФ: {e}")
        return "❌ Ошибка при запросе котировок. Не удалось подключиться к серверу ЦБ."


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_spam(message.chat.id): return
    welcome_text = (
        "👋 <b>Привет! Я твой личный Финансовый Ассистент Pro.</b>\n\n"
        "🚀 <b>Как пользоваться ботом?</b>\n"
        "Нажми кнопку <b>«Open»</b> в углу экрана, чтобы открыть визуальный калькулятор!\n\n"
        "📖 <b>Команды финансовой аналитики:</b>\n"
        "/rates — Актуальные курсы мировых валют\n"
        "/snowball — Стратегия закрытия долгов\n"
        "/compound — Магия сложного процента\n"
        "/safety_net — Расчет финансовой подушки"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")


@bot.message_handler(commands=['rates'])
def show_rates(message):
    if is_spam(message.chat.id): return
    waiting_msg = bot.send_message(message.chat.id, "🔄 Запрашиваю официальные данные у Банка России...")
    rates_text = get_forex_rates()
    bot.delete_message(message.chat.id, waiting_msg.message_id)
    bot.send_message(message.chat.id, rates_text, parse_mode="Markdown")


@bot.message_handler(commands=['snowball'])
def info_snowball(message):
    if is_spam(message.chat.id): return
    text = "📉 **Метод 'Снежного кома'**: отсортируй долги от меньшего к большему и направляй ускоритель на первый."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['compound'])
def info_compound(message):
    if is_spam(message.chat.id): return
    text = "📈 **Сложный процент**: начисление процентов на проценты. Время — твой главный союзник."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(commands=['safety_net'])
def info_safety(message):
    if is_spam(message.chat.id): return
    text = "💰 **Подушка безопасности**: сумма обязательных расходов за 3-6 месяцев, хранящаяся на накопительном счете."
    bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if is_spam(message.chat.id): return
    bot.send_message(message.chat.id,
                     "🤖 Я понимаю только команды из меню. Нажми кнопку <b>«Open»</b> для калькуляторов!",
                     parse_mode="HTML")


if __name__ == '__main__':
    print("Локализованная Pro-версия на API ЦБ РФ запущена...")
    bot.infinity_polling()


    
