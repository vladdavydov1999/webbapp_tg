import telebot
import time  # Подключаем библиотеку для работы со временем

TOKEN = 'TOKEN'
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения времени последнего сообщения от каждого пользователя
last_message_time = {}


# Функция проверки: не слишком ли быстро отправлено сообщение
def is_spam(chat_id):
    current_time = time.time()
    # Если пользователь нажал кнопку впервые, его еще нет в словаре
    if chat_id not in last_message_time:
        last_message_time[chat_id] = current_time
        return False

    # Считаем, сколько секунд прошло с прошлого нажатия
    time_passed = current_time - last_message_time[chat_id]
    last_message_time[chat_id] = current_time  # Обновляем время на текущее

    # Если прошло меньше 1.5 секунд — это спам/двойной клик
    if time_passed < 1.5:
        return True
    return False


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Если это двойной клик — игнорируем его
    if is_spam(message.chat.id):
        return

    welcome_text = (
        "👋 <b>Привет! Я твой личный Финансовый Ассистент.</b>\n\n"
        "Я помогаю рассчитывать сложный процент и составлять графики закрытия долгов.\n\n"
        "🚀 <b>Как пользоваться ботом?</b>\n"
        "Просто нажми на синюю кнопку <b>«Open»</b> (или иконку слева от поля ввода), "
        "чтобы открыть удобный визуальный калькулятор!\n\n"
        "📖 Или используй меню команд ниже, чтобы почитать полезные финансовые статьи:\n"
        "/snowball — Как работает метод 'Снежного кома'?\n"
        "/compound — Магия сложного процента\n"
        "/safety_net — Как рассчитать финансовую подушку?"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")


@bot.message_handler(commands=['snowball'])
def info_snowball(message):
    if is_spam(message.chat.id): return
    text = (
        "📉 <b>Метод 'Снежного кома' (Debt Snowball):</b>\n\n"
        "1. Выпиши все долги и отсортируй их от меньшего к большему по сумме.\n"
        "2. Плати по всем кредитам строго минимальные платежи.\n"
        "3. Все свободные деньги (ускоритель) направляй на досрочное гашение самого маленького долга.\n"
        "4. Когда мелкий долг закроется, освободившаяся сумма перекидывается на следующий по величине кредит.\n\n"
        "💡 <i>Этот метод признан самым эффективным психологически!</i>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")


@bot.message_handler(commands=['compound'])
def info_compound(message):
    if is_spam(message.chat.id): return
    text = (
        "📈 <b>Магия сложного процента:</b>\n\n"
        "Сложный процент — это начисление процентов на проценты. "
        "Когда твоя прибыль добавляется к начальному капиталу, "
        "в следующем периоде процент начисляется на уже увеличенную сумму.\n\n"
        "⏳ На горизонте 10–15 лет сложный процент способен превратить скромные ежемесячные пополнения в солидный капитал. Проверь это в нашем приложении!"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")


@bot.message_handler(commands=['safety_net'])
def info_safety(message):
    if is_spam(message.chat.id): return
    text = (
        "💰 <b>Финансовая подушка безопасности:</b>\n\n"
        "Это неприкосновенный запас денег на случай форс-мажоров (потеря работы, ремонт, здоровье).\n\n"
        "📐 Посчитай обязательные расходы за месяц (еда, жилье, кредиты) и умножь эту сумму на 3 или 6 месяцев. Держи эти деньги на накопительном счете."
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if is_spam(message.chat.id): return
    bot.send_message(
        message.chat.id,
        "🤖 Я понимаю только команды из меню. Нажми кнопку <b>«Open»</b>, чтобы запустить приложение!",
        parse_mode="HTML"
    )


if __name__ == '__main__':
    print("Бот перезапущен с защитой от двойных кликов...")
    bot.infinity_polling()




