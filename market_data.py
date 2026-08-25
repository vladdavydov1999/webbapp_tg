"""
Слой получения рыночных данных для бота.

Используются бесплатные источники, доступные из России без VPN:
  * ЦБ РФ (cbr-xml-daily) — официальные курсы валют к рублю: USD, EUR, CNY, BYN, PLN;
  * Нацбанк Польши (api.nbp.pl) — цена золота (XAU), пересчитанная в USD за тройскую унцию;
  * CoinGecko (api.coingecko.com) — цена Bitcoin (BTC) в USD;
  * Yahoo Finance — цена нефти Brent (BZ=F), работает в режиме "best effort".

Все запросы выполняются с таймаутом и кэшируются на короткое время,
чтобы не долбить чужие API при каждом нажатии кнопки.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Настройки
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = 10 * 60  # 10 минут
TIMEOUT = 8
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

URL_CBR = "https://www.cbr-xml-daily.ru/daily_json.js"
URL_NBP_GOLD = "https://api.nbp.pl/api/cenyzlota?format=json"
URL_COINGECKO = (
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
)
URL_YAHOO_BRENT = "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F"

# Тройская унция = 31,1035 грамма
GRAMS_PER_TROY_OUNCE = 31.1035

# Справочное значение нефти Brent (USD/баррель) на случай, если источник недоступен.
# Всегда помечается как "справочное", чтобы не вводить в заблуждение.
BRENT_REFERENCE_USD = 83.0

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})

_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, producer):
    """Возвращает закэшированное значение или вызывает producer и кладёт в кэш."""
    now = time.time()
    hit = _cache.get(key)
    if hit and (now - hit[0]) < CACHE_TTL_SECONDS:
        return hit[1]

    value = producer()
    _cache[key] = (now, value)
    return value


def _get_json(url: str, params: Optional[dict] = None):
    response = _session.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Источники данных
# ---------------------------------------------------------------------------
def _fetch_cbr() -> dict[str, float]:
    """Официальные курсы ЦБ РФ: возвращает словарь код валюты -> рублей за 1 единицу."""
    data = _get_json(URL_CBR)
    valute = data.get("Valute", {})

    def rub_per_unit(code: str) -> float:
        item = valute.get(code)
        if not item:
            raise KeyError(f"Валюта {code} отсутствует в ответе ЦБ РФ")
        nominal = float(item.get("Nominal", 1))
        value = float(item.get("Value", 0))
        return value / nominal

    return {
        "USD": rub_per_unit("USD"),
        "EUR": rub_per_unit("EUR"),
        "CNY": rub_per_unit("CNY"),
        "BYN": rub_per_unit("BYN"),
        "PLN": rub_per_unit("PLN"),
    }


def _fetch_gold_usd() -> float:
    """Цена золота в USD за тройскую унцию через Нацбанк Польши + курс ЦБ РФ."""
    # Курсы ЦБ РФ могут быть закэшированы, это нормально.
    cbr = get_cbr_rates()

    # api.nbp.pl возвращает список вида [{"data": "...", "cena": 312.5}] — PLN за грамм.
    rows = _get_json(URL_NBP_GOLD)
    pln_per_gram = float(rows[0]["cena"])

    rub_per_pln = cbr["PLN"]
    rub_per_usd = cbr["USD"]

    # PLN за тройскую унцию -> USD за тройскую унцию.
    # usd_per_pln = долларов за 1 злотый, поэтому умножаем.
    pln_per_ounce = pln_per_gram * GRAMS_PER_TROY_OUNCE
    usd_per_pln = rub_per_pln / rub_per_usd
    return pln_per_ounce * usd_per_pln


def _fetch_btc_usd() -> float:
    """Цена Bitcoin в USD через CoinGecko."""
    data = _get_json(URL_COINGECKO)
    return float(data["bitcoin"]["usd"])


def _fetch_brent_usd() -> float:
    """Цена нефти Brent в USD за баррель через Yahoo Finance (best effort)."""
    data = _get_json(URL_YAHOO_BRENT)
    result = data["chart"]["result"][0]
    return float(result["meta"]["regularMarketPrice"])


# ---------------------------------------------------------------------------
# Публичное API для бота
# ---------------------------------------------------------------------------
def get_cbr_rates() -> dict[str, float]:
    """Курсы ЦБ РФ с кэшем."""
    return _cached("cbr", _fetch_cbr)


def get_gold_usd() -> float:
    """Золото (XAU), USD за тройскую унцию."""
    return _cached("gold_usd", _fetch_gold_usd)


def get_btc_usd() -> float:
    """Bitcoin (BTC), USD."""
    return _cached("btc_usd", _fetch_btc_usd)


def get_brent_usd() -> float:
    """Нефть Brent, USD за баррель. При недоступности источника возвращает справочное значение."""
    return _cached("brent_usd", lambda: _try_fetch_brent())


def _try_fetch_brent() -> float:
    try:
        return _fetch_brent_usd()
    except Exception as exc:  # noqa: BLE001 — источник необязателен
        print(f"⚠️ Нефть Brent: источник недоступен ({exc}), показываю справочное значение.")
        return BRENT_REFERENCE_USD


# ---------------------------------------------------------------------------
# Формирование отчёта
# ---------------------------------------------------------------------------
def build_market_report() -> str:
    """
    Собирает текст сводки для Telegram в корректном HTML.

    Важно: Telegram поддерживает только ограниченный набор тегов (b, i, code и т.п.),
    поэтому здесь используется перевод строки '\\n', а не '<br>'.
    """
    try:
        cbr = get_cbr_rates()

        usd_rub = cbr["USD"]
        eur_rub = cbr["EUR"]
        cny_rub = cbr["CNY"]
        byn_rub = cbr["BYN"]

        usd_eur = usd_rub / eur_rub
        cny_usd = cny_rub / usd_rub  # USD за 1 юань

        try:
            gold_usd = get_gold_usd()
            gold_text = f"<code>{gold_usd:,.1f} USD</code>\n"
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ Золото: {exc}")
            gold_text = "<i>недоступно</i>\n"

        try:
            btc_usd = get_btc_usd()
            btc_text = f"<code>{btc_usd:,.0f} USD</code>"
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ BTC: {exc}")
            btc_text = "<i>недоступно</i>"

        brent_usd = get_brent_usd()  # best effort, всегда возвращает число

        stamp = datetime.now().strftime("%d.%m.%Y %H:%M")

        return (
            "📰 <b>МЕЖДУНАРОДНЫЙ ИНВЕСТ-ТЕРМИНАЛ PRO</b>\n"
            f"📅 <i>Срез рынков на {stamp}</i>\n\n"
            "💵 <b>КУРСЫ ЦБ РФ:</b>\n"
            f"▪️ Доллар США (USD): <code>{usd_rub:.2f} RUB</code>\n"
            f"▪️ Евро (EUR): <code>{eur_rub:.2f} RUB</code> | ~<code>{usd_eur:.4f} USD</code>\n"
            f"▪️ Китайский юань (CNY): <code>{cny_rub:.2f} RUB</code> | ~<code>{cny_usd:.4f} USD</code>\n"
            f"▪️ Белорусский рубль (BYN): <code>{byn_rub:.2f} RUB</code>\n\n"
            "🏆 <b>ДРАГМЕТАЛЛЫ И ЭНЕРГОНОСИТЕЛИ:</b>\n"
            f"▪️ Золото (XAU, унция): {gold_text}"
            f"▪️ Нефть Brent (баррель): <code>{brent_usd:.2f} USD</code>\n\n"
            "🌍 <b>КРИПТОВАЛЮТЫ:</b>\n"
            f"▪️ Bitcoin (BTC): {btc_text}\n\n"
            "⚡️ <i>Данные: ЦБ РФ, Нацбанк Польши, CoinGecko.</i> "
            "<i>Источник нефти может показывать справочное значение.</i>"
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Ошибка сбора рыночного отчёта: {exc}")
        return "⚠️ Не удалось получить данные рынка. Попробуйте позже."


if __name__ == "__main__":
    print(build_market_report())
