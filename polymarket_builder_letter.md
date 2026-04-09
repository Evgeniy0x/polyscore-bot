# PolyScore — Letter to Polymarket Team

**To:** builders@polymarket.com / team@polymarket.com
**Subject:** PolyScore — Telegram Bot with 12 Languages, AES-256 Security & Zero Fees. Applying for Builder Program.

---

Hi Polymarket Team,

My name is Kash. I've been building on top of Polymarket for the past several months, and I want to share what I've created — and ask for your help to take it further.

**PolyScore** is a Telegram bot that brings Polymarket to a global audience that would never otherwise find it. Think of it as Polymarket's front door for the other 6 billion people who don't speak English and don't use desktop apps.

Here's what we've built:

---

## What PolyScore Does Today

**Zero platform fee.** We take nothing from users. Our revenue comes from Polymarket's existing fee structure, meaning we're fully aligned — every user we bring is pure upside for both of us.

**12 languages.** Russian, Spanish, Portuguese, Turkish, Indonesian, Chinese, Arabic, French, German, Hindi, Japanese, and English. Market names are automatically translated using a cached translation layer (SQLite + Google Translate), so a user in Jakarta sees Indonesian market names the moment they open the app.

**AES-256-CTR + HMAC-SHA256 wallet encryption.** Private keys are never stored in plaintext. We use symmetric encryption with a master key from environment variables — even if our database were somehow compromised, keys are useless without the master key. We built this after the Polycule incident ($230K lost due to insecure key storage) specifically to show that Telegram bots can be done safely.

**Live price alerts.** Users set a target price on any YES/NO market and get a Telegram notification the moment it crosses. This drives re-engagement and keeps traders active.

**Built-in Academy.** Five structured learning modules (50–100 XP each) teaching prediction market fundamentals, bankroll management, liquidity dynamics, whale behavior, and trader psychology. In 12 languages. Because the biggest barrier to Polymarket adoption isn't trust — it's understanding.

**Parlay system.** Users can combine multiple markets into a single position. This is a feature even desktop Polymarket doesn't offer in a native UI.

**Copy Trading.** Users can follow top traders and mirror their positions automatically.

**Leaderboard.** Weekly rankings by profit%, ROI, and volume. Creates organic competition and retention.

---

## The Problem We're Solving

Look at Polymarket's current builder ecosystem:

- **PolyGun** — English only, 1% additional fee, no alerts, no academy
- **PolyCop** — English only, 0.5% additional fee, no education layer
- **PolyBot** — English only, 1% fee, basic interface
- **Polycule** — was hacked for $230K and went offline

None of them speak the language of the next 100 million prediction market users. None of them have an education layer. None of them are free.

**We are.** And we've verified it works — we have active users across Russia, Turkey, Indonesia, and Brazil who found prediction markets for the first time through PolyScore.

---

## What's Coming Next

**Crypto markets.** We're adding dedicated crypto-native markets: BTC/ETH price targets, altcoin pumps, protocol TVL, on-chain metrics. These markets perform extremely well with the Telegram-native crypto audience.

**15-minute micro-markets.** Short-duration intraday markets on sports scores, crypto price moves, and news events. These are perfect for the Telegram user who checks their phone between meetings. High frequency = high engagement = more volume flowing through Polymarket.

**Social signals & AI predictions.** We're building an AI layer that analyzes Twitter/X sentiment, Reddit activity, and on-chain data to surface market inefficiencies. We call it PolyScore AI — it gives users an edge, which keeps them on our platform (and on Polymarket).

**Web interface.** We've launched a landing page that explains PolyScore to new users before they open Telegram: **[polyscore.bet]** (or github.io link — deploying this week). The site is in English and already ranks above our competitors for "polymarket telegram bot" in early SEO signals.

---

## What We're Asking For

We're applying to **every builder rewards program** you offer, and we'd love your help with:

1. **Builder grant or rewards allocation** — We're driving real volume and real new users. Even a modest allocation would accelerate development of the crypto markets and 15-minute market features significantly.

2. **API priority / higher rate limits** — As our user base grows (especially in Asia and LATAM), we're hitting rate limit walls during peak hours. We'd love to discuss an arrangement that supports scale.

3. **Co-marketing** — A single mention of PolyScore in your Twitter/X, Telegram, or newsletter would be worth more to us than any grant. We serve markets that your current users simply don't reach.

4. **Direct feedback** — If there are features, integrations, or market categories that you want to see built for Telegram users, we'll build them. We're fast, we're motivated, and we're already embedded in your ecosystem.

5. **Verified builder status** — We want to be the official Polymarket Telegram interface for non-English speakers. This is a category you don't have covered yet.

---

## Why PolyScore Is Different

Every other Telegram bot in your ecosystem is a fee extraction tool built for English speakers.

We are a **growth tool** built for the world.

When users in Indonesia discover prediction markets through PolyScore, they don't know about PolyGun or PolyCop. They learn what a prediction market is, they make their first trade, and they become Polymarket users for life — through us.

We're not competing with Polymarket. We're your distribution layer for markets that your core product can't reach: people who live in Telegram, speak another language, and have never heard of CLOB liquidity or AMMs.

---

## Technical Stack (for your engineers)

- Python 3.12, python-telegram-bot v21.9 (async)
- SQLite + aiosqlite (Railway PaaS deployment)
- eth-account==0.8.0 (pure Python, no C extensions — Railway-compatible)
- AES-256-CTR with HMAC-SHA256, self-testing on import
- deep-translator with SQLite caching (no API costs, instant repeat lookups)
- Polymarket REST + WebSocket APIs
- Background asyncio workers for alerts (5-minute intervals) and copy trading

We'd love to schedule a call, get your feedback, or simply get acknowledged as a builder in your ecosystem.

Telegram: @PolymarketMAMA_Bot
Website: https://polyscore.bet
GitHub: https://github.com/[your-handle]/polyscore-bot
Email: nomer5555@gmail.com

Thank you for building the infrastructure that makes all of this possible. Polymarket is the most important prediction market platform in the world — and we want to help it reach the rest of it.

— Kash
Founder, PolyScore

---

*P.S. — We noticed Polycule lost $230K because they stored private keys in plaintext. We built PolyScore's security from scratch specifically to prove that Telegram bots can hold user funds safely. We'd love to be your reference implementation for secure builder integrations.*
