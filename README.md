# PolyScore

> **Telegram-бот для ставок на Polymarket — 0% комиссии, 12 языков, AES-256**
> Официальная заявка в [Polymarket Builders Program](https://builders.polymarket.com) — $2.5M+ грантов

**Telegram бот:** [@PolymarketMAMA_Bot](https://t.me/PolymarketMAMA_Bot)
**Лендинг:** https://polyscore-bot.vercel.app
**Builder Address:** `0x9d0724d90f6f3ea13990afd3b7211ff358efc489`
**Builder API Key:** `019d0c95-6adc-764f-9dd1-d79e70e3f1fe`
**Основатель:** Kash (nomer5555@gmail.com)
**Дата создания:** 20.03.2026

PolyScore brings sports prediction markets to mainstream bettors through Telegram. Instead of crypto-native UIs, users get familiar sports-betting language: American odds, parlay builders, shareable bet slip cards, and AI-powered picks — all backed by Polymarket's deep liquidity.

---

## Why PolyScore Wins the Builders Competition

| Signal | Detail |
|---|---|
| 📅 MLB Partnership | Announced March 19, 2026 — sports markets are Polymarket's growth bet |
| 📊 Sports = 39% volume | Largest category, yet zero sports-native trading interfaces exist |
| 🎯 New audience | Sports bettors (50M+ in US) don't know Polymarket exists |
| 💰 Volume multiplier | Parlay = 3–5 orders per click → outsized builder revenue share |
| 📱 Telegram | 950M MAU, zero-install, viral by default (share bet slips) |

---

## Features (MVP)

- **🏅 Sports Markets** — Browse MLB, NBA, NHL, UFC, F1, Soccer by category
- **📈 Trending** — Hot markets sorted by 24h volume
- **🎰 Parlay Builder** — Combine 2–5 legs, auto-calculate combined odds and payout
- **🤖 AI Picks** — Claude Sonnet 4-powered analysis and edge detection per market
- **📸 Bet Slip Cards** — Shareable PNG cards with outcome, American odds, payout
- **💼 Portfolio** — Track bets, parlays, P&L in Telegram
- **📋 Watchlist** — Save markets to monitor
- **🌍 Bilingual** — Russian + English UI

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/polyscore
cd polyscore
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required:
- `BOT_TOKEN` — create via [@BotFather](https://t.me/BotFather) on Telegram
- `OPENROUTER_API_KEY` — get from [openrouter.ai](https://openrouter.ai)

Optional (for live trading):
- `POLY_API_KEY`, `POLY_SECRET`, `POLY_PASSPHRASE` — from [polymarket.com/settings?tab=builder](https://polymarket.com/settings?tab=builder)

### 3. Run

```bash
python bot.py
```

The bot starts in **demo mode** by default — all bets are recorded to the local database without real on-chain orders. To enable live trading, add your Polymarket API credentials to `.env` and uncomment the CLOB order placement in `handlers/betting.py`.

---

## Project Structure

```
polyscore/
├── bot.py                  # Entry point — registers all handlers
├── config.py               # API keys, URLs, sport tags, UI constants
├── requirements.txt
├── .env.example
│
├── services/
│   ├── polymarket.py       # Gamma API, CLOB API, Relayer clients
│   ├── database.py         # Async SQLite (aiosqlite) — users/bets/parlays
│   └── ai_service.py       # OpenRouter → Claude Sonnet 4 via stdlib urllib
│
├── handlers/
│   ├── start.py            # /start, language switch, main menu
│   ├── markets.py          # Sport browsing, market detail, watchlist
│   ├── betting.py          # ConversationHandler: bet flow → slip card
│   ├── parlay.py           # Multi-leg parlay builder
│   └── portfolio.py        # Stats, history, AI briefings
│
└── utils/
    └── bet_slip.py         # Pillow PNG bet slip generator
```

---

## Architecture

```
User (Telegram)
    │
    ▼
python-telegram-bot v21 (async)
    │
    ├──► Gamma API (polymarket) ──► market data (no auth)
    ├──► CLOB API (polymarket)  ──► order placement (API key)
    ├──► Relayer v2             ──► gasless wallet creation
    ├──► OpenRouter API         ──► Claude Sonnet 4 / Gemini Flash
    └──► SQLite (aiosqlite)     ──► users, bets, parlays, watchlist
```

### Builder Code

Every order placed through PolyScore embeds `builder_code=polyscore` in the CLOB API request. This attributes all trading volume to PolyScore in Polymarket's weekly reward distribution (~0.5–1% of routed volume paid in USDC).

### Parlay Volume Multiplier

A single 3-leg parlay click generates **3 separate market orders** — each with the builder code embedded. A user building 5-leg parlays daily generates 5× the builder revenue compared to single bets.

---

## Deploy on Railway (one-click)

```bash
railway login
railway init
railway up
```

Set environment variables in the Railway dashboard under **Variables**. See `railway.toml` for service configuration.

### Alternative: Fly.io

```bash
fly launch
fly secrets set BOT_TOKEN=xxx OPENROUTER_API_KEY=xxx
fly deploy
```

---

## Enabling Live Trading

1. Register as a Polymarket builder at [polymarket.com/settings?tab=builder](https://polymarket.com/settings?tab=builder)
2. Copy your API key, secret, and passphrase to `.env`
3. In `handlers/betting.py`, find the `cb_bet_confirm` function and uncomment:
   ```python
   # result = await clob.place_market_order(...)
   ```
4. In `handlers/parlay.py`, find `cb_parlay_place` and uncomment the order loop

---

## Roadmap

- [ ] `/wallet` command — guided Safe wallet setup via Relayer v2
- [ ] Price alerts — background task watching watched markets
- [ ] Public channel auto-posting — daily hot markets digest to @PolyScore
- [ ] Web app — Mini App (TWA) for deeper market browsing
- [ ] Live P&L — real-time position tracking via CLOB WebSocket
- [ ] Social feed — see what top bettors are trading

---

## Grant Application Pitch

**Problem:** 50M+ US sports bettors have never heard of Polymarket. Existing interfaces are built for crypto-native traders, not sports fans.

**Solution:** PolyScore speaks sports-bettor language — American odds, parlays, bet slips — delivered through Telegram (zero-install, viral by design).

**Traction opportunity:** The MLB partnership (March 2026) creates a perfect moment to onboard sports audiences. PolyScore is purpose-built to capture this wave.

**Revenue model for Polymarket:** Every PolyScore user generates builder-code-attributed volume. Parlay builders multiply this by 3–5× per session. More sports bettors onboarded = more liquidity in sports markets = better odds for everyone.

**Team:** [your name/team here]
**Builder code:** `polyscore`
**Apply:** [builders.polymarket.com](https://builders.polymarket.com)

---

## Tech Stack

| Layer | Tech |
|---|---|
| Bot framework | python-telegram-bot 21.9 (async) |
| Market data | Polymarket Gamma API (REST) |
| Trading | Polymarket CLOB API (REST + WebSocket) |
| Wallet | Polymarket Relayer v2 (gasless Safe) |
| AI | OpenRouter → Claude Sonnet 4 / Gemini 2.0 Flash |
| Database | SQLite via aiosqlite |
| Images | Pillow (PNG bet slips) |
| Deploy | Railway / Fly.io |

---

## License

MIT — build on it, fork it, ship it. If you use the builder code pattern, change `BUILDER_CODE` in `config.py` to your own.
