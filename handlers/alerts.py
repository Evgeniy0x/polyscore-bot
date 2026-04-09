# PolyScore — 🔔 Система алертов на цену
#
# Пользователь может поставить алерт на рынок:
# "Уведоми меня когда YES достигнет 70%"
# Фоновый воркер проверяет цены каждые 5 минут и шлёт уведомление.

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import (
    get_user, get_user_alerts, add_price_alert,
    delete_alert, get_all_active_alerts, mark_alert_triggered
)
from services.polymarket import gamma


# ══════════════════════════════════════════════════════════════════════
# Тексты на 12 языков
# ══════════════════════════════════════════════════════════════════════

T = {
    "title": {
        "ru": "🔔 <b>Мои алерты</b>",
        "en": "🔔 <b>My Alerts</b>",
        "es": "🔔 <b>Mis alertas</b>",
        "pt": "🔔 <b>Meus alertas</b>",
        "tr": "🔔 <b>Uyarılarım</b>",
        "id": "🔔 <b>Alert Saya</b>",
        "zh": "🔔 <b>我的提醒</b>",
        "ar": "🔔 <b>تنبيهاتي</b>",
        "fr": "🔔 <b>Mes alertes</b>",
        "de": "🔔 <b>Meine Alarme</b>",
        "hi": "🔔 <b>मेरे अलर्ट</b>",
        "ja": "🔔 <b>マイアラート</b>",
    },
    "no_alerts": {
        "ru": "У тебя пока нет активных алертов.\n\nОткрой любой рынок и нажми 🔔 чтобы добавить алерт на цену.",
        "en": "You have no active alerts yet.\n\nOpen any market and tap 🔔 to add a price alert.",
        "es": "Aún no tienes alertas activas.\n\nAbre cualquier mercado y pulsa 🔔 para añadir una alerta.",
        "pt": "Você ainda não tem alertas ativos.\n\nAbra qualquer mercado e toque 🔔 para adicionar um alerta.",
        "tr": "Henüz aktif uyarınız yok.\n\nHerhangi bir piyasayı açın ve 🔔 tuşuna basın.",
        "id": "Anda belum memiliki alert aktif.\n\nBuka market apapun dan ketuk 🔔 untuk menambah alert.",
        "zh": "您还没有活跃的提醒。\n\n打开任意市场并点击 🔔 添加价格提醒。",
        "ar": "ليس لديك تنبيهات نشطة بعد.\n\nافتح أي سوق واضغط 🔔 لإضافة تنبيه.",
        "fr": "Vous n'avez pas encore d'alertes actives.\n\nOuvrez n'importe quel marché et appuyez sur 🔔.",
        "de": "Du hast noch keine aktiven Alarme.\n\nÖffne einen Markt und tippe 🔔 um einen Alarm hinzuzufügen.",
        "hi": "अभी तक कोई सक्रिय अलर्ट नहीं है।\n\nकोई भी मार्केट खोलें और 🔔 दबाएं।",
        "ja": "アクティブなアラートはまだありません。\n\n市場を開いて 🔔 をタップしてアラートを追加。",
    },
    "alert_line_above": {
        "ru": "📈 YES ≥ {price}% — {question}",
        "en": "📈 YES ≥ {price}% — {question}",
        "es": "📈 YES ≥ {price}% — {question}",
        "pt": "📈 YES ≥ {price}% — {question}",
        "tr": "📈 YES ≥ {price}% — {question}",
        "id": "📈 YES ≥ {price}% — {question}",
        "zh": "📈 YES ≥ {price}% — {question}",
        "ar": "📈 YES ≥ {price}% — {question}",
        "fr": "📈 YES ≥ {price}% — {question}",
        "de": "📈 YES ≥ {price}% — {question}",
        "hi": "📈 YES ≥ {price}% — {question}",
        "ja": "📈 YES ≥ {price}% — {question}",
    },
    "alert_line_below": {
        "ru": "📉 YES ≤ {price}% — {question}",
        "en": "📉 YES ≤ {price}% — {question}",
        "es": "📉 YES ≤ {price}% — {question}",
        "pt": "📉 YES ≤ {price}% — {question}",
        "tr": "📉 YES ≤ {price}% — {question}",
        "id": "📉 YES ≤ {price}% — {question}",
        "zh": "📉 YES ≤ {price}% — {question}",
        "ar": "📉 YES ≤ {price}% — {question}",
        "fr": "📉 YES ≤ {price}% — {question}",
        "de": "📉 YES ≤ {price}% — {question}",
        "hi": "📉 YES ≤ {price}% — {question}",
        "ja": "📉 YES ≤ {price}% — {question}",
    },
    "delete_btn": {
        "ru": "🗑 Удалить", "en": "🗑 Delete", "es": "🗑 Eliminar",
        "pt": "🗑 Excluir", "tr": "🗑 Sil", "id": "🗑 Hapus",
        "zh": "🗑 删除", "ar": "🗑 حذف", "fr": "🗑 Supprimer",
        "de": "🗑 Löschen", "hi": "🗑 हटाएं", "ja": "🗑 削除",
    },
    "back_btn": {
        "ru": "🔙 Назад", "en": "🔙 Back", "es": "🔙 Atrás",
        "pt": "🔙 Voltar", "tr": "🔙 Geri", "id": "🔙 Kembali",
        "zh": "🔙 返回", "ar": "🔙 رجوع", "fr": "🔙 Retour",
        "de": "🔙 Zurück", "hi": "🔙 वापस", "ja": "🔙 戻る",
    },
    "add_alert_prompt": {
        "ru": (
            "🔔 <b>Добавить алерт на рынок</b>\n\n"
            "<b>{question}</b>\n\n"
            "Текущая цена YES: <b>{current}%</b>\n\n"
            "Выбери уровень срабатывания:"
        ),
        "en": (
            "🔔 <b>Add price alert</b>\n\n"
            "<b>{question}</b>\n\n"
            "Current YES price: <b>{current}%</b>\n\n"
            "Choose trigger level:"
        ),
        "es": (
            "🔔 <b>Agregar alerta de precio</b>\n\n"
            "<b>{question}</b>\n\n"
            "Precio YES actual: <b>{current}%</b>\n\n"
            "Elige el nivel de activación:"
        ),
        "pt": (
            "🔔 <b>Adicionar alerta de preço</b>\n\n"
            "<b>{question}</b>\n\n"
            "Preço YES atual: <b>{current}%</b>\n\n"
            "Escolha o nível de ativação:"
        ),
        "tr": (
            "🔔 <b>Fiyat uyarısı ekle</b>\n\n"
            "<b>{question}</b>\n\n"
            "Mevcut YES fiyatı: <b>{current}%</b>\n\n"
            "Tetikleme seviyesini seçin:"
        ),
        "id": (
            "🔔 <b>Tambah alert harga</b>\n\n"
            "<b>{question}</b>\n\n"
            "Harga YES saat ini: <b>{current}%</b>\n\n"
            "Pilih level pemicu:"
        ),
        "zh": (
            "🔔 <b>添加价格提醒</b>\n\n"
            "<b>{question}</b>\n\n"
            "当前 YES 价格: <b>{current}%</b>\n\n"
            "选择触发价格:"
        ),
        "ar": (
            "🔔 <b>إضافة تنبيه سعر</b>\n\n"
            "<b>{question}</b>\n\n"
            "سعر YES الحالي: <b>{current}%</b>\n\n"
            "اختر مستوى التفعيل:"
        ),
        "fr": (
            "🔔 <b>Ajouter une alerte de prix</b>\n\n"
            "<b>{question}</b>\n\n"
            "Prix YES actuel: <b>{current}%</b>\n\n"
            "Choisissez le niveau de déclenchement:"
        ),
        "de": (
            "🔔 <b>Preisalarm hinzufügen</b>\n\n"
            "<b>{question}</b>\n\n"
            "Aktueller YES-Preis: <b>{current}%</b>\n\n"
            "Wähle den Auslösepegel:"
        ),
        "hi": (
            "🔔 <b>मूल्य अलर्ट जोड़ें</b>\n\n"
            "<b>{question}</b>\n\n"
            "वर्तमान YES मूल्य: <b>{current}%</b>\n\n"
            "ट्रिगर स्तर चुनें:"
        ),
        "ja": (
            "🔔 <b>価格アラート追加</b>\n\n"
            "<b>{question}</b>\n\n"
            "現在の YES 価格: <b>{current}%</b>\n\n"
            "トリガーレベルを選択:"
        ),
    },
    "alert_saved": {
        "ru": "✅ Алерт сохранён! Уведомлю когда YES {dir} {price}%.",
        "en": "✅ Alert saved! I'll notify you when YES {dir} {price}%.",
        "es": "✅ ¡Alerta guardada! Te notificaré cuando YES {dir} {price}%.",
        "pt": "✅ Alerta salvo! Vou te notificar quando YES {dir} {price}%.",
        "tr": "✅ Uyarı kaydedildi! YES {dir} {price}% olduğunda sizi bilgilendireceğim.",
        "id": "✅ Alert tersimpan! Saya akan memberi tahu Anda ketika YES {dir} {price}%.",
        "zh": "✅ 提醒已保存！当 YES {dir} {price}% 时我会通知您。",
        "ar": "✅ تم حفظ التنبيه! سأخبرك عندما YES {dir} {price}%.",
        "fr": "✅ Alerte sauvegardée! Je vous notifierai quand YES {dir} {price}%.",
        "de": "✅ Alarm gespeichert! Ich benachrichtige dich wenn YES {dir} {price}%.",
        "hi": "✅ अलर्ट सहेजा गया! जब YES {dir} {price}% होगा तो मैं सूचित करूंगा।",
        "ja": "✅ アラートを保存しました！YES が {dir} {price}% になったら通知します。",
    },
    "alert_fired": {
        "ru": "🔔 <b>Алерт сработал!</b>\n\n<b>{question}</b>\n\nYES достиг <b>{price}%</b> (цель: {target}%)\n\n👉 Открыть рынок: polymarket.com",
        "en": "🔔 <b>Alert triggered!</b>\n\n<b>{question}</b>\n\nYES reached <b>{price}%</b> (target: {target}%)\n\n👉 Open market: polymarket.com",
        "es": "🔔 <b>¡Alerta activada!</b>\n\n<b>{question}</b>\n\nYES llegó a <b>{price}%</b> (objetivo: {target}%)\n\n👉 Abrir mercado: polymarket.com",
        "pt": "🔔 <b>Alerta ativado!</b>\n\n<b>{question}</b>\n\nYES atingiu <b>{price}%</b> (alvo: {target}%)\n\n👉 Abrir mercado: polymarket.com",
        "tr": "🔔 <b>Uyarı tetiklendi!</b>\n\n<b>{question}</b>\n\nYES <b>{price}%</b>'e ulaştı (hedef: {target}%)\n\n👉 Piyasayı aç: polymarket.com",
        "id": "🔔 <b>Alert terpicu!</b>\n\n<b>{question}</b>\n\nYES mencapai <b>{price}%</b> (target: {target}%)\n\n👉 Buka market: polymarket.com",
        "zh": "🔔 <b>提醒触发！</b>\n\n<b>{question}</b>\n\nYES 达到 <b>{price}%</b>（目标：{target}%）\n\n👉 打开市场：polymarket.com",
        "ar": "🔔 <b>تم تفعيل التنبيه!</b>\n\n<b>{question}</b>\n\nوصل YES إلى <b>{price}%</b> (الهدف: {target}%)\n\n👉 افتح السوق: polymarket.com",
        "fr": "🔔 <b>Alerte déclenchée!</b>\n\n<b>{question}</b>\n\nYES a atteint <b>{price}%</b> (cible: {target}%)\n\n👉 Ouvrir le marché: polymarket.com",
        "de": "🔔 <b>Alarm ausgelöst!</b>\n\n<b>{question}</b>\n\nYES erreichte <b>{price}%</b> (Ziel: {target}%)\n\n👉 Markt öffnen: polymarket.com",
        "hi": "🔔 <b>अलर्ट ट्रिगर हुआ!</b>\n\n<b>{question}</b>\n\nYES <b>{price}%</b> पर पहुंचा (लक्ष्य: {target}%)\n\n👉 मार्केट खोलें: polymarket.com",
        "ja": "🔔 <b>アラート発動！</b>\n\n<b>{question}</b>\n\nYES が <b>{price}%</b> に達しました（目標：{target}%）\n\n👉 市場を開く：polymarket.com",
    },
    "deleted": {
        "ru": "🗑 Алерт удалён.", "en": "🗑 Alert deleted.",
        "es": "🗑 Alerta eliminada.", "pt": "🗑 Alerta excluído.",
        "tr": "🗑 Uyarı silindi.", "id": "🗑 Alert dihapus.",
        "zh": "🗑 提醒已删除。", "ar": "🗑 تم حذف التنبيه.",
        "fr": "🗑 Alerte supprimée.", "de": "🗑 Alarm gelöscht.",
        "hi": "🗑 अलर्ट हटाया गया।", "ja": "🗑 アラートを削除しました。",
    },
}


def _t(key: str, lang: str, **kwargs) -> str:
    text = T[key].get(lang, T[key]["en"])
    if kwargs:
        text = text.format(**kwargs)
    return text


# ══════════════════════════════════════════════════════════════════════
# Хендлеры
# ══════════════════════════════════════════════════════════════════════

async def cb_alerts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать список алертов пользователя."""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")

    alerts = await get_user_alerts(query.from_user.id)

    text = _t("title", lang) + "\n\n"
    keyboard = []

    if not alerts:
        text += _t("no_alerts", lang)
    else:
        for a in alerts:
            price_pct = int(a["target_price"] * 100)
            q = a["question"][:35] + "…" if len(a["question"]) > 35 else a["question"]
            if a["direction"] == "above":
                line = _t("alert_line_above", lang, price=price_pct, question=q)
            else:
                line = _t("alert_line_below", lang, price=price_pct, question=q)
            text += line + "\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"{_t('delete_btn', lang)} #{a['id']}",
                    callback_data=f"alert:del:{a['id']}"
                )
            ])

    keyboard.append([InlineKeyboardButton(_t("back_btn", lang), callback_data="menu:main")])
    await query.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_alert_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Удалить алерт."""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")

    alert_id = int(query.data.split(":")[2])
    await delete_alert(alert_id, query.from_user.id)

    # Показываем обновлённый список
    await cb_alerts(update, ctx)


async def cb_alert_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """
    Показать форму добавления алерта для рынка.
    Вызывается из детального просмотра рынка: callback_data = "alert:add:{market_idx}"
    """
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")

    market_idx = int(query.data.split(":")[2])

    # Берём рынок из кеша bot_data
    mc = ctx.bot_data.get("mc", {})
    market = mc.get(market_idx)
    if not market:
        await query.answer("❌ Market not found", show_alert=True)
        return

    question = market.get("question", market.get("title", "—"))
    yes_price, _ = gamma.extract_prices(market)
    current_pct = int(yes_price * 100)
    market_id = market.get("id", market.get("slug", str(market_idx)))

    # Предлагаем пороговые уровни: ±10%, ±20%, ±30% от текущей цены
    levels_above = sorted(set([
        min(95, current_pct + 10),
        min(95, current_pct + 20),
        min(95, current_pct + 30),
    ]))
    levels_below = sorted(set([
        max(5, current_pct - 10),
        max(5, current_pct - 20),
        max(5, current_pct - 30),
    ]), reverse=True)

    text = _t("add_alert_prompt", lang, question=question[:60], current=current_pct)

    keyboard = []
    # Кнопки "выше X%"
    row_above = [
        InlineKeyboardButton(
            f"📈 ≥{lvl}%",
            callback_data=f"alert:set:{market_idx}:above:{lvl}"
        ) for lvl in levels_above
    ]
    keyboard.append(row_above)
    # Кнопки "ниже X%"
    row_below = [
        InlineKeyboardButton(
            f"📉 ≤{lvl}%",
            callback_data=f"alert:set:{market_idx}:below:{lvl}"
        ) for lvl in levels_below
    ]
    keyboard.append(row_below)
    keyboard.append([InlineKeyboardButton(_t("back_btn", lang), callback_data=f"m:{market_idx}")])

    await query.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(keyboard))


async def cb_alert_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Сохранить алерт: alert:set:{idx}:{direction}:{price_pct}"""
    query = update.callback_query
    await query.answer()
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "en")

    parts = query.data.split(":")
    market_idx = int(parts[2])
    direction = parts[3]   # above / below
    price_pct = int(parts[4])

    mc = ctx.bot_data.get("mc", {})
    market = mc.get(market_idx)
    if not market:
        await query.answer("❌ Market not found", show_alert=True)
        return

    question = market.get("question", market.get("title", "—"))
    market_id = market.get("id", market.get("slug", str(market_idx)))
    target_price = price_pct / 100.0

    await add_price_alert(query.from_user.id, market_id, question, target_price, direction)

    dir_str = f"≥{price_pct}" if direction == "above" else f"≤{price_pct}"
    text = _t("alert_saved", lang, dir=dir_str, price=price_pct)
    await query.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup([[
                                      InlineKeyboardButton(_t("back_btn", lang), callback_data="alerts")
                                  ]]))


# ══════════════════════════════════════════════════════════════════════
# Фоновый воркер — проверяет алерты каждые 5 минут
# ══════════════════════════════════════════════════════════════════════

import asyncio
import logging
logger = logging.getLogger("PolyScore.alerts")


async def alerts_worker(app):
    """
    Фоновый воркер: каждые 5 минут проверяет все активные алерты.
    Если цена достигла порога — шлёт сообщение пользователю.
    """
    while True:
        try:
            await _check_alerts(app)
        except Exception as e:
            logger.error(f"Alerts worker error: {e}")
        await asyncio.sleep(300)  # 5 минут


async def _check_alerts(app):
    alerts = await get_all_active_alerts()
    if not alerts:
        return

    # Группируем по market_id чтобы не дёргать API лишний раз
    market_prices = {}

    for alert in alerts:
        market_id = alert["market_id"]

        # Получаем цену если ещё не получили
        if market_id not in market_prices:
            try:
                data = await gamma.fetch_market(market_id)
                if data:
                    yes_p, _ = gamma.extract_prices(data)
                    market_prices[market_id] = yes_p
                else:
                    market_prices[market_id] = None
            except Exception:
                market_prices[market_id] = None

        current_price = market_prices.get(market_id)
        if current_price is None:
            continue

        # Проверяем условие
        triggered = False
        if alert["direction"] == "above" and current_price >= alert["target_price"]:
            triggered = True
        elif alert["direction"] == "below" and current_price <= alert["target_price"]:
            triggered = True

        if triggered:
            await mark_alert_triggered(alert["id"])
            await _send_alert_notification(app, alert, current_price)


async def _send_alert_notification(app, alert: dict, current_price: float):
    """Отправить уведомление пользователю."""
    try:
        user_data = await __import__('services.database', fromlist=['get_user']).get_user(alert["user_id"])
        lang = (user_data or {}).get("language", "en")

        current_pct = int(current_price * 100)
        target_pct = int(alert["target_price"] * 100)
        question = alert["question"][:80]

        text = T["alert_fired"].get(lang, T["alert_fired"]["en"]).format(
            question=question,
            price=current_pct,
            target=target_pct
        )

        keyboard = [[InlineKeyboardButton(
            "📊 Открыть рынок" if lang == "ru" else "📊 Open Market",
            callback_data="cat:markets"
        )]]

        await app.bot.send_message(
            chat_id=alert["user_id"],
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info(f"Alert fired: user={alert['user_id']} market={alert['market_id']}")
    except Exception as e:
        logger.error(f"Failed to send alert notification: {e}")
