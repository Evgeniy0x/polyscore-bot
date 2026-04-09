# PolyScore — AI сервис (OpenRouter, async aiohttp)
# Прогнозы, нарративы, объяснения рынков
# ОБНОВЛЕНО v2: async aiohttp — не блокирует event loop

import json
import os
import sys
import asyncio
import aiohttp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OPENROUTER_API_KEY, AI_MODEL_FAST, AI_MODEL_SMART


# ══════════════════════════════════════════════════════════════════════
# Базовый async вызов OpenRouter
# ══════════════════════════════════════════════════════════════════════

async def call_openrouter(prompt: str, model: str, max_tokens: int = 600) -> str:
    """
    Async вызов OpenRouter API через aiohttp.
    Не блокирует Telegram event loop.
    """
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "ТВОЙ_OPENROUTER_KEY":
        return "⚠️ AI не настроен. Добавь OPENROUTER_API_KEY в .env"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://polyscore.app",
        "X-Title":       "PolyScore",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
                ssl=False,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    body = await resp.text()
                    print(f"[AI] HTTPError {resp.status}: {body[:200]}")
                    return f"⚠️ AI ошибка {resp.status}"
    except asyncio.TimeoutError:
        print("[AI] Timeout при вызове OpenRouter")
        return "⚠️ AI временно недоступен (timeout)"
    except Exception as e:
        print(f"[AI] Ошибка: {e}")
        return "⚠️ AI временно недоступен"


def _extract_yes_price(market: dict) -> float:
    """Извлечь YES цену из любого формата рынка (tokens или outcomePrices)."""
    # Используем GammaClient.extract_prices без импорта (чтобы избежать circular)
    # Формат 1: tokens
    tokens = market.get("tokens", [])
    if tokens:
        for t in tokens:
            if t.get("outcome", "").upper() == "YES":
                return float(t.get("price", 0) or 0)

    # Формат 2: outcomePrices (из /events)
    outcome_prices = market.get("outcomePrices")
    if outcome_prices:
        try:
            prices = json.loads(outcome_prices) if isinstance(outcome_prices, str) else outcome_prices
            if len(prices) >= 1:
                return float(prices[0])
        except Exception:
            pass

    return 0.0


# ══════════════════════════════════════════════════════════════════════
# Спортивные прогнозы
# ══════════════════════════════════════════════════════════════════════

async def get_sport_prediction(market: dict, language: str = "ru") -> str:
    """
    Generate AI prediction for a sports market in user's language.
    Returns analysis text with recommendation.
    """
    question    = market.get("question", market.get("title", ""))
    description = market.get("description", "")

    yes_price = _extract_yes_price(market)
    no_price  = max(0, 1.0 - yes_price) if yes_price > 0 else 0.0

    # Language-specific instructions
    lang_instructions = {
        "ru": """Ты спортивный аналитик prediction markets.

Рынок: {question}
Описание: {description}
Текущие шансы: YES={yes_price:.0%}, NO={no_price:.0%}

Напиши КРАТКИЙ анализ (3-4 предложения MAX) для Telegram-бота:
1. Что означает этот рынок простыми словами
2. Почему рынок стоит именно так (1-2 факта)
3. Где ты видишь VALUE (перекуплен YES или NO?)
4. Рекомендация: BUY YES / BUY NO / ПРОПУСТИТЬ

Пиши по-русски, коротко, как трейдер. Используй эмодзи умеренно.""",
        "en": """You are a sports analyst for prediction markets.

Market: {question}
Description: {description}
Current odds: YES={yes_price:.0%}, NO={no_price:.0%}

Write a SHORT analysis (3-4 sentences MAX) for a Telegram bot:
1. What does this market mean in simple terms
2. Why the market is priced this way (1-2 facts)
3. Where do you see VALUE (is YES or NO overpriced?)
4. Recommendation: BUY YES / BUY NO / SKIP

Write in English, concisely, like a trader. Use emojis sparingly.""",
        "es": """Eres un analista deportivo de mercados de predicción.

Mercado: {question}
Descripción: {description}
Probabilidades actuales: SÍ={yes_price:.0%}, NO={no_price:.0%}

Escribe un análisis BREVE (máximo 3-4 oraciones) para un bot de Telegram:
1. Qué significa este mercado en términos simples
2. Por qué el mercado está valorado así (1-2 hechos)
3. Dónde ves VALUE (¿SÍ o NO está sobrevalorado?)
4. Recomendación: COMPRAR SÍ / COMPRAR NO / SALTAR

Escribe en español, concisamente, como un trader. Usa emojis moderadamente.""",
        "pt": """Você é um analista esportivo de mercados de previsão.

Mercado: {question}
Descrição: {description}
Probabilidades atuais: SIM={yes_price:.0%}, NÃO={no_price:.0%}

Escreva uma análise BREVE (máximo 3-4 frases) para um bot de Telegram:
1. O que este mercado significa em termos simples
2. Por que o mercado está precificado assim (1-2 fatos)
3. Onde você vê VALUE (SIM ou NÃO está precificado demais?)
4. Recomendação: COMPRAR SIM / COMPRAR NÃO / PULAR

Escreva em português, concisamente, como um trader. Use emojis com moderação.""",
        "tr": """Tahmin piyasaları için bir spor analisti misiniz.

Pazar: {question}
Açıklama: {description}
Mevcut oranlar: EVET={yes_price:.0%}, HAYIR={no_price:.0%}

Bir Telegram botu için KISA bir analiz yazın (maksimum 3-4 cümle):
1. Bu pazar basit terimlerle ne anlama gelir
2. Pazar neden bu şekilde fiyatlandırılmıştır (1-2 gerçek)
3. VALUE'yu nerede görüyorsunuz (EVET veya HAYIR aşırı fiyatlanmış mı?)
4. Tavsiye: EVET ALIM / HAYIR ALIM / ATLAMA

Türkçe yazın, kısa ve net, bir trader gibi. Emojileri ılımlı kullanın.""",
        "id": """Anda adalah seorang analis olahraga untuk pasar prediksi.

Pasar: {question}
Deskripsi: {description}
Peluang saat ini: YA={yes_price:.0%}, TIDAK={no_price:.0%}

Tulis analisis SINGKAT (maksimal 3-4 kalimat) untuk bot Telegram:
1. Apa arti pasar ini dalam istilah sederhana
2. Mengapa pasar dihargai seperti ini (1-2 fakta)
3. Di mana Anda melihat VALUE (apakah YA atau TIDAK terlalu mahal?)
4. Rekomendasi: BELI YA / BELI TIDAK / LEWATI

Tulis dalam bahasa Indonesia, ringkas, seperti trader. Gunakan emoji secara moderat.""",
        "zh": """你是预测市场的体育分析师。

市场: {question}
描述: {description}
当前赔率: 是={yes_price:.0%}, 否={no_price:.0%}

为Telegram机器人写简短分析（最多3-4句话）：
1. 用简单话语解释这个市场
2. 为什么市场定价如此（1-2个事实）
3. 你在哪里看到价值（是或否被高估了？）
4. 建议：买是 / 买否 / 跳过

用中文写，简洁，像交易员一样。适度使用表情符号。""",
        "ar": """أنت محلل رياضي لأسواق التنبؤ.

السوق: {question}
الوصف: {description}
الاحتمالات الحالية: نعم={yes_price:.0%}, لا={no_price:.0%}

اكتب تحليلاً موجزاً (3-4 جمل كحد أقصى) لبوت Telegram:
1. ماذا يعني هذا السوق بكلمات بسيطة
2. لماذا السوق بهذا السعر (1-2 حقائق)
3. أين ترى القيمة (هل نعم أو لا مبالغ فيها؟)
4. التوصية: اشترِ نعم / اشترِ لا / تخطَّ

اكتب بالعربية، بإيجاز، مثل المتداول. استخدم الرموز التعبيرية باعتدال.""",
        "fr": """Tu es analyste sportif pour les marchés de prédiction.

Marché: {question}
Description: {description}
Cotes actuelles: OUI={yes_price:.0%}, NON={no_price:.0%}

Rédige une analyse COURTE (3-4 phrases MAX) pour un bot Telegram:
1. Ce que signifie ce marché en termes simples
2. Pourquoi le marché est coté ainsi (1-2 faits)
3. Où tu vois de la valeur (OUI ou NON est surévalué?)
4. Recommandation: ACHETER OUI / ACHETER NON / PASSER

Écris en français, concis, comme un trader. Utilise les emojis avec modération.""",
        "de": """Du bist ein Sportanalyst für Prognosemärkte.

Markt: {question}
Beschreibung: {description}
Aktuelle Quoten: JA={yes_price:.0%}, NEIN={no_price:.0%}

Schreibe eine KURZE Analyse (max. 3-4 Sätze) für einen Telegram-Bot:
1. Was dieser Markt in einfachen Worten bedeutet
2. Warum der Markt so bewertet ist (1-2 Fakten)
3. Wo du Wert siehst (ist JA oder NEIN überbewertet?)
4. Empfehlung: JA KAUFEN / NEIN KAUFEN / ÜBERSPRINGEN

Schreibe auf Deutsch, prägnant, wie ein Trader. Verwende Emojis sparsam.""",
        "hi": """आप भविष्यवाणी बाजारों के लिए एक खेल विश्लेषक हैं।

बाजार: {question}
विवरण: {description}
वर्तमान ऑड्स: हाँ={yes_price:.0%}, नहीं={no_price:.0%}

Telegram बॉट के लिए संक्षिप्त विश्लेषण लिखें (अधिकतम 3-4 वाक्य):
1. इस बाजार का सरल शब्दों में क्या अर्थ है
2. बाजार इस तरह क्यों मूल्यांकित है (1-2 तथ्य)
3. आप कहाँ मूल्य देखते हैं (क्या हाँ या नहीं अधिक मूल्यांकित है?)
4. सिफारिश: हाँ खरीदें / नहीं खरीदें / छोड़ें

हिंदी में लिखें, संक्षिप्त, एक ट्रेडर की तरह। इमोजी का संयम से उपयोग करें।""",
        "ja": """あなたは予測市場のスポーツアナリストです。

市場: {question}
説明: {description}
現在のオッズ: YES={yes_price:.0%}, NO={no_price:.0%}

Telegramボット用に短い分析を書いてください（最大3-4文）：
1. この市場が簡単な言葉で何を意味するか
2. なぜ市場がこのように価格付けされているか（1-2の事実）
3. どこにバリューが見えるか（YESまたはNOは過大評価されているか？）
4. 推奨：YES買い / NO買い / スキップ

日本語で、簡潔に、トレーダーのように書いてください。絵文字は控えめに。""",
    }

    lang_prompt = lang_instructions.get(language, lang_instructions["en"])
    prompt = lang_prompt.format(
        question=question,
        description=description[:300] if description else "—",
        yes_price=yes_price,
        no_price=no_price
    )

    return await call_openrouter(prompt, model=AI_MODEL_FAST, max_tokens=300)


async def get_morning_briefing(markets: list[dict], language: str = "ru") -> str:
    """
    Morning digest — top-5 markets of the day with AI analysis in user's language.
    """
    if not markets:
        no_markets_msg = {
            "ru": "🌅 Сегодня новых рынков нет. Проверь позже!",
            "en": "🌅 No new markets today. Check back later!",
            "es": "🌅 Sin mercados nuevos hoy. ¡Vuelve más tarde!",
            "pt": "🌅 Sem novos mercados hoje. Volte depois!",
            "tr": "🌅 Bugün yeni pazar yok. Daha sonra kontrol et!",
            "id": "🌅 Tidak ada pasar baru hari ini. Periksa nanti!",
        }
        return no_markets_msg.get(language, no_markets_msg["en"])

    top = markets[:5]
    market_list = ""
    for i, m in enumerate(top, 1):
        q = m.get("question", m.get("title", ""))
        yes_p = _extract_yes_price(m)
        v24 = float(m.get("volume24hr", 0) or 0)
        market_list += f"{i}. {q} (YES={yes_p:.0%}, vol=${v24:,.0f})\n"

    lang_briefing = {
        "ru": f"""Ты спортивный аналитик prediction markets. Сегодня утром — {len(top)} горячих рынка.

{market_list}

Напиши утренний брифинг для Telegram-канала (русский язык):
- 3-4 предложения про самые интересные рынки
- Укажи где виден edge (рынок недооценён/переоценён)
- Тон: уверенный, профессиональный, как у спортивного эксперта
- Заверши коротким призывом к действию
- Максимум 150 слов""",
        "en": f"""You are a sports analyst for prediction markets. This morning — {len(top)} hot markets.

{market_list}

Write a morning briefing for a Telegram channel (English):
- 3-4 sentences about the most interesting markets
- Point out where you see edge (market underpriced/overpriced)
- Tone: confident, professional, like a sports expert
- End with a short call to action
- Maximum 150 words""",
        "es": f"""Eres un analista deportivo de mercados de predicción. Esta mañana — {len(top)} mercados candentes.

{market_list}

Escribe un breve matutino para un canal de Telegram (español):
- 3-4 oraciones sobre los mercados más interesantes
- Señala dónde ves edge (mercado infravalorado/sobrevalorado)
- Tono: confiado, profesional, como un experto deportivo
- Termina con un llamado a la acción corto
- Máximo 150 palabras""",
        "pt": f"""Você é um analista esportivo de mercados de previsão. Esta manhã — {len(top)} mercados quentes.

{market_list}

Escreva um resumo matinal para um canal de Telegram (português):
- 3-4 frases sobre os mercados mais interessantes
- Aponte onde você vê vantagem (mercado subavaliado/superavaliado)
- Tom: confiante, profissional, como um especialista em esportes
- Termine com um chamado para ação curto
- Máximo 150 palavras""",
        "tr": f"""Tahmin piyasaları için bir spor analisti misiniz. Bu sabah — {len(top)} sıcak pazarlar.

{market_list}

Bir Telegram kanalı için sabah özeti yazın (Türkçe):
- En ilginç pazarlar hakkında 3-4 cümle
- Edge'i gördüğünüz yeri gösterin (pazar düşük fiyatlı/aşırı fiyatlı)
- Ton: güvenli, profesyonel, spor uzmanı gibi
- Kısa bir harekete geçme çağrısı ile bitirin
- Maksimum 150 kelime""",
        "id": f"""Anda adalah seorang analis olahraga untuk pasar prediksi. Pagi ini — {len(top)} pasar panas.

{market_list}

Tulis ringkasan pagi untuk saluran Telegram (Indonesia):
- 3-4 kalimat tentang pasar yang paling menarik
- Tunjukkan di mana Anda melihat keuntungan (pasar terlalu murah/mahal)
- Nada: percaya diri, profesional, seperti ahli olahraga
- Akhiri dengan ajakan untuk bertindak yang singkat
- Maksimal 150 kata""",
        "zh": f"""你是预测市场的体育分析师。今天早上有 {len(top)} 个热门市场。

{market_list}

为Telegram频道写早间简报（中文）：
- 关于最有趣市场的3-4句话
- 指出在哪里看到优势（市场定价过低/过高）
- 语气：自信、专业，像体育专家
- 以简短的行动号召结束
- 最多150字""",
        "ar": f"""أنت محلل رياضي لأسواق التنبؤ. هذا الصباح — {len(top)} أسواق ساخنة.

{market_list}

اكتب إحاطة صباحية لقناة Telegram (عربي):
- 3-4 جمل عن أكثر الأسواق إثارة للاهتمام
- أشر إلى أين ترى ميزة (السوق بأقل من قيمته/أعلى من قيمته)
- النبرة: واثق، احترافي، مثل خبير رياضي
- اختم بدعوة قصيرة للعمل
- 150 كلمة كحد أقصى""",
        "fr": f"""Tu es analyste sportif pour les marchés de prédiction. Ce matin — {len(top)} marchés chauds.

{market_list}

Rédige un briefing matinal pour une chaîne Telegram (français):
- 3-4 phrases sur les marchés les plus intéressants
- Indique où tu vois un avantage (marché sous-évalué/surévalué)
- Ton: confiant, professionnel, comme un expert sportif
- Termine avec un appel à l'action court
- Maximum 150 mots""",
        "de": f"""Du bist ein Sportanalyst für Prognosemärkte. Heute Morgen — {len(top)} heiße Märkte.

{market_list}

Schreibe ein morgendliches Briefing für einen Telegram-Kanal (Deutsch):
- 3-4 Sätze über die interessantesten Märkte
- Weise darauf hin, wo du einen Vorteil siehst (Markt unterbewertet/überbewertet)
- Ton: selbstbewusst, professionell, wie ein Sportexperte
- Beende mit einem kurzen Handlungsaufruf
- Maximal 150 Wörter""",
        "hi": f"""आप भविष्यवाणी बाजारों के लिए एक खेल विश्लेषक हैं। आज सुबह — {len(top)} गर्म बाजार।

{market_list}

Telegram चैनल के लिए सुबह की संक्षिप्त रिपोर्ट लिखें (हिंदी):
- सबसे दिलचस्प बाजारों के बारे में 3-4 वाक्य
- बताएं कहाँ फायदा दिखता है (बाजार कम/ज्यादा मूल्यांकित)
- स्वर: आत्मविश्वासी, पेशेवर, खेल विशेषज्ञ की तरह
- एक छोटे कार्य-आह्वान के साथ समाप्त करें
- अधिकतम 150 शब्द""",
        "ja": f"""あなたは予測市場のスポーツアナリストです。今朝 — {len(top)} つのホットなマーケット。

{market_list}

Telegramチャンネル用の朝のブリーフィングを書いてください（日本語）：
- 最も興味深い市場について3-4文
- エッジが見える場所を指摘する（市場が過小評価/過大評価）
- トーン：自信満々、プロフェッショナル、スポーツ専門家のように
- 短い行動の呼びかけで締める
- 最大150語""",
    }

    prompt = lang_briefing.get(language, lang_briefing["en"])
    return await call_openrouter(prompt, model=AI_MODEL_SMART, max_tokens=400)


async def explain_market(market: dict, language: str = "ru") -> str:
    """
    Explain a market in simple terms in user's language.
    For beginners who don't understand what's happening.
    """
    question = market.get("question", market.get("title", ""))
    desc     = market.get("description", "")[:400]
    end_date = market.get("endDate", "")[:10]
    yes_price = _extract_yes_price(market)

    lang_prompts = {
        "ru": f"""Объясни этот рынок prediction market простыми словами по-русски.

Вопрос: {question}
Детали: {desc if desc else "нет описания"}
Текущая цена YES: {yes_price:.0%}
Закрывается: {end_date}

Напиши для новичка (4-5 предложений):
1. Что означает этот рынок на обычном языке
2. Когда и как он резолвится (когда узнаем результат)
3. Что означает текущая цена {yes_price:.0%}
4. На что обратить внимание при ставке

Без сложных терминов DeFi. Пиши как объясняешь другу.""",
        "en": f"""Explain this prediction market in simple English words.

Question: {question}
Details: {desc if desc else "no description"}
Current YES price: {yes_price:.0%}
Closes: {end_date}

Write for a beginner (4-5 sentences):
1. What this market means in plain language
2. When and how it resolves (when we'll know the answer)
3. What the current price {yes_price:.0%} means
4. What to watch for when placing a bet

No complex DeFi terms. Write like you're explaining to a friend.""",
        "es": f"""Explica este mercado de predicción en términos simples en español.

Pregunta: {question}
Detalles: {desc if desc else "sin descripción"}
Precio actual de SÍ: {yes_price:.0%}
Cierra: {end_date}

Escribe para un principiante (4-5 oraciones):
1. Qué significa este mercado en lenguaje simple
2. Cuándo y cómo se resuelve (cuándo sabremos la respuesta)
3. Qué significa el precio actual de {yes_price:.0%}
4. Qué vigilar al hacer una apuesta

Sin términos complejos de DeFi. Escribe como si explicaras a un amigo.""",
        "pt": f"""Explique este mercado de previsão em termos simples em português.

Pergunta: {question}
Detalhes: {desc if desc else "sem descrição"}
Preço atual de SIM: {yes_price:.0%}
Fecha em: {end_date}

Escreva para um iniciante (4-5 frases):
1. O que este mercado significa em linguagem simples
2. Quando e como ele se resolve (quando saberemos a resposta)
3. O que o preço atual de {yes_price:.0%} significa
4. O que observar ao fazer uma aposta

Sem termos complexos de DeFi. Escreva como se explicasse a um amigo.""",
        "tr": f"""Bu tahmin pazarını Türkçe basit terimlerle açıklayın.

Soru: {question}
Detaylar: {desc if desc else "açıklama yok"}
Mevcut EVET fiyatı: {yes_price:.0%}
Kapanış: {end_date}

Bir başlangıç için yazın (4-5 cümle):
1. Bu pazarın basit dilde ne anlama geldiği
2. Ne zaman ve nasıl çözüleceği (cevabı ne zaman bilebileceğimiz)
3. Mevcut fiyat {yes_price:.0%}'nin ne anlama geldiği
4. Bahis yaparken nelere dikkat etmek gerekir

Karmaşık DeFi terimleri yok. Bir arkadaşa açıklar gibi yazın.""",
        "id": f"""Jelaskan pasar prediksi ini dalam istilah sederhana dalam bahasa Indonesia.

Pertanyaan: {question}
Detail: {desc if desc else "tanpa deskripsi"}
Harga YA saat ini: {yes_price:.0%}
Ditutup: {end_date}

Tulis untuk pemula (4-5 kalimat):
1. Apa arti pasar ini dalam bahasa sederhana
2. Kapan dan bagaimana cara diselesaikan (kapan kita akan tahu jawabannya)
3. Apa arti harga saat ini {yes_price:.0%}
4. Apa yang harus diperhatikan saat menempatkan taruhan

Tidak ada istilah DeFi yang kompleks. Tulis seperti menjelaskan kepada teman.""",
    }

    prompt = lang_prompts.get(language, lang_prompts["en"])
    return await call_openrouter(prompt, model=AI_MODEL_FAST, max_tokens=350)


async def analyze_edge(market: dict, language: str = "ru") -> str:
    """
    Edge analysis — where AI sees mismatch with real probability in user's language.
    """
    question  = market.get("question", market.get("title", ""))
    volume    = float(market.get("volume", 0) or 0)
    yes_price = _extract_yes_price(market)

    lang_prompts = {
        "ru": f"""Ты аналитик prediction markets. Найди edge.

Рынок: {question}
Рыночная цена YES: {yes_price:.0%}
Общий объём: ${volume:,.0f}

Оцени (по-русски, 3-4 предложения):
1. Какова ТВОЯ оценка реальной вероятности? (от 0 до 100%)
2. Есть ли edge? Рынок пере- или недооценён?
3. Риски ставки в ту или иную сторону
4. Итог: BUY YES / BUY NO / НЕЙТРАЛЬНО

Будь честным — если не знаешь, так и скажи.""",
        "en": f"""You are a prediction market analyst. Find the edge.

Market: {question}
Market YES price: {yes_price:.0%}
Total volume: ${volume:,.0f}

Evaluate (in English, 3-4 sentences):
1. What is YOUR estimate of the true probability? (0-100%)
2. Is there an edge? Is the market overpriced or underpriced?
3. Risks of betting either way
4. Bottom line: BUY YES / BUY NO / NEUTRAL

Be honest — if you don't know, say so.""",
        "es": f"""Eres un analista de mercados de predicción. Encuentra el edge.

Mercado: {question}
Precio del mercado SÍ: {yes_price:.0%}
Volumen total: ${volume:,.0f}

Evalúa (en español, 3-4 oraciones):
1. ¿Cuál es TU estimación de la probabilidad real? (0-100%)
2. ¿Hay edge? ¿El mercado está sobrevalorado o infravalorado?
3. Riesgos de apostar en cualquier dirección
4. Conclusión: COMPRAR SÍ / COMPRAR NO / NEUTRAL

Sé honesto — si no sabes, dilo.""",
        "pt": f"""Você é um analista de mercados de previsão. Encontre a vantagem.

Mercado: {question}
Preço do mercado SIM: {yes_price:.0%}
Volume total: ${volume:,.0f}

Avalie (em português, 3-4 frases):
1. Qual é SUA estimativa da probabilidade real? (0-100%)
2. Há vantagem? O mercado está sobrevalorado ou subavaliado?
3. Riscos de apostar de qualquer forma
4. Conclusão: COMPRAR SIM / COMPRAR NÃO / NEUTRO

Seja honesto — se não souber, diga.""",
        "tr": f"""Siz bir tahmin piyasası analisti misiniz. Edge'i bulun.

Pazar: {question}
Pazar EVET fiyatı: {yes_price:.0%}
Toplam hacim: ${volume:,.0f}

Değerlendirin (Türkçe, 3-4 cümle):
1. Gerçek olasılık için SİZİN tahmininiz nedir? (0-100%)
2. Edge var mı? Pazar aşırı fiyatlı mı yoksa düşük fiyatlı mı?
3. Her iki yöne de bahis yapmanın riskleri
4. Sonuç: EVET ALIM / HAYIR ALIM / TARAFSIZ

Dürüst olun — eğer bilmiyorsanız, söyleyin.""",
        "id": f"""Anda adalah seorang analis pasar prediksi. Temukan keuntungannya.

Pasar: {question}
Harga pasar YA: {yes_price:.0%}
Volume total: ${volume:,.0f}

Evaluasi (dalam bahasa Indonesia, 3-4 kalimat):
1. Apa perkiraan ANDA tentang probabilitas sebenarnya? (0-100%)
2. Apakah ada keuntungan? Apakah pasar terlalu mahal atau murah?
3. Risiko bertaruh dengan cara apa pun
4. Garis bawah: BELI YA / BELI TIDAK / NETRAL

Jadilah jujur — jika Anda tidak tahu, katakan saja.""",
    }

    prompt = lang_prompts.get(language, lang_prompts["en"])
    return await call_openrouter(prompt, model=AI_MODEL_SMART, max_tokens=300)
