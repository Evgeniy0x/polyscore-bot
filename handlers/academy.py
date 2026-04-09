# PolyScore — 🎓 Academy Module
# Уникальная система обучения: интерактивные уроки, квизы, прогресс, достижения.
# Вдохновлено лучшим из Duolingo, eToro, Robinhood — но лучше чем все они.

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import get_user, get_academy_progress, save_academy_progress


# ══════════════════════════════════════════════════════════════════════
# Структура уроков (5 модулей × 3 урока = 15 уроков)
# Каждый урок: теория → пример → квиз → XP
# ══════════════════════════════════════════════════════════════════════

MODULES = {
    "ru": [
        {
            "id": "basics",
            "emoji": "📖",
            "title": "Основы предсказаний",
            "desc": "Что такое prediction market и как это работает",
            "xp": 50,
            "lessons": [
                {
                    "id": "what_is",
                    "title": "Что такое Polymarket?",
                    "emoji": "🌍",
                    "text": (
                        "🌍 <b>Что такое prediction market?</b>\n\n"
                        "Представь, что ты смотришь матч НБА.\n"
                        "Ты уверен, что Lakers победят — на 70%.\n\n"
                        "На Polymarket ты можешь <b>купить YES по цене $0.70</b>.\n"
                        "Если Lakers побеждают — ты получаешь <b>$1.00 за каждую акцию</b>.\n"
                        "Прибыль: <b>+$0.30 (43%) на каждый доллар</b>.\n\n"
                        "❌ Если проигрывают — акция стоит $0.00.\n\n"
                        "💡 Ключевая идея: цена = вероятность по мнению рынка.\n"
                        "YES за $0.70 = «рынок думает, вероятность 70%».\n\n"
                        "Если ты умнее рынка — ты зарабатываешь."
                    ),
                    "quiz": {
                        "q": "Lakers YES стоит $0.45. Что это значит?",
                        "options": [
                            ("Рынок считает вероятность победы Lakers 45%", True),
                            ("Lakers проиграют с вероятностью 45%", False),
                            ("Максимальная ставка — $45", False),
                        ]
                    },
                    "xp": 15,
                },
                {
                    "id": "prices",
                    "title": "Как читать цены",
                    "emoji": "💹",
                    "text": (
                        "💹 <b>Как читать цены на рынке</b>\n\n"
                        "Каждый рынок имеет два исхода: <b>YES и NO</b>.\n"
                        "Цены всегда в сумме дают ~$1.00.\n\n"
                        "<b>Пример: «Канзас-Сити выиграет Супербоул?»</b>\n"
                        "• YES: $0.62 → рынок даёт 62% вероятность\n"
                        "• NO: $0.38 → вероятность «нет» = 38%\n\n"
                        "📊 <b>Как читать импульс:</b>\n"
                        "Если YES вырос с $0.50 → $0.70 за час — "
                        "значит кто-то крупный покупает YES.\n"
                        "Это <b>информация</b> — может, инсайдер знает результат?\n\n"
                        "🤖 Именно поэтому AI PolyScore следит за движением цен — "
                        "чтобы находить такие сигналы для тебя."
                    ),
                    "quiz": {
                        "q": "YES = $0.80, NO = $0.20. Что выгоднее купить, если ты считаешь вероятность YES = 90%?",
                        "options": [
                            ("YES — рынок недооценивает вероятность", True),
                            ("NO — дешевле стоит", False),
                            ("Нечего покупать, всё правильно оценено", False),
                        ]
                    },
                    "xp": 15,
                },
                {
                    "id": "edge",
                    "title": "Что такое Edge",
                    "emoji": "⚡",
                    "text": (
                        "⚡ <b>Edge — твоё преимущество перед рынком</b>\n\n"
                        "Edge = разница между ТВОЕЙ оценкой вероятности и ЦЕНОЙ рынка.\n\n"
                        "<b>Пример:</b>\n"
                        "• Рынок: Lakers YES = $0.55 (55% вероятность)\n"
                        "• Ты смотришь статистику: Lakers выигрывали 72% последних матчей дома\n"
                        "• Твоя оценка: 72%\n"
                        "• <b>Edge = 72% - 55% = +17%</b> ← ПОКУПАЙ YES!\n\n"
                        "📌 Правило:\n"
                        "• Edge > +5% → сделка выгодна\n"
                        "• Edge < 0% → рынок знает больше тебя\n"
                        "• Edge > +15% → редкая возможность, действуй быстро\n\n"
                        "🤖 PolyScore AI считает Edge автоматически для каждого рынка."
                    ),
                    "quiz": {
                        "q": "Рынок: YES = $0.40. Твоя оценка вероятности = 60%. Каков твой Edge?",
                        "options": [
                            ("+20% — покупай YES!", True),
                            ("-20% — покупай NO!", False),
                            ("0% — рынок прав", False),
                        ]
                    },
                    "xp": 20,
                },
            ]
        },
        {
            "id": "strategy",
            "emoji": "🎯",
            "title": "Торговые стратегии",
            "desc": "Kelly Criterion, банкролл-менеджмент, диверсификация",
            "xp": 75,
            "lessons": [
                {
                    "id": "bankroll",
                    "title": "Управление банкроллом",
                    "emoji": "💰",
                    "text": (
                        "💰 <b>Управление банкроллом — правило №1</b>\n\n"
                        "Даже лучшие аналитики проигрывают серии ставок.\n"
                        "Управление банкроллом спасает от полного слива.\n\n"
                        "<b>Правило 1-5%:</b>\n"
                        "Никогда не ставь больше 1-5% от капитала на одну ставку.\n\n"
                        "<b>Пример:</b>\n"
                        "• Капитал: $500\n"
                        "• Максимум на ставку: $5-$25\n"
                        "• Если ставишь $50 (10%) и проигрываешь 5 подряд → -$250 (50% капитала)\n"
                        "• Если ставишь $10 (2%) — те же 5 проигрышей → -$50 (10%)\n\n"
                        "🧮 <b>Формула Kelly Criterion (для профи):</b>\n"
                        "f = (p × b - q) / b\n"
                        "где p = вероятность победы, q = 1-p, b = коэффициент\n\n"
                        "PolyScore AI учитывает Kelly при расчёте размера ставки."
                    ),
                    "quiz": {
                        "q": "Твой баланс $200. Следуя правилу 2%, сколько максимум ставить?",
                        "options": [
                            ("$4", True),
                            ("$20", False),
                            ("$50", False),
                        ]
                    },
                    "xp": 20,
                },
                {
                    "id": "diversify",
                    "title": "Диверсификация",
                    "emoji": "🌐",
                    "text": (
                        "🌐 <b>Диверсификация — не клади яйца в одну корзину</b>\n\n"
                        "Топ-трейдеры Polymarket ставят на <b>10-20 разных рынков</b> одновременно.\n\n"
                        "<b>Почему?</b>\n"
                        "Даже точный анализ не гарантирует результат.\n"
                        "Но при 15 ставках с Edge +10% — статистика работает на тебя.\n\n"
                        "<b>Плохо:</b> $100 на один матч НБА\n"
                        "<b>Хорошо:</b>\n"
                        "• $20 на НБА\n"
                        "• $20 на НХЛ\n"
                        "• $20 на UFC\n"
                        "• $20 на политику\n"
                        "• $20 на крипто-рынок\n\n"
                        "📊 Корреляция важна: НБА и НХЛ независимы.\n"
                        "НБА и «выиграет ли конкретный игрок» — сильно коррелируют."
                    ),
                    "quiz": {
                        "q": "Зачем диверсифицировать ставки?",
                        "options": [
                            ("Снизить дисперсию и использовать статистику", True),
                            ("Чтобы всегда выигрывать", False),
                            ("Это требование Polymarket", False),
                        ]
                    },
                    "xp": 25,
                },
                {
                    "id": "parlays",
                    "title": "Когда использовать парлеи",
                    "emoji": "🎰",
                    "text": (
                        "🎰 <b>Парлеи: большая прибыль, большой риск</b>\n\n"
                        "Парлей = комбинация нескольких ставок.\n"
                        "Все исходы должны сыграть — иначе проигрываешь всё.\n\n"
                        "<b>Пример парлея × 3:</b>\n"
                        "• Lakers WIN: YES $0.65\n"
                        "• Golden State WIN: YES $0.60\n"
                        "• Celtics WIN: YES $0.70\n"
                        "• Итог: $0.65 × $0.60 × $0.70 ≈ $0.27\n"
                        "• Ставишь $10 → выигрыш $37 (370%!) если все 3 угадал\n\n"
                        "⚠️ <b>Правило парлеев:</b>\n"
                        "• Максимум 2-3 ноги в парлее\n"
                        "• Максимум 1-2% банкролла на парлей\n"
                        "• Используй только рынки с высоким Edge\n\n"
                        "💡 PolyScore строит парлеи только из топ AI-рекомендаций."
                    ),
                    "quiz": {
                        "q": "Парлей из 3 ног по $0.70 каждая. Какова вероятность победы?",
                        "options": [
                            ("34% (0.7 × 0.7 × 0.7)", True),
                            ("70% (среднее)", False),
                            ("210% (сумма)", False),
                        ]
                    },
                    "xp": 30,
                },
            ]
        },
        {
            "id": "polymarket",
            "emoji": "🔮",
            "title": "Polymarket Pro",
            "desc": "Ликвидность, slippage, ордера, крупные игроки",
            "xp": 100,
            "lessons": [
                {
                    "id": "liquidity",
                    "title": "Ликвидность рынка",
                    "emoji": "💧",
                    "text": (
                        "💧 <b>Ликвидность — насколько легко купить/продать</b>\n\n"
                        "Высокая ликвидность = можно купить $1000 без изменения цены.\n"
                        "Низкая ликвидность = покупка $100 уже сдвигает цену.\n\n"
                        "<b>Как проверить ликвидность:</b>\n"
                        "• Объём за 24ч > $10K → хорошая ликвидность\n"
                        "• Объём за 24ч < $1K → осторожно, slippage!\n\n"
                        "<b>Что такое slippage:</b>\n"
                        "Ты видишь цену YES = $0.60.\n"
                        "Но когда покупаешь на $500 — исполняется по $0.65.\n"
                        "Разница $0.05 × 500 = $25 потерь из-за slippage.\n\n"
                        "✅ PolyScore показывает объём рынка и предупреждает\n"
                        "о низкой ликвидности перед ставкой."
                    ),
                    "quiz": {
                        "q": "Объём рынка за 24ч = $500. Что ты сделаешь?",
                        "options": [
                            ("Поставлю маленькую сумму или поищу другой рынок", True),
                            ("Поставлю $1000 — рынок работает", False),
                            ("Объём не важен", False),
                        ]
                    },
                    "xp": 30,
                },
                {
                    "id": "whales",
                    "title": "Следи за крупными игроками",
                    "emoji": "🐋",
                    "text": (
                        "🐋 <b>Whale watching — следи за умными деньгами</b>\n\n"
                        "На Polymarket все транзакции публичны.\n"
                        "Топ-трейдеры с ROI > 50% — это источник сигналов.\n\n"
                        "<b>Сигналы китов:</b>\n"
                        "• Крупная покупка YES на «тихом» рынке → инсайдер?\n"
                        "• Топ-трейдер купил YES за 48ч до события → следуй\n"
                        "• Массовый выход из рынка → переоценивай позицию\n\n"
                        "<b>Как использовать Copy Trading в PolyScore:</b>\n"
                        "1. Найди топ-трейдера (🏆 Топ игроки)\n"
                        "2. Посмотри его историю и ROI\n"
                        "3. Установи % копирования (5-20%)\n"
                        "4. Бот автоматически копирует его сделки\n\n"
                        "⚠️ Диверсифицируй: копируй 3-5 разных трейдеров."
                    ),
                    "quiz": {
                        "q": "Топ-трейдер с ROI 80% купил YES. Что лучше сделать?",
                        "options": [
                            ("Изучить рынок и рассмотреть небольшую позицию", True),
                            ("Немедленно вложить весь банкролл", False),
                            ("Игнорировать — это манипуляция", False),
                        ]
                    },
                    "xp": 35,
                },
                {
                    "id": "advanced",
                    "title": "Продвинутые стратегии",
                    "emoji": "🚀",
                    "text": (
                        "🚀 <b>Продвинутые стратегии профессионалов</b>\n\n"
                        "<b>1. Pre-event decay (временной распад)</b>\n"
                        "За 1-2ч до события YES и NO цены сходятся к 50/50.\n"
                        "Покупай явных фаворитов заранее, не в последний момент.\n\n"
                        "<b>2. Hedging (хеджирование)</b>\n"
                        "Купил YES за $0.40, вырос до $0.80.\n"
                        "Продай часть позиции — зафиксируй прибыль.\n"
                        "Или купи NO как страховку.\n\n"
                        "<b>3. Market Making</b>\n"
                        "Выставляй ордера одновременно на YES и NO.\n"
                        "Зарабатывай на спреде bid/ask.\n"
                        "Подходит для высоколиквидных рынков.\n\n"
                        "<b>4. Арбитраж</b>\n"
                        "YES + NO ≠ $1.00 → арбитражная возможность.\n"
                        "Купи оба — гарантированная прибыль без риска.\n\n"
                        "💎 Эти стратегии используют топ-1% трейдеров."
                    ),
                    "quiz": {
                        "q": "YES = $0.45, NO = $0.45. Что делать?",
                        "options": [
                            ("Купить оба — арбитраж! YES+NO=$0.90, выплата $1.00", True),
                            ("Купить YES — он дешевле", False),
                            ("Рынок недооценён — ждать", False),
                        ]
                    },
                    "xp": 35,
                },
            ]
        },
        {
            "id": "psychology",
            "emoji": "🧠",
            "title": "Психология трейдера",
            "desc": "Ошибки новичков, bias, дисциплина",
            "xp": 75,
            "lessons": [
                {
                    "id": "biases",
                    "title": "Когнитивные ловушки",
                    "emoji": "🪤",
                    "text": (
                        "🪤 <b>Топ-5 ловушек трейдера на Polymarket</b>\n\n"
                        "<b>1. Confirmation bias</b>\n"
                        "Ищешь только информацию, которая подтверждает твою ставку.\n"
                        "Решение: читай аргументы обеих сторон.\n\n"
                        "<b>2. Recency bias</b>\n"
                        "«Lakers вчера выиграли 3 подряд — обязательно выиграют».\n"
                        "Маленькая выборка не равна вероятности.\n\n"
                        "<b>3. Anchoring</b>\n"
                        "«YES стоил $0.80 — сейчас $0.50, значит дёшево».\n"
                        "Прошлая цена не определяет справедливую стоимость.\n\n"
                        "<b>4. FOMO (страх упустить)</b>\n"
                        "Цена резко выросла → «надо брать!».\n"
                        "На Polymarket резкий рост = меньше прибыли для тебя.\n\n"
                        "<b>5. Tilt (эмоциональная игра)</b>\n"
                        "После потерь делаешь импульсивные ставки.\n"
                        "Правило: после 2 проигрышей подряд — пауза 1 час."
                    ),
                    "quiz": {
                        "q": "Ты потерял 3 ставки подряд. Правильное действие?",
                        "options": [
                            ("Взять паузу и проанализировать стратегию", True),
                            ("Удвоить ставку — надо отыграться", False),
                            ("Переключиться на другой вид спорта сразу", False),
                        ]
                    },
                    "xp": 25,
                },
                {
                    "id": "discipline",
                    "title": "Дисциплина и система",
                    "emoji": "⚔️",
                    "text": (
                        "⚔️ <b>Система vs Интуиция</b>\n\n"
                        "Лучшие трейдеры Polymarket используют СИСТЕМУ, не интуицию.\n\n"
                        "<b>Пример системы:</b>\n"
                        "1. Ставлю только если Edge > +8%\n"
                        "2. Максимум 3% банкролла на ставку\n"
                        "3. Минимум 5 рынков одновременно\n"
                        "4. Не ставлю на последние 2ч до события\n"
                        "5. Веду дневник ставок (P&L)\n\n"
                        "<b>Дневник трейдера:</b>\n"
                        "Записывай каждую ставку:\n"
                        "• Почему поставил (тезис)\n"
                        "• Результат\n"
                        "• Чему научился\n\n"
                        "📊 PolyScore автоматически ведёт твой дневник ставок\n"
                        "и считает ROI, win rate, средний Edge."
                    ),
                    "quiz": {
                        "q": "Ты нашёл рынок с Edge +3%. Ставить?",
                        "options": [
                            ("Нет — Edge слишком маленький (правило >8%)", True),
                            ("Да — любой положительный Edge выгоден", False),
                            ("Да, но только крупную сумму", False),
                        ]
                    },
                    "xp": 25,
                },
                {
                    "id": "mindset",
                    "title": "Мышление победителя",
                    "emoji": "🏆",
                    "text": (
                        "🏆 <b>Мышление топ-трейдера Polymarket</b>\n\n"
                        "<b>Думай в вероятностях, не в исходах</b>\n"
                        "«Я поставил правильно, но потерял» — это нормально.\n"
                        "При Edge +15% ты всё равно проигрываешь 45% сделок.\n"
                        "Оценивай процесс, не результат одной ставки.\n\n"
                        "<b>Долгосрочная игра</b>\n"
                        "100 ставок с Edge +10% → ожидаемая прибыль +10% на банкролл.\n"
                        "Но на дистанции 10-20 ставок — возможны любые результаты.\n\n"
                        "<b>Учись у рынка</b>\n"
                        "Если рынок не согласен с тобой — спроси себя:\n"
                        "«Что знают остальные игроки, чего не знаю я?\"\n\n"
                        "🎯 <b>Цель не «угадать» — а иметь систематическое преимущество.</b>"
                    ),
                    "quiz": {
                        "q": "Ты поставил правильно (Edge +20%), но проиграл. Что это значит?",
                        "options": [
                            ("Нормально — дисперсия. Продолжай систему.", True),
                            ("Система не работает — менять стратегию", False),
                            ("Нужно было ставить больше", False),
                        ]
                    },
                    "xp": 25,
                },
            ]
        },
        {
            "id": "practice",
            "emoji": "🏅",
            "title": "Практика и достижения",
            "desc": "Разбор реальных сделок и финальный тест",
            "xp": 100,
            "lessons": [
                {
                    "id": "case1",
                    "title": "Разбор сделки: НБА",
                    "emoji": "⚾",
                    "text": (
                        "⚾ <b>Разбор реальной сделки — Lakers vs Nuggets</b>\n\n"
                        "<b>Ситуация:</b>\n"
                        "За 3ч до матча: Lakers YES = $0.42\n"
                        "Официальная статистика: Lakers дома выигрывают 61% матчей.\n"
                        "Дополнительно: LeBron James здоров, Nuggets без Jokic (травма).\n\n"
                        "<b>Анализ:</b>\n"
                        "• Базовая ставка: 61% (по статистике дома)\n"
                        "• Поправка на отсутствие Jokic: +8%\n"
                        "• Итоговая оценка: ~69%\n"
                        "• Рыночная цена: 42%\n"
                        "• <b>Edge = 69% - 42% = +27%</b> ← редкая возможность!\n\n"
                        "<b>Действие:</b> Купить YES на 3% банкролла.\n\n"
                        "📈 Результат: Lakers победили 118-105.\n"
                        "YES с $0.42 → $1.00 = прибыль +138%."
                    ),
                    "quiz": {
                        "q": "В этой ситуации Edge = +27%. Сколько % банкролла ставить?",
                        "options": [
                            ("3-5% — высокий Edge, но дисциплина важнее", True),
                            ("50% — такой Edge бывает редко!", False),
                            ("0% — слишком рискованно", False),
                        ]
                    },
                    "xp": 30,
                },
                {
                    "id": "case2",
                    "title": "Разбор ошибки: FOMO",
                    "emoji": "📉",
                    "text": (
                        "📉 <b>Разбор ошибки — как потерять на хорошем рынке</b>\n\n"
                        "<b>Ситуация:</b>\n"
                        "UFC: Исраэль Адесанья YES = $0.35\n"
                        "За 30 минут до боя цена выросла до $0.70.\n"
                        "«Кто-то знает что-то — надо брать!» — FOMO.\n\n"
                        "<b>Ошибка:</b>\n"
                        "Купил YES за $0.70 на $200 (20% банкролла).\n\n"
                        "<b>Что случилось:</b>\n"
                        "• При $0.35 Edge был +15% (ожидаемая вероятность 50%)\n"
                        "• При $0.70 Edge = -20% (переоценен!)\n"
                        "• Исраэль проиграл. YES → $0.00.\n"
                        "• Потеря: $200 (20% банкролла).\n\n"
                        "<b>Урок:</b>\n"
                        "1. Не гонись за уже выросшей ценой\n"
                        "2. Рассчитывай Edge, а не следуй толпе\n"
                        "3. Никогда 20% банкролла на одну ставку!"
                    ),
                    "quiz": {
                        "q": "YES вырос с $0.35 до $0.75 за час. Что делать?",
                        "options": [
                            ("Пересчитать Edge заново — он мог стать отрицательным", True),
                            ("Купить — рынок дал сигнал", False),
                            ("Продать NO — обратная игра", False),
                        ]
                    },
                    "xp": 35,
                },
                {
                    "id": "final",
                    "title": "Финальный тест 🏆",
                    "emoji": "🎓",
                    "text": (
                        "🎓 <b>Финальный тест — ты готов к реальной игре!</b>\n\n"
                        "Поздравляем! Ты прошёл все уроки PolyScore Academy.\n\n"
                        "<b>Что ты знаешь теперь:</b>\n"
                        "✅ Как работают prediction markets\n"
                        "✅ Как читать и считать Edge\n"
                        "✅ Управление банкроллом (Kelly Criterion)\n"
                        "✅ Диверсификация и когда использовать парлеи\n"
                        "✅ Как читать движение ликвидности\n"
                        "✅ Как избежать когнитивных ловушек\n"
                        "✅ Мышление профессионального трейдера\n\n"
                        "🏆 <b>Ты получаешь звание «PolyScore Analyst»!</b>\n\n"
                        "Теперь нажми «Начать торговать» и применяй знания на практике.\n"
                        "PolyScore AI будет помогать тебе каждый день."
                    ),
                    "quiz": {
                        "q": "Главное правило управления банкроллом?",
                        "options": [
                            ("Не более 1-5% от капитала на одну ставку", True),
                            ("Всегда ставить фиксированную сумму $10", False),
                            ("Ставить больше на высокий Edge", False),
                        ]
                    },
                    "xp": 35,
                },
            ]
        },
    ]
}

MODULES["en"] = [
    {
        "id": "basics",
        "emoji": "📖",
        "title": "Prediction Basics",
        "desc": "What is a prediction market and how it works",
        "xp": 50,
        "lessons": [
            {
                "id": "what_is",
                "title": "What is Polymarket?",
                "emoji": "🌍",
                "text": (
                    "🌍 <b>What is a prediction market?</b>\n\n"
                    "Imagine you're watching an NBA game.\n"
                    "You're 70% sure the Lakers will win.\n\n"
                    "On Polymarket you can <b>buy YES at $0.70</b>.\n"
                    "If Lakers win — you get <b>$1.00 per share</b>.\n"
                    "Profit: <b>+$0.30 (43%) per dollar</b>.\n\n"
                    "❌ If they lose — the share is worth $0.00.\n\n"
                    "💡 Key idea: price = market probability.\n"
                    "YES at $0.70 = \"market thinks 70% chance\".\n\n"
                    "If you're smarter than the market — you profit."
                ),
                "quiz": {
                    "q": "Lakers YES is at $0.45. What does this mean?",
                    "options": [
                        ("Market thinks Lakers have a 45% chance of winning", True),
                        ("Lakers will lose with 45% probability", False),
                        ("Maximum bet is $45", False),
                    ]
                },
                "xp": 15,
            },
            {
                "id": "prices",
                "title": "How to Read Prices",
                "emoji": "💹",
                "text": (
                    "💹 <b>How to read market prices</b>\n\n"
                    "Every market has two outcomes: <b>YES and NO</b>.\n"
                    "Prices always add up to ~$1.00.\n\n"
                    "<b>Example: \"Will Kansas City win the Super Bowl?\"</b>\n"
                    "• YES: $0.62 → market gives 62% probability\n"
                    "• NO: $0.38 → probability of \"no\" = 38%\n\n"
                    "📊 <b>Reading momentum:</b>\n"
                    "If YES jumped from $0.50 → $0.70 in one hour —\n"
                    "someone big is buying YES.\n"
                    "That's <b>information</b> — maybe an insider knows the result?\n\n"
                    "🤖 That's why PolyScore AI tracks price movements —\n"
                    "to find these signals for you."
                ),
                "quiz": {
                    "q": "YES = $0.80, NO = $0.20. What's better to buy if you think YES probability = 90%?",
                    "options": [
                        ("YES — the market is underpricing the probability", True),
                        ("NO — it's cheaper", False),
                        ("Nothing — everything is fairly priced", False),
                    ]
                },
                "xp": 15,
            },
            {
                "id": "edge",
                "title": "What is Edge",
                "emoji": "⚡",
                "text": (
                    "⚡ <b>Edge — your advantage over the market</b>\n\n"
                    "Edge = difference between YOUR probability estimate and the MARKET PRICE.\n\n"
                    "<b>Example:</b>\n"
                    "• Market: Lakers YES = $0.55 (55% probability)\n"
                    "• You check stats: Lakers won 72% of home games recently\n"
                    "• Your estimate: 72%\n"
                    "• <b>Edge = 72% - 55% = +17%</b> ← BUY YES!\n\n"
                    "📌 Rules:\n"
                    "• Edge > +5% → trade is profitable\n"
                    "• Edge < 0% → market knows more than you\n"
                    "• Edge > +15% → rare opportunity, act fast\n\n"
                    "🤖 PolyScore AI calculates Edge automatically for every market."
                ),
                "quiz": {
                    "q": "Market: YES = $0.40. Your probability estimate = 60%. What is your Edge?",
                    "options": [
                        ("+20% — buy YES!", True),
                        ("-20% — buy NO!", False),
                        ("0% — market is right", False),
                    ]
                },
                "xp": 20,
            },
        ]
    },
    {
        "id": "strategy",
        "emoji": "🎯",
        "title": "Trading Strategies",
        "desc": "Kelly Criterion, bankroll management, diversification",
        "xp": 75,
        "lessons": [
            {
                "id": "bankroll",
                "title": "Bankroll Management",
                "emoji": "💰",
                "text": (
                    "💰 <b>Bankroll management — rule #1</b>\n\n"
                    "Even the best analysts hit losing streaks.\n"
                    "Bankroll management saves you from going bust.\n\n"
                    "<b>The 1-5% rule:</b>\n"
                    "Never bet more than 1-5% of your capital on a single bet.\n\n"
                    "<b>Example:</b>\n"
                    "• Capital: $500\n"
                    "• Max per bet: $5-$25\n"
                    "• If you bet $50 (10%) and lose 5 in a row → -$250 (50% of capital)\n"
                    "• If you bet $10 (2%) — same 5 losses → -$50 (10%)\n\n"
                    "🧮 <b>Kelly Criterion formula (for pros):</b>\n"
                    "f = (p × b - q) / b\n"
                    "where p = win probability, q = 1-p, b = odds\n\n"
                    "PolyScore AI uses Kelly when calculating bet sizes."
                ),
                "quiz": {
                    "q": "Your balance is $200. Following the 2% rule, what is the maximum bet?",
                    "options": [
                        ("$4", True),
                        ("$20", False),
                        ("$50", False),
                    ]
                },
                "xp": 20,
            },
            {
                "id": "diversify",
                "title": "Diversification",
                "emoji": "🌐",
                "text": (
                    "🌐 <b>Diversification — don't put all eggs in one basket</b>\n\n"
                    "Top Polymarket traders bet on <b>10-20 different markets</b> at once.\n\n"
                    "<b>Why?</b>\n"
                    "Even accurate analysis doesn't guarantee results.\n"
                    "But with 15 bets each with +10% Edge — statistics work for you.\n\n"
                    "<b>Bad:</b> $100 on one NBA game\n"
                    "<b>Good:</b>\n"
                    "• $20 on NBA\n"
                    "• $20 on NHL\n"
                    "• $20 on UFC\n"
                    "• $20 on politics\n"
                    "• $20 on crypto\n\n"
                    "📊 Correlation matters: NBA and NHL are independent.\n"
                    "NBA and \"will a specific player win\" — highly correlated."
                ),
                "quiz": {
                    "q": "Why diversify bets?",
                    "options": [
                        ("To reduce variance and use statistics", True),
                        ("To always win", False),
                        ("It's a Polymarket requirement", False),
                    ]
                },
                "xp": 25,
            },
            {
                "id": "parlays",
                "title": "When to Use Parlays",
                "emoji": "🎰",
                "text": (
                    "🎰 <b>Parlays: big profit, big risk</b>\n\n"
                    "A parlay = combination of multiple bets.\n"
                    "All outcomes must hit — otherwise you lose everything.\n\n"
                    "<b>3-leg parlay example:</b>\n"
                    "• Lakers WIN: YES $0.65\n"
                    "• Golden State WIN: YES $0.60\n"
                    "• Celtics WIN: YES $0.70\n"
                    "• Combined: $0.65 × $0.60 × $0.70 ≈ $0.27\n"
                    "• Bet $10 → win $37 (370%!) if all 3 hit\n\n"
                    "⚠️ <b>Parlay rules:</b>\n"
                    "• Max 2-3 legs in a parlay\n"
                    "• Max 1-2% of bankroll on a parlay\n"
                    "• Only use markets with high Edge\n\n"
                    "💡 PolyScore builds parlays only from top AI recommendations."
                ),
                "quiz": {
                    "q": "A 3-leg parlay at $0.70 each. What is the win probability?",
                    "options": [
                        ("34% (0.7 × 0.7 × 0.7)", True),
                        ("70% (average)", False),
                        ("210% (sum)", False),
                    ]
                },
                "xp": 30,
            },
        ]
    },
    {
        "id": "polymarket",
        "emoji": "🔮",
        "title": "Polymarket Pro",
        "desc": "Liquidity, slippage, orders, whales",
        "xp": 100,
        "lessons": [
            {
                "id": "liquidity",
                "title": "Market Liquidity",
                "emoji": "💧",
                "text": (
                    "💧 <b>Liquidity — how easy it is to buy/sell</b>\n\n"
                    "High liquidity = you can buy $1000 without moving the price.\n"
                    "Low liquidity = buying $100 already shifts the price.\n\n"
                    "<b>How to check liquidity:</b>\n"
                    "• 24h volume > $10K → good liquidity\n"
                    "• 24h volume < $1K → caution, slippage!\n\n"
                    "<b>What is slippage:</b>\n"
                    "You see YES = $0.60.\n"
                    "But when you buy $500 — it executes at $0.65.\n"
                    "Difference: $0.05 × 500 = $25 lost to slippage.\n\n"
                    "✅ PolyScore shows market volume and warns\n"
                    "about low liquidity before you bet."
                ),
                "quiz": {
                    "q": "24h market volume = $500. What do you do?",
                    "options": [
                        ("Bet a small amount or find another market", True),
                        ("Bet $1000 — the market works", False),
                        ("Volume doesn't matter", False),
                    ]
                },
                "xp": 30,
            },
            {
                "id": "whales",
                "title": "Watch the Whales",
                "emoji": "🐋",
                "text": (
                    "🐋 <b>Whale watching — follow the smart money</b>\n\n"
                    "On Polymarket all transactions are public.\n"
                    "Top traders with ROI > 50% are signal sources.\n\n"
                    "<b>Whale signals:</b>\n"
                    "• Large YES buy on a quiet market → insider?\n"
                    "• Top trader bought YES 48h before event → follow\n"
                    "• Mass exit from a market → reassess your position\n\n"
                    "<b>How to use Copy Trading in PolyScore:</b>\n"
                    "1. Find a top trader (🏆 Top Players)\n"
                    "2. Check their history and ROI\n"
                    "3. Set copy % (5-20%)\n"
                    "4. Bot automatically copies their trades\n\n"
                    "⚠️ Diversify: copy 3-5 different traders."
                ),
                "quiz": {
                    "q": "A top trader with 80% ROI bought YES. What's the best move?",
                    "options": [
                        ("Study the market and consider a small position", True),
                        ("Put in your entire bankroll immediately", False),
                        ("Ignore it — it's manipulation", False),
                    ]
                },
                "xp": 35,
            },
            {
                "id": "advanced",
                "title": "Advanced Strategies",
                "emoji": "🚀",
                "text": (
                    "🚀 <b>Advanced strategies used by professionals</b>\n\n"
                    "<b>1. Pre-event decay</b>\n"
                    "1-2h before an event, YES and NO prices converge to 50/50.\n"
                    "Buy clear favorites early, not at the last minute.\n\n"
                    "<b>2. Hedging</b>\n"
                    "Bought YES at $0.40, now at $0.80.\n"
                    "Sell part of your position — lock in profit.\n"
                    "Or buy NO as insurance.\n\n"
                    "<b>3. Market Making</b>\n"
                    "Place orders on both YES and NO simultaneously.\n"
                    "Earn on the bid/ask spread.\n"
                    "Works best in high-liquidity markets.\n\n"
                    "<b>4. Arbitrage</b>\n"
                    "YES + NO ≠ $1.00 → arbitrage opportunity.\n"
                    "Buy both — guaranteed profit with no risk.\n\n"
                    "💎 These strategies are used by the top 1% of traders."
                ),
                "quiz": {
                    "q": "YES = $0.45, NO = $0.45. What do you do?",
                    "options": [
                        ("Buy both — arbitrage! YES+NO=$0.90, payout $1.00", True),
                        ("Buy YES — it's cheaper", False),
                        ("Market is undervalued — wait", False),
                    ]
                },
                "xp": 35,
            },
        ]
    },
    {
        "id": "psychology",
        "emoji": "🧠",
        "title": "Trader Psychology",
        "desc": "Beginner mistakes, biases, discipline",
        "xp": 75,
        "lessons": [
            {
                "id": "biases",
                "title": "Cognitive Traps",
                "emoji": "🪤",
                "text": (
                    "🪤 <b>Top 5 trader traps on Polymarket</b>\n\n"
                    "<b>1. Confirmation bias</b>\n"
                    "You only look for info that confirms your bet.\n"
                    "Fix: read arguments from both sides.\n\n"
                    "<b>2. Recency bias</b>\n"
                    "\"Lakers won 3 in a row — they'll definitely win again\".\n"
                    "Small sample size ≠ probability.\n\n"
                    "<b>3. Anchoring</b>\n"
                    "\"YES was $0.80 — now $0.50, so it's cheap\".\n"
                    "Past price doesn't define fair value.\n\n"
                    "<b>4. FOMO (fear of missing out)</b>\n"
                    "Price jumped sharply → \"I have to buy!\".\n"
                    "On Polymarket a sharp rise = less profit for you.\n\n"
                    "<b>5. Tilt (emotional betting)</b>\n"
                    "After losses you make impulsive bets.\n"
                    "Rule: after 2 losses in a row — take a 1-hour break."
                ),
                "quiz": {
                    "q": "You lost 3 bets in a row. What's the right move?",
                    "options": [
                        ("Take a break and analyze your strategy", True),
                        ("Double the bet — need to recover", False),
                        ("Switch to a different sport immediately", False),
                    ]
                },
                "xp": 25,
            },
            {
                "id": "discipline",
                "title": "Discipline and System",
                "emoji": "⚔️",
                "text": (
                    "⚔️ <b>System vs Intuition</b>\n\n"
                    "The best Polymarket traders use a SYSTEM, not intuition.\n\n"
                    "<b>Example system:</b>\n"
                    "1. Only bet if Edge > +8%\n"
                    "2. Max 3% of bankroll per bet\n"
                    "3. Minimum 5 markets open at once\n"
                    "4. Don't bet in the last 2h before an event\n"
                    "5. Keep a betting journal (P&L)\n\n"
                    "<b>Trader journal:</b>\n"
                    "Record every bet:\n"
                    "• Why you bet (thesis)\n"
                    "• Result\n"
                    "• What you learned\n\n"
                    "📊 PolyScore automatically keeps your betting journal\n"
                    "and tracks ROI, win rate, average Edge."
                ),
                "quiz": {
                    "q": "You found a market with Edge +3%. Should you bet?",
                    "options": [
                        ("No — Edge is too small (rule: >8%)", True),
                        ("Yes — any positive Edge is profitable", False),
                        ("Yes, but only a large amount", False),
                    ]
                },
                "xp": 25,
            },
            {
                "id": "mindset",
                "title": "Winner Mindset",
                "emoji": "🏆",
                "text": (
                    "🏆 <b>Mindset of a top Polymarket trader</b>\n\n"
                    "<b>Think in probabilities, not outcomes</b>\n"
                    "\"I bet right but lost\" — that's normal.\n"
                    "With Edge +15% you still lose 45% of trades.\n"
                    "Judge the process, not the result of one bet.\n\n"
                    "<b>Long-term game</b>\n"
                    "100 bets with Edge +10% → expected profit +10% on bankroll.\n"
                    "But over 10-20 bets — any result is possible.\n\n"
                    "<b>Learn from the market</b>\n"
                    "If the market disagrees with you — ask yourself:\n"
                    "\"What do the other players know that I don't?\"\n\n"
                    "🎯 <b>The goal is not to \"guess\" — but to have systematic edge.</b>"
                ),
                "quiz": {
                    "q": "You bet correctly (Edge +20%) but lost. What does this mean?",
                    "options": [
                        ("Normal — variance. Keep the system going.", True),
                        ("System doesn't work — change strategy", False),
                        ("Should have bet more", False),
                    ]
                },
                "xp": 25,
            },
        ]
    },
    {
        "id": "practice",
        "emoji": "🏅",
        "title": "Practice & Achievements",
        "desc": "Real trade breakdowns and final test",
        "xp": 100,
        "lessons": [
            {
                "id": "case1",
                "title": "Trade Breakdown: NBA",
                "emoji": "⚾",
                "text": (
                    "⚾ <b>Real trade breakdown — Lakers vs Nuggets</b>\n\n"
                    "<b>Situation:</b>\n"
                    "3h before tipoff: Lakers YES = $0.42\n"
                    "Official stats: Lakers win 61% of home games.\n"
                    "Extra: LeBron James healthy, Nuggets without Jokic (injured).\n\n"
                    "<b>Analysis:</b>\n"
                    "• Base rate: 61% (home game stats)\n"
                    "• Jokic absence adjustment: +8%\n"
                    "• Final estimate: ~69%\n"
                    "• Market price: 42%\n"
                    "• <b>Edge = 69% - 42% = +27%</b> ← rare opportunity!\n\n"
                    "<b>Action:</b> Buy YES with 3% of bankroll.\n\n"
                    "📈 Result: Lakers won 118-105.\n"
                    "YES from $0.42 → $1.00 = profit +138%."
                ),
                "quiz": {
                    "q": "In this situation Edge = +27%. How much % of bankroll to bet?",
                    "options": [
                        ("3-5% — high Edge, but discipline matters more", True),
                        ("50% — such Edge is rare!", False),
                        ("0% — too risky", False),
                    ]
                },
                "xp": 30,
            },
            {
                "id": "case2",
                "title": "Mistake Breakdown: FOMO",
                "emoji": "📉",
                "text": (
                    "📉 <b>Mistake breakdown — how to lose on a good market</b>\n\n"
                    "<b>Situation:</b>\n"
                    "UFC: Israel Adesanya YES = $0.35\n"
                    "30 minutes before the fight, price jumped to $0.70.\n"
                    "\"Someone knows something — gotta buy!\" — FOMO.\n\n"
                    "<b>Mistake:</b>\n"
                    "Bought YES at $0.70 for $200 (20% of bankroll).\n\n"
                    "<b>What happened:</b>\n"
                    "• At $0.35 Edge was +15% (expected probability 50%)\n"
                    "• At $0.70 Edge = -20% (overpriced!)\n"
                    "• Israel lost. YES → $0.00.\n"
                    "• Loss: $200 (20% of bankroll).\n\n"
                    "<b>Lesson:</b>\n"
                    "1. Don't chase already-risen prices\n"
                    "2. Calculate Edge, don't follow the crowd\n"
                    "3. Never 20% of bankroll on one bet!"
                ),
                "quiz": {
                    "q": "YES jumped from $0.35 to $0.75 in one hour. What do you do?",
                    "options": [
                        ("Recalculate Edge — it may have turned negative", True),
                        ("Buy — the market gave a signal", False),
                        ("Sell NO — play the reverse", False),
                    ]
                },
                "xp": 35,
            },
            {
                "id": "final",
                "title": "Final Test 🏆",
                "emoji": "🎓",
                "text": (
                    "🎓 <b>Final Test — you're ready for the real game!</b>\n\n"
                    "Congratulations! You've completed all PolyScore Academy lessons.\n\n"
                    "<b>What you know now:</b>\n"
                    "✅ How prediction markets work\n"
                    "✅ How to read and calculate Edge\n"
                    "✅ Bankroll management (Kelly Criterion)\n"
                    "✅ Diversification and when to use parlays\n"
                    "✅ How to read liquidity movements\n"
                    "✅ How to avoid cognitive traps\n"
                    "✅ Professional trader mindset\n\n"
                    "🏆 <b>You've earned the title \"PolyScore Analyst\"!</b>\n\n"
                    "Now hit \"Start Trading\" and put your knowledge to work.\n"
                    "PolyScore AI will help you every day."
                ),
                "quiz": {
                    "q": "The main bankroll management rule?",
                    "options": [
                        ("No more than 1-5% of capital on a single bet", True),
                        ("Always bet a fixed $10 amount", False),
                        ("Bet more on high Edge", False),
                    ]
                },
                "xp": 35,
            },
        ]
    },
]

# Остальные языки — используем английскую версию как fallback
for _lang in ["es", "pt", "tr", "id", "zh", "ar", "fr", "de", "hi", "ja"]:
    MODULES[_lang] = MODULES["en"]


# ══════════════════════════════════════════════════════════════════════
# Достижения
# ══════════════════════════════════════════════════════════════════════

ACHIEVEMENTS = {
    "first_lesson": {"emoji": "🌱", "name": {"ru": "Первый шаг", "en": "First Step"}, "xp": 10},
    "module_1":     {"emoji": "📖", "name": {"ru": "Основы изучены", "en": "Basics Mastered"}, "xp": 50},
    "module_2":     {"emoji": "🎯", "name": {"ru": "Стратег", "en": "Strategist"}, "xp": 75},
    "module_3":     {"emoji": "🔮", "name": {"ru": "Pro Трейдер", "en": "Pro Trader"}, "xp": 100},
    "module_4":     {"emoji": "🧠", "name": {"ru": "Мастер психологии", "en": "Mind Master"}, "xp": 75},
    "all_modules":  {"emoji": "🎓", "name": {"ru": "PolyScore Analyst", "en": "PolyScore Analyst"}, "xp": 200},
    "perfect_quiz": {"emoji": "💯", "name": {"ru": "Идеальный результат", "en": "Perfect Score"}, "xp": 30},
    "streak_3":     {"emoji": "🔥", "name": {"ru": "3 урока подряд", "en": "3-lesson streak"}, "xp": 25},
}

XP_LEVELS = [
    (0,   "🥉 Новичок"),
    (100, "🥈 Любитель"),
    (250, "🥇 Продвинутый"),
    (500, "💎 Эксперт"),
    (800, "🌟 Мастер"),
    (1200,"👑 PolyScore Analyst"),
]


def get_level(xp: int, lang: str = "ru") -> str:
    level = XP_LEVELS[0][1]
    for req_xp, name in XP_LEVELS:
        if xp >= req_xp:
            level = name
    return level


def get_next_level_xp(xp: int) -> int:
    for req_xp, _ in XP_LEVELS:
        if xp < req_xp:
            return req_xp
    return XP_LEVELS[-1][0]


def progress_bar(current: int, total: int, length: int = 10) -> str:
    filled = int(length * current / max(total, 1))
    return "█" * filled + "░" * (length - filled)


# ══════════════════════════════════════════════════════════════════════
# Handlers
# ══════════════════════════════════════════════════════════════════════

async def cb_academy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Главный экран Академии."""
    query = update.callback_query
    await query.answer()

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    user_id = query.from_user.id

    progress = await get_academy_progress(user_id)
    total_xp = progress.get("total_xp", 0)
    completed = progress.get("completed_lessons", [])
    total_lessons = sum(len(m["lessons"]) for m in MODULES.get(lang, MODULES["ru"]))
    done_count = len(completed)

    level = get_level(total_xp, lang)
    next_xp = get_next_level_xp(total_xp)
    bar = progress_bar(total_xp, next_xp)

    if lang == "ru":
        text = (
            f"🎓 <b>PolyScore Academy</b>\n\n"
            f"{level}\n"
            f"XP: <b>{total_xp}</b> / {next_xp}  {bar}\n\n"
            f"📚 Пройдено уроков: <b>{done_count}/{total_lessons}</b>\n\n"
            f"Обучение — твоё главное конкурентное преимущество.\n"
            f"Топ-трейдеры Polymarket начинали с базы. Начни прямо сейчас."
        )
    else:
        text = (
            f"🎓 <b>PolyScore Academy</b>\n\n"
            f"{level}\n"
            f"XP: <b>{total_xp}</b> / {next_xp}  {bar}\n\n"
            f"📚 Lessons completed: <b>{done_count}/{total_lessons}</b>\n\n"
            f"Knowledge is your biggest edge.\n"
            f"Top Polymarket traders started with the basics. Start now."
        )

    modules = MODULES.get(lang, MODULES["ru"])
    keyboard = []
    for m in modules:
        module_lessons = [l["id"] for l in m["lessons"]]
        done_in_module = sum(1 for lid in module_lessons if f"{m['id']}:{lid}" in completed)
        total_in_module = len(module_lessons)
        status = "✅ " if done_in_module == total_in_module else (
            f"🔄 {done_in_module}/{total_in_module} " if done_in_module > 0 else ""
        )
        keyboard.append([InlineKeyboardButton(
            f"{m['emoji']} {status}{m['title']}  +{m['xp']}XP",
            callback_data=f"academy:module:{m['id']}"
        )])

    keyboard.append([
        InlineKeyboardButton("🏅 Достижения" if lang == "ru" else "🏅 Achievements",
                             callback_data="academy:achievements"),
        InlineKeyboardButton("📊 Мой прогресс" if lang == "ru" else "📊 My Progress",
                             callback_data="academy:stats"),
    ])
    keyboard.append([InlineKeyboardButton(
        "🔙 Назад" if lang == "ru" else "🔙 Back", callback_data="menu:main"
    )])

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_academy_module(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Экран модуля — список уроков."""
    query = update.callback_query
    await query.answer()

    module_id = query.data.split(":")[2]
    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    user_id = query.from_user.id

    progress = await get_academy_progress(user_id)
    completed = progress.get("completed_lessons", [])

    modules = MODULES.get(lang, MODULES["ru"])
    module = next((m for m in modules if m["id"] == module_id), None)
    if not module:
        await query.answer("Module not found", show_alert=True)
        return

    done_in_module = sum(1 for l in module["lessons"]
                         if f"{module_id}:{l['id']}" in completed)
    total_xp = progress.get("total_xp", 0)
    bar = progress_bar(done_in_module, len(module["lessons"]))

    if lang == "ru":
        text = (
            f"{module['emoji']} <b>{module['title']}</b>\n\n"
            f"{module['desc']}\n\n"
            f"Прогресс: {bar} {done_in_module}/{len(module['lessons'])} уроков\n"
            f"Награда за модуль: <b>+{module['xp']} XP</b>"
        )
    else:
        text = (
            f"{module['emoji']} <b>{module['title']}</b>\n\n"
            f"{module['desc']}\n\n"
            f"Progress: {bar} {done_in_module}/{len(module['lessons'])} lessons\n"
            f"Module reward: <b>+{module['xp']} XP</b>"
        )

    keyboard = []
    for i, lesson in enumerate(module["lessons"]):
        lesson_key = f"{module_id}:{lesson['id']}"
        status = "✅ " if lesson_key in completed else f"{i+1}. "
        keyboard.append([InlineKeyboardButton(
            f"{lesson['emoji']} {status}{lesson['title']}  +{lesson['xp']}XP",
            callback_data=f"academy:lesson:{module_id}:{lesson['id']}"
        )])

    keyboard.append([InlineKeyboardButton(
        "🔙 Назад" if lang == "ru" else "🔙 Back", callback_data="academy:main"
    )])

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_academy_lesson(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать урок (теория)."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    module_id  = parts[2]
    lesson_id  = parts[3]

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")

    modules = MODULES.get(lang, MODULES["ru"])
    module = next((m for m in modules if m["id"] == module_id), None)
    if not module:
        return
    lesson = next((l for l in module["lessons"] if l["id"] == lesson_id), None)
    if not lesson:
        return

    text = lesson["text"]
    keyboard = [
        [InlineKeyboardButton(
            f"✏️ Пройти тест  +{lesson['xp']}XP" if lang == "ru" else f"✏️ Take Quiz  +{lesson['xp']}XP",
            callback_data=f"academy:quiz:{module_id}:{lesson_id}:0"
        )],
        [InlineKeyboardButton(
            "🔙 К модулю" if lang == "ru" else "🔙 Back to module",
            callback_data=f"academy:module:{module_id}"
        )],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_academy_quiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать квиз-вопрос урока."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    module_id  = parts[2]
    lesson_id  = parts[3]
    # parts[4] = ответ (если уже выбрали), иначе "0" = показать вопрос

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    user_id = query.from_user.id

    modules = MODULES.get(lang, MODULES["ru"])
    module = next((m for m in modules if m["id"] == module_id), None)
    if not module:
        return
    lesson = next((l for l in module["lessons"] if l["id"] == lesson_id), None)
    if not lesson:
        return

    quiz = lesson["quiz"]

    if parts[4] == "0":
        # Показываем вопрос
        text = f"✏️ <b>Тест</b>\n\n{quiz['q']}" if lang == "ru" else f"✏️ <b>Quiz</b>\n\n{quiz['q']}"
        keyboard = []
        for i, (option_text, is_correct) in enumerate(quiz["options"]):
            keyboard.append([InlineKeyboardButton(
                f"{chr(65+i)}. {option_text}",
                callback_data=f"academy:quiz:{module_id}:{lesson_id}:{i+1}"
            )])
        keyboard.append([InlineKeyboardButton(
            "🔙 К уроку" if lang == "ru" else "🔙 Back to lesson",
            callback_data=f"academy:lesson:{module_id}:{lesson_id}"
        )])
    else:
        # Обрабатываем ответ
        answer_idx = int(parts[4]) - 1
        selected_text, is_correct = quiz["options"][answer_idx]

        if is_correct:
            # Правильный ответ — сохраняем прогресс
            lesson_key = f"{module_id}:{lesson_id}"
            progress = await get_academy_progress(user_id)
            completed = progress.get("completed_lessons", [])
            xp_gained = lesson["xp"]

            new_achievement = None
            if lesson_key not in completed:
                completed.append(lesson_key)
                new_xp = progress.get("total_xp", 0) + xp_gained

                # Проверяем достижения
                if len(completed) == 1:
                    new_achievement = "first_lesson"

                await save_academy_progress(user_id, completed, new_xp)
            else:
                new_xp = progress.get("total_xp", 0)
                xp_gained = 0

            xp_line = f"\n🎉 <b>+{xp_gained} XP!</b>" if xp_gained > 0 else "\n(уже пройдено)"
            ach_line = ""
            if new_achievement:
                a = ACHIEVEMENTS[new_achievement]
                ach_name = a["name"].get(lang, a["name"]["en"])
                ach_line = f"\n🏅 Достижение разблокировано: {a['emoji']} <b>{ach_name}</b>!"

            text = (
                f"✅ <b>Правильно!</b>\n\n"
                f"<i>{selected_text}</i>{xp_line}{ach_line}\n\n"
                f"Текущий XP: <b>{new_xp}</b>  {get_level(new_xp, lang)}"
            ) if lang == "ru" else (
                f"✅ <b>Correct!</b>\n\n"
                f"<i>{selected_text}</i>{xp_line}{ach_line}\n\n"
                f"Current XP: <b>{new_xp}</b>  {get_level(new_xp, lang)}"
            )
        else:
            correct_text = next(t for t, correct in quiz["options"] if correct)
            text = (
                f"❌ <b>Неправильно</b>\n\n"
                f"Твой ответ: <i>{selected_text}</i>\n\n"
                f"✅ Правильный ответ:\n<i>{correct_text}</i>\n\n"
                f"Не сдавайся! Попробуй ещё раз."
            ) if lang == "ru" else (
                f"❌ <b>Incorrect</b>\n\n"
                f"Your answer: <i>{selected_text}</i>\n\n"
                f"✅ Correct answer:\n<i>{correct_text}</i>\n\n"
                f"Don't give up! Try again."
            )

        keyboard = []
        if is_correct:
            keyboard.append([InlineKeyboardButton(
                f"▶️ Следующий урок" if lang == "ru" else "▶️ Next Lesson",
                callback_data=f"academy:module:{module_id}"
            )])
            keyboard.append([InlineKeyboardButton(
                "🎯 К рынкам" if lang == "ru" else "🎯 Browse Markets",
                callback_data="cat:markets"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                "🔄 Попробовать снова" if lang == "ru" else "🔄 Try Again",
                callback_data=f"academy:quiz:{module_id}:{lesson_id}:0"
            )])
            keyboard.append([InlineKeyboardButton(
                "📖 Перечитать урок" if lang == "ru" else "📖 Re-read Lesson",
                callback_data=f"academy:lesson:{module_id}:{lesson_id}"
            )])

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_academy_achievements(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Экран достижений."""
    query = update.callback_query
    await query.answer()

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    user_id = query.from_user.id

    progress = await get_academy_progress(user_id)
    completed = progress.get("completed_lessons", [])
    total_xp = progress.get("total_xp", 0)
    earned_achievements = progress.get("achievements", [])

    lines = ["🏅 <b>Достижения</b>\n" if lang == "ru" else "🏅 <b>Achievements</b>\n"]
    for ach_id, ach in ACHIEVEMENTS.items():
        name = ach["name"].get(lang, ach["name"]["en"])
        if ach_id in earned_achievements:
            lines.append(f"{ach['emoji']} <b>{name}</b> ✅  +{ach['xp']}XP")
        else:
            lines.append(f"🔒 {name}  +{ach['xp']}XP")

    lines.append(f"\n🌟 Всего XP: <b>{total_xp}</b>  {get_level(total_xp, lang)}"
                 if lang == "ru" else
                 f"\n🌟 Total XP: <b>{total_xp}</b>  {get_level(total_xp, lang)}")

    keyboard = [[InlineKeyboardButton(
        "🔙 Назад" if lang == "ru" else "🔙 Back", callback_data="academy:main"
    )]]

    await query.edit_message_text(
        "\n".join(lines), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_academy_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Статистика прогресса."""
    query = update.callback_query
    await query.answer()

    user = await get_user(query.from_user.id)
    lang = (user or {}).get("language", "ru")
    user_id = query.from_user.id

    progress = await get_academy_progress(user_id)
    total_xp = progress.get("total_xp", 0)
    completed = progress.get("completed_lessons", [])

    modules = MODULES.get(lang, MODULES["ru"])
    total_lessons = sum(len(m["lessons"]) for m in modules)
    done_count = len(completed)
    pct = int(done_count / max(total_lessons, 1) * 100)
    bar = progress_bar(done_count, total_lessons, 12)
    level = get_level(total_xp, lang)
    next_xp = get_next_level_xp(total_xp)

    if lang == "ru":
        text = (
            f"📊 <b>Мой прогресс</b>\n\n"
            f"Уровень: <b>{level}</b>\n"
            f"XP: <b>{total_xp}</b> / {next_xp}\n"
            f"{progress_bar(total_xp, next_xp, 12)}\n\n"
            f"Уроков пройдено: <b>{done_count}/{total_lessons}</b> ({pct}%)\n"
            f"{bar}\n\n"
        )
        # Прогресс по модулям
        for m in modules:
            done_m = sum(1 for l in m["lessons"] if f"{m['id']}:{l['id']}" in completed)
            total_m = len(m["lessons"])
            text += f"{m['emoji']} {m['title']}: {done_m}/{total_m}\n"
    else:
        text = (
            f"📊 <b>My Progress</b>\n\n"
            f"Level: <b>{level}</b>\n"
            f"XP: <b>{total_xp}</b> / {next_xp}\n"
            f"{progress_bar(total_xp, next_xp, 12)}\n\n"
            f"Lessons done: <b>{done_count}/{total_lessons}</b> ({pct}%)\n"
            f"{bar}\n\n"
        )
        for m in modules:
            done_m = sum(1 for l in m["lessons"] if f"{m['id']}:{l['id']}" in completed)
            total_m = len(m["lessons"])
            text += f"{m['emoji']} {m['title']}: {done_m}/{total_m}\n"

    keyboard = [
        [InlineKeyboardButton(
            "🎓 Продолжить обучение" if lang == "ru" else "🎓 Continue Learning",
            callback_data="academy:main"
        )],
        [InlineKeyboardButton(
            "🔙 Назад" if lang == "ru" else "🔙 Back", callback_data="menu:main"
        )],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def setup_academy_handlers(app):
    """Зарегистрировать все handlers Академии."""
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(cb_academy,               pattern=r"^academy:main$"))
    app.add_handler(CallbackQueryHandler(cb_academy_module,        pattern=r"^academy:module:"))
    app.add_handler(CallbackQueryHandler(cb_academy_lesson,        pattern=r"^academy:lesson:"))
    app.add_handler(CallbackQueryHandler(cb_academy_quiz,          pattern=r"^academy:quiz:"))
    app.add_handler(CallbackQueryHandler(cb_academy_achievements,  pattern=r"^academy:achievements$"))
    app.add_handler(CallbackQueryHandler(cb_academy_stats,         pattern=r"^academy:stats$"))
