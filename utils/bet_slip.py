# PolyScore — Bet Slip Cards (Pillow)
# Генерирует PNG карточки ставок для шаринга в Telegram/X
# Формат: тёмный фон, зелёный акцент, как DraftKings

from PIL import Image, ImageDraw, ImageFont
import io
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    CARD_BG_COLOR, CARD_ACCENT_GREEN, CARD_ACCENT_RED,
    CARD_TEXT_COLOR, CARD_MUTED_COLOR
)
from services.polymarket import price_to_american_odds


def hex_to_rgb(hex_color: str) -> tuple:
    """#RRGGBB → (R, G, B)"""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Загрузить системный шрифт."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()


def create_bet_slip(
    question:  str,
    outcome:   str,   # "YES" или "NO"
    amount:    float,
    price:     float,
    market_id: str = "",
    username:  str = "",
) -> bytes:
    """
    Создать PNG карточку одиночной ставки.
    Возвращает bytes (PNG).
    """
    W, H = 600, 320
    img  = Image.new("RGB", (W, H), hex_to_rgb(CARD_BG_COLOR))
    draw = ImageDraw.Draw(img)

    # ── Фон с градиентом (ручной) ──────────────────────────────────────
    for y in range(H):
        alpha = int(15 * (1 - y / H))
        draw.line([(0, y), (W, y)], fill=(0, 255, 136, alpha))

    # ── Цветная полоска сверху ─────────────────────────────────────────
    accent = CARD_ACCENT_GREEN if outcome == "YES" else CARD_ACCENT_RED
    draw.rectangle([(0, 0), (W, 5)], fill=hex_to_rgb(accent))

    # ── Logo / Brand ──────────────────────────────────────────────────
    font_brand = get_font(14, bold=True)
    draw.text((24, 18), "⚡ POLYSCORE", fill=hex_to_rgb(accent), font=font_brand)
    draw.text((W - 100, 18), "via Polymarket", fill=hex_to_rgb(CARD_MUTED_COLOR),
              font=get_font(11))

    # ── Вопрос ─────────────────────────────────────────────────────────
    font_q = get_font(16, bold=True)
    # Перенос текста вручную
    max_chars = 55
    if len(question) > max_chars:
        # Режем по словам
        words, line, lines_q = question.split(), "", []
        for w in words:
            if len(line) + len(w) + 1 <= max_chars:
                line = (line + " " + w).strip()
            else:
                if line:
                    lines_q.append(line)
                line = w
        if line:
            lines_q.append(line)
        q_display = "\n".join(lines_q[:2])
        if len(lines_q) > 2:
            q_display += "…"
    else:
        q_display = question

    draw.text((24, 55), q_display, fill=hex_to_rgb(CARD_TEXT_COLOR), font=font_q)

    # ── Разделитель ───────────────────────────────────────────────────
    sep_y = 130
    draw.line([(24, sep_y), (W - 24, sep_y)], fill=(50, 60, 70), width=1)

    # ── Исход (YES/NO + odds) ─────────────────────────────────────────
    font_outcome  = get_font(32, bold=True)
    font_odds     = get_font(22, bold=True)

    outcome_color = hex_to_rgb(CARD_ACCENT_GREEN) if outcome == "YES" \
                    else hex_to_rgb(CARD_ACCENT_RED)
    odds_str      = price_to_american_odds(price)
    prob_str      = f"{price:.0%}"

    draw.text((24, 145), outcome, fill=outcome_color, font=font_outcome)
    draw.text((120, 155), odds_str, fill=outcome_color, font=font_odds)
    draw.text((230, 160), f"({prob_str})", fill=hex_to_rgb(CARD_MUTED_COLOR),
              font=get_font(16))

    # ── Ставка и потенциальный выигрыш ────────────────────────────────
    font_m   = get_font(14)
    font_mb  = get_font(14, bold=True)

    potential = amount / price if price > 0 else 0
    profit    = potential - amount

    draw.text((24, 210),  "СТАВКА",      fill=hex_to_rgb(CARD_MUTED_COLOR), font=font_m)
    draw.text((24, 228),  f"${amount:.2f} USDC",
              fill=hex_to_rgb(CARD_TEXT_COLOR), font=font_mb)

    draw.text((200, 210), "ВЫИГРЫШ",     fill=hex_to_rgb(CARD_MUTED_COLOR), font=font_m)
    draw.text((200, 228), f"${potential:.2f} USDC",
              fill=hex_to_rgb(CARD_ACCENT_GREEN), font=font_mb)

    draw.text((380, 210), "ПРОФИТ",      fill=hex_to_rgb(CARD_MUTED_COLOR), font=font_m)
    draw.text((380, 228), f"+${profit:.2f}",
              fill=hex_to_rgb(CARD_ACCENT_GREEN), font=font_mb)

    # ── Нижняя строка ─────────────────────────────────────────────────
    draw.line([(24, 270), (W - 24, 270)], fill=(50, 60, 70), width=1)

    footer_text = f"@{username} · t.me/PolymarketMAMA_Bot" if username else "t.me/PolymarketMAMA_Bot"
    draw.text((24, 283), footer_text,
              fill=hex_to_rgb(CARD_MUTED_COLOR), font=get_font(11))

    if market_id:
        draw.text((W - 120, 283), f"ID: {market_id[:8]}…",
                  fill=hex_to_rgb(CARD_MUTED_COLOR), font=get_font(11))

    # ── Сохранить в bytes ─────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


def create_parlay_slip(
    legs:     list[dict],
    amount:   float,
    username: str = "",
) -> bytes:
    """
    Создать PNG карточку парлея.

    legs = [
        {"question": "...", "outcome": "YES", "price": 0.65},
        ...
    ]
    """
    # Считаем суммарные odds
    total_odds  = 1.0
    for leg in legs:
        p = float(leg.get("price", 0))
        if p > 0:
            total_odds *= (1 / p)

    potential   = amount * total_odds
    profit      = potential - amount

    W = 600
    H = 160 + 60 * len(legs) + 120  # Динамическая высота
    H = max(H, 380)

    img  = Image.new("RGB", (W, H), hex_to_rgb(CARD_BG_COLOR))
    draw = ImageDraw.Draw(img)

    # Акцент сверху
    draw.rectangle([(0, 0), (W, 5)], fill=hex_to_rgb(CARD_ACCENT_GREEN))

    # Brand
    draw.text((24, 18), "⚡ POLYSCORE · PARLAY",
              fill=hex_to_rgb(CARD_ACCENT_GREEN), font=get_font(14, bold=True))
    draw.text((W - 100, 18), "via Polymarket",
              fill=hex_to_rgb(CARD_MUTED_COLOR), font=get_font(11))

    # Ноги парлея
    y = 55
    draw.line([(24, y), (W - 24, y)], fill=(50, 60, 70), width=1)
    y += 10

    for i, leg in enumerate(legs, 1):
        q       = leg.get("question", "")
        outcome = leg.get("outcome", "YES")
        price   = float(leg.get("price", 0))
        odds    = price_to_american_odds(price)
        color   = hex_to_rgb(CARD_ACCENT_GREEN) if outcome == "YES" \
                  else hex_to_rgb(CARD_ACCENT_RED)

        # Укоротить вопрос
        if len(q) > 45:
            q = q[:42] + "…"

        draw.text((24, y),
                  f"{i}. {q}",
                  fill=hex_to_rgb(CARD_TEXT_COLOR), font=get_font(13))
        y += 20
        draw.text((36, y),
                  f"   → {outcome}  {odds}",
                  fill=color, font=get_font(13, bold=True))
        y += 30
        draw.line([(24, y - 5), (W - 24, y - 5)], fill=(40, 50, 60), width=1)

    # Итоги
    y += 10
    total_odds_str = f"{total_odds:.2f}x"

    draw.text((24, y), "ПАРЛЕЙ КОЭФ.",
              fill=hex_to_rgb(CARD_MUTED_COLOR), font=get_font(13))
    draw.text((220, y), "СТАВКА",
              fill=hex_to_rgb(CARD_MUTED_COLOR), font=get_font(13))
    draw.text((400, y), "ВЫИГРЫШ",
              fill=hex_to_rgb(CARD_MUTED_COLOR), font=get_font(13))
    y += 20

    draw.text((24, y),  total_odds_str,
              fill=hex_to_rgb(CARD_ACCENT_GREEN), font=get_font(22, bold=True))
    draw.text((220, y), f"${amount:.2f}",
              fill=hex_to_rgb(CARD_TEXT_COLOR), font=get_font(22, bold=True))
    draw.text((400, y), f"${potential:.2f}",
              fill=hex_to_rgb(CARD_ACCENT_GREEN), font=get_font(22, bold=True))

    y += 45
    draw.line([(24, y), (W - 24, y)], fill=(50, 60, 70), width=1)
    y += 10
    footer = f"@{username} · t.me/PolymarketMAMA_Bot" if username else "t.me/PolymarketMAMA_Bot"
    draw.text((24, y), footer,
              fill=hex_to_rgb(CARD_MUTED_COLOR), font=get_font(11))

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
