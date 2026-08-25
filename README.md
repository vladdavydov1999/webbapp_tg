# Фин-Терминал Pro

Финансовая экосистема в Telegram:
- **Telegram-бот** (`bot_tg/main.py`) — курсы ЦБ РФ, золото, нефть, Bitcoin + утренняя рассылка;
- **Mini App** (`bot_tg/index.html`) — инвестиционные калькуляторы (портфель, долги, резервный фонд, ипотека);
- **Сайт-визитка** (`bot_tg/landing.html`) — страница проекта с кнопками запуска.

Все данные берутся из **бесплатных источников, доступных из России без VPN**:
| Показатель | Источник |
|------------|----------|
| Валюты USD / EUR / CNY / BYN (в рублях) | ЦБ РФ (cbr-xml-daily) |
| Золото XAU (USD/унция) | Нацбанк Польши (api.nbp.pl) + курс ЦБ РФ |
| Bitcoin BTC (USD) | CoinGecko |
| Нефть Brent (USD/баррель) | Yahoo Finance (best effort, при сбое — справочное значение) |

---

## 🚀 Быстрый старт

### 1. Создание окружения и зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# или  .venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 2. Настройка секретов

Секреты **не должны лежать в коде**. Скопируйте образец и заполните его:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```
TELEGRAM_BOT_TOKEN=1234567890:AAXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
ADMIN_CHAT_ID=0
MINI_APP_URL=https://vladdavydov1999.github.io/webbapp_tg/
TZ=Europe/Moscow
```

Где взять значения:
- `TELEGRAM_BOT_TOKEN` — от бота [@BotFather](https://t.me/BotFather).
- `ADMIN_CHAT_ID` — ваш числовой id (узнаёте через [@userinfobot](https://t.me/userinfobot)); оставьте `0`, чтобы отключить утреннюю рассылку.
- `MINI_APP_URL` — публичный адрес Mini App (для Telegram WebApp).
- `TZ` — часовой пояс для утреннего отчёта (в 09:00).

> ⚠️ Файл `.env` уже добавлен в `.gitignore` — он не должен попадать в git.

### 3. Запуск бота

```bash
cd bot_tg
../.venv/bin/python main.py
```

Проверить сбор данных отдельно (без запуска бота):

```bash
../.venv/bin/python market_data.py
```

---

## 🤖 Команды и кнопки бота

| Действие | Результат |
|----------|-----------|
| `/start`, `/help` | Приветствие и клавиатура меню |
| «📊 Мировые рынки» | Сводка курсов ЦБ РФ, золота, нефти, Bitcoin |
| «📱 Открыть Фин-Терминал» | Кнопка-ссылка WebApp на Mini App |

Утренняя рассылка отправляется автоматически в 09:00 по `TZ` на `ADMIN_CHAT_ID`.

---

## 🌍 Деплой сайта и Mini App

`index.html` и `landing.html` — статические страницы. Проще всего хостить их на **GitHub Pages**:

1. Создайте репозиторий (например, `webbapp_tg`) и загрузите туда `index.html` как главную страницу.
2. Включите GitHub Pages (Settings → Pages → Branch: main).
3. Укажите полученный адрес в `MINI_APP_URL` внутри `.env` и в кнопках `landing.html`.

Затем в [@BotFather](https://t.me/BotFather) → ваш бот → *Bot Settings → Menu Button* укажите `MINI_APP_URL`, чтобы кнопка меню открывала Mini App прямо из чата.

---

## 🗂 Структура проекта

```
Python_project/
├── requirements.txt        # зависимости Python
├── .env.example            # образец секретов (копируется в .env)
├── .gitignore              # исключает .env, БД, venv и пр.
└── bot_tg/
    ├── main.py             # точка входа бота
    ├── config.py           # чтение настроек из окружения/.env
    ├── market_data.py      # слой данных (ЦБ РФ, золото, нефть, BTC) с кэшем
    ├── index.html          # Mini App (калькуляторы)
    └── landing.html        # сайт-визитка
```

---

## 🛠 Технические детали

- **Кэширование**: рыночные данные обновляются не чаще, чем раз в 10 минут (`CACHE_TTL_SECONDS` в `market_data.py`), чтобы не перегружать бесплатные API.
- **Telegram HTML**: используются только поддерживаемые теги (`b`, `i`, `code`), вместо `<br>` применяется перевод строки.
- **Ошибки**: если источник недоступен (кроме ЦБ РФ), бот честно помечает значение как справочное или «недоступно», а не показывает выдуманные цифры.
