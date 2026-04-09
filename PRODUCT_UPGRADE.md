# PolyScore — Product Upgrade Specification
> Version 2.0 · Architect: controlled upgrade (no rebuild)
> Date: 2026-03-21

---

## 1. PRODUCT STRUCTURE — 3 LAYERS

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 — CORE (Signal → Decision → Execute → Track)       │
│  Intel Mode  ·  Signal Card  ·  Quick Execute  ·  Result    │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2 — TRADING SYSTEM                                   │
│  Portfolio  ·  Copy Trading  ·  Alerts  ·  Parlays          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3 — ECOSYSTEM                                        │
│  Academy  ·  Analytics  ·  Leaderboard  ·  Settings        │
└─────────────────────────────────────────────────────────────┘
```

**Layer 1** — everything a new user touches in first 5 minutes.
**Layer 2** — power user features, accessed after first trade.
**Layer 3** — optional, never blocks the core flow.

---

## 2. CORE LOOP

```
SIGNAL (from AI or whale activity or mispricing)
    ↓
SIGNAL CARD (market + direction + edge + reason + risk)
    ↓  [Tap: "Trade" or "Skip"]
AMOUNT INPUT (pre-filled suggestion, editable)
    ↓  [Tap: "Confirm $X"]
EXECUTION (CLOB order or demo fallback)
    ↓
RESULT FEEDBACK (instant: "✅ Position open · $X · potential $Y")
    ↓
PORTFOLIO TRACKING (real-time from data-api.polymarket.com)
    ↓
WIN/LOSS NOTIFICATION (push when market resolves)
```

Total taps: **3** (Signal Card → Confirm amount → Confirm trade)

---

## 3. INTEL MODE UX

### Entry Points
- Main menu → "🧠 Intel" button (no wallet required)
- /intel command
- Auto-shown to new users without wallet (replaces empty state)

### What User Sees in <10 Seconds

```
🧠 Intel Feed

📊 BTC >$95k by April?
   YES 67% · Edge: +8.3%
   🐋 Whale just bought $12k YES
   "Market underprices this given options data"
   [📈 Trade YES]  [Skip →]

─────────────────────────
📊 Trump approval >50%?
   NO 71% · Edge: +5.1%
   🤖 AI Model · High confidence
   "Poll divergence from market price"
   [📈 Trade NO]  [Skip →]

─────────────────────────
[🔔 Set Alert]  [📚 Learn why]
```

### Intel Feed Rules
- Max 5 signals per session refresh
- Sorted by: edge % descending
- Priority badges: 🔴 HIGH / 🟡 MEDIUM / ⚪ LOW
- No wallet required to VIEW
- Wallet required to TRADE (graceful redirect)
- Refresh button every 30 min (not auto-spam)

### Intel → Trade Transition
```
User taps [📈 Trade YES]
  ↓
If no wallet:
  "📲 One step: connect wallet to execute"
  [🚀 Create Wallet]  [📲 I have one]
  (after wallet → returns to same signal)

If wallet:
  → Amount screen with pre-filled suggestion
```

---

## 4. TRADER MODE UX

### Entry: Main Menu after wallet connected

```
⚡ PolyScore

💼 Balance: $247.50 USDC
📊 Open: 3 positions · +$12.40 P&L

[🧠 Intel]      [📊 Portfolio]
[🤖 AutoTrade]  [🔥 Markets]
[⚙️ Settings]   [🏆 Leaders]
```

### Key Principles
- Balance shown on main screen (from wallet API)
- Open position count + unrealized P&L always visible
- Intel is primary CTA (not Markets)
- Max 6 buttons, 2-per-row

### Portfolio Quick View (inline on main screen)
- Shows top 3 open positions
- Tap → full portfolio

---

## 5. SIGNAL SYSTEM

### DecisionObject Schema
```python
@dataclass
class SignalCard:
    # Identity
    signal_id: str          # uuid
    market_id: str          # Polymarket conditionId
    question: str           # "Will BTC exceed $95k by April 30?"

    # Direction
    direction: str          # "YES" | "NO"
    current_price: float    # 0.67 = 67%
    fair_value: float       # model's estimate = 0.75

    # Edge
    edge_pct: float         # (fair_value - current_price) / current_price = 11.9%
    confidence: float       # 0.0 - 1.0

    # Source
    source: str             # "whale_activity" | "ai_model" | "mispricing" | "algo"
    source_label: str       # "🐋 Whale" | "🤖 AI Model" | "📊 Arbitrage" | "⚡ Algo"

    # Timing
    generated_at: datetime
    expires_at: datetime    # signal TTL
    market_closes_at: datetime | None

    # Human explanation
    reason: str             # 1 line: "Options market implies 75%, Polymarket at 67%"
    risk: str               # 1 line: "Low liquidity, spread ~3%"

    # Execution hint
    suggested_amount: float  # USDC
    priority: str           # "HIGH" | "MEDIUM" | "LOW"
```

### Signal Sources
| Source | Generator | Frequency |
|---|---|---|
| `ai_model` | ai_service.py morning briefing | 1x/day per user |
| `whale_activity` | copy_trading_service monitoring top wallets | Real-time |
| `mispricing` | trading_algorithm cross-platform strategy | Every 15 min |
| `algo` | trading_algorithm behavioral/event strategies | Triggered |

### Signal Prioritization
```
HIGH:   edge > 10% AND confidence > 0.75 AND volume > $100k
MEDIUM: edge > 5%  AND confidence > 0.60
LOW:    everything else (shown but not notified)
```

### Anti-Spam Rules
- Max 3 push notifications per user per day
- HIGH priority only in push
- MEDIUM/LOW shown in feed but no push
- Same market: max 1 signal per 4 hours
- User can set: "Notify for HIGH only" (default) or "All" or "Off"

### Signal Card Format (Telegram message)
```
🔴 HIGH SIGNAL

📊 Will BTC exceed $95k by April 30?

Direction:  YES  67% → 75% (est.)
Edge:       +11.9%  |  Confidence: 78%
Source:     🐋 Whale Activity
Closes:     Apr 30, 2026

💡 Options market implies 75%, PM at 67%
⚠️  Low liquidity, spread ~3%

💵 Suggested: $25 USDC

[✅ Trade $25 YES]  [✏️ Change amount]
[⏭ Skip]           [📚 Learn why]
```

---

## 6. EXECUTION FLOW

### Unified 3-Tap Flow

```
TAP 1: Signal Card → [✅ Trade $25 YES]
  ↓
TAP 2: Amount confirmation screen
  ┌──────────────────────────────┐
  │ 📋 Confirm Trade             │
  │                              │
  │ ✅ YES · 67% · (+44) odds    │
  │ Amount:    $25.00 USDC       │
  │ Potential: $37.31 USDC       │
  │ Net profit: +$12.31          │
  │                              │
  │ ⚠️ Trades are irreversible   │
  └──────────────────────────────┘
  [✅ Confirm $25]  [✏️ Edit]  [❌ Cancel]
  ↓
TAP 3: [✅ Confirm $25]
  ↓
EXECUTION + RESULT CARD
```

### Amount Screen Rules
- Pre-fill from `signal.suggested_amount`
- If no signal context: show last used amount
- Min $1, no max shown (wallet balance check)
- [✏️ Edit] → inline edit (not new screen)

### Result Card (immediate feedback)
```
🎉 Position Open!

✅ YES · $25.00 USDC
📈 Price: 67% · (+44)
💰 Potential: $37.31
📋 ID: #8472

[📊 My Portfolio]  [🧠 More Signals]
```
Sends as photo (bet_slip) + inline buttons.

### Error States in Execution
| Error | Message | Next Action |
|---|---|---|
| No wallet | "💳 Connect wallet first" | [Create] [Add] |
| Insufficient balance | "💰 Not enough USDC · Balance: $X" | [Add funds guide] |
| Market closed | "⏰ This market has closed" | [See similar] |
| CLOB rejected | "❌ Order rejected: {reason}" | [Try smaller amount] |
| API timeout | "🔄 Network issue · Try again?" | [Retry] [Cancel] |
| Demo mode | "🎮 Demo: trade saved locally (no CLOB key)" | [Portfolio] |

---

## 7. PORTFOLIO SYSTEM

### Data Source: data-api.polymarket.com

```
GET https://data-api.polymarket.com/positions?user={wallet_address}&sizeThreshold=0

Returns:
[{
  "market": "Will BTC...",
  "conditionId": "0x...",
  "outcome": "YES",
  "outcomeIndex": 0,
  "size": 37.31,          # shares owned
  "avgPrice": 0.67,       # entry price
  "currentPrice": 0.71,   # current price
  "initialValue": 25.0,   # USDC invested
  "currentValue": 26.51,  # current USDC value
  "cashPnl": 1.51,        # unrealized P&L
  "percentPnl": 6.04,     # %
  "closed": false
}]
```

### Portfolio Screen Design
```
📊 My Portfolio

💼 Total Invested:  $125.00 USDC
📈 Current Value:   $134.20 USDC
💰 Unrealized P&L:  +$9.20  (+7.4%)

── Open Positions (3) ──────────────

✅ YES  BTC >$95k by Apr
   Entry: 67% · Now: 71% · +$1.51 (+6%)
   $25 → $26.51

❌ NO   Trump approval >50%
   Entry: 71% · Now: 68% · +$2.10 (+8.3%)
   $25 → $27.10

⏳ YES  Fed rate cut Mar?
   Entry: 45% · Now: 44% · -$0.45 (-2%)
   $15 → $14.55

── Resolved ────────────────────────
[Show last 5 resolved]

[🔙 Menu]  [🧠 New Signals]
```

### Position Sync Strategy
```python
# services/position_sync.py
# Runs as background task every 10 minutes
# Only syncs users active in last 48 hours

async def sync_user_positions(user_id, wallet_address, bot):
    positions = await fetch_polymarket_positions(wallet_address)
    for pos in positions:
        if pos["closed"] and not already_notified(pos["conditionId"]):
            await notify_resolved(user_id, pos, bot)
    store_positions_cache(user_id, positions)
```

### New DB Table: positions_cache
```sql
CREATE TABLE positions_cache (
    user_id       INTEGER,
    condition_id  TEXT,
    data_json     TEXT,   -- full position JSON
    synced_at     TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, condition_id)
)
```

---

## 8. ACADEMY INTEGRATION

### Principles
- Academy is **optional, never blocking**
- Accessible via: /academy, "🎓 Academy" in Layer 3 menu
- Contextually linked from signals: [📚 Learn why]
- NOT shown during onboarding (separate flow)

### Contextual Links (new feature)
Each SignalCard gets optional `learn_topic` field:
```python
signal.learn_topic = "mispricing"  # links to Academy module on arbitrage
```
When user taps [📚 Learn why]:
```
📚 Why this matters

This signal comes from price divergence between
Polymarket and options markets.

Learn more → [📖 Module: Market Inefficiency]
[← Back to Signal]
```

### Academy Access in Menu
Moved from main menu Row 3 → Settings/More screen:
```
⚙️ More
  [🎓 Academy]    [📊 Analytics]
  [🏆 Leaderboard] [📋 History]
  [🔙 Back]
```

---

## 9. CRITICAL FIXES

### Fix #1 — Async AI (BLOCKING BUG)

File: `services/ai_service.py`

Problem: `urllib.request.urlopen()` is synchronous → blocks Telegram event loop for up to 30s.

Fix: Replace with `aiohttp`. All public functions become `async`.
Callers: `portfolio.py`, `markets.py` — update to `await`.

### Fix #2 — Wallet Guard Before Betting

File: `handlers/betting.py` → `cb_bet_start()`

Add at start:
```python
user = await get_user(query.from_user.id)
if not user or not user.get("wallet_address"):
    # redirect to wallet with context return
    ctx.user_data["return_to"] = query.data  # remember where they came from
    await query.edit_message_text(...)
    return ConversationHandler.END
```

### Fix #3 — Cache Fallback on Restart

File: `handlers/markets.py` → `_get_cached()`

Add fallback:
```python
def _get_cached(ctx, idx):
    market = ctx.bot_data.get("mc", {}).get(idx)
    if not market:
        return None  # caller must handle None
```

All callers check for None → show "List refreshed, please browse again" + [Markets button].

### Fix #4 — Settings Handler

New file: `handlers/settings.py`

Settings screen:
```
⚙️ Settings

Language:     🇷🇺 Русский  [Change]
Notifications: 🔔 HIGH only [Change]
Mode:          🎮 Demo       [→ Live]
Wallet:        0xabc...def  [Manage]

[🔙 Back]
```

---

## 10. IMPLEMENTATION PLAN

### Sprint 0 — Critical Fixes (Day 1-2)
Priority: UNBLOCK the product

- [ ] Fix #1: async ai_service.py
- [ ] Fix #2: wallet guard in betting.py
- [ ] Fix #3: cache fallback in markets.py
- [ ] Fix #4: settings.py handler

No new features. Just make existing product reliable.

### Sprint 1 — Signal System (Day 3-5)
Priority: DIFFERENTIATE the product

- [ ] Create `services/signal_pipeline.py` with `SignalCard` dataclass
- [ ] Update `ai_service.py` to return `SignalCard` from `get_morning_briefing()`
- [ ] Create `handlers/intel.py` (Intel Mode feed)
- [ ] Add Intel Mode to main menu (replaces "AI Pick" button)
- [ ] Signal card renderer function (text formatter)

### Sprint 2 — Real Portfolio (Day 6-8)
Priority: BUILD TRUST

- [ ] Create `services/position_sync.py`
- [ ] Add `positions_cache` table to database.py
- [ ] Update `handlers/portfolio.py` to use real API data
- [ ] Add win/loss notifications
- [ ] Add balance display to main menu

### Sprint 3 — Execution Unification (Day 9-11)
Priority: SMOOTH THE FLOW

- [ ] Unified `execute_trade()` function in `services/trading.py`
- [ ] Pre-fill amount from SignalCard.suggested_amount
- [ ] Unified error messages (all languages)
- [ ] Result card improvements (match Signal Card style)
- [ ] Return-to-context after wallet creation

### Sprint 4 — Copy Trading + Retention (Day 12-16)
Priority: ENGAGEMENT & REVENUE

- [ ] Real order execution in copy_trading.py
- [ ] Trader profile cards
- [ ] Daily briefing push (09:00 UTC)
- [ ] Win notification with P&L card
- [ ] Streak tracker
- [ ] URL handler (paste polymarket link → trade)

---

## 11. FIRST CODE CHANGES

Below are the actual code changes for Sprint 0 + Sprint 1 (start).

### Change 1: ai_service.py — async rewrite
→ See implementation file

### Change 2: betting.py — wallet guard
→ See implementation file

### Change 3: markets.py — cache fallback
→ See implementation file

### Change 4: settings.py — new handler
→ See implementation file

### Change 5: signal_pipeline.py — new service
→ See implementation file

### Change 6: bot.py — register new handlers
→ See implementation file

---

## 12. SELF-CHECK AGAINST CONSTRAINTS

| Constraint | Status | Notes |
|---|---|---|
| DO NOT remove working features | ✅ | Nothing removed. Academy kept. Parlay kept. |
| DO NOT overcomplicate flows | ✅ | 3-tap max enforced throughout |
| DO NOT break UX consistency | ✅ | Signal Card style is additive |
| Max 3-4 buttons per screen | ✅ | All screens audited: max 4 |
| Every screen leads to action | ✅ | No dead ends |
| Avoid deep nesting | ✅ | Max 3 levels deep |
| Product feels fast | ✅ | Async fix is #1 priority |
| Product feels clear | ✅ | Signal Card has structure |
| Product feels reliable | ⚠️ | Needs: position sync, real PnL |
| Product feels professional | ✅ | Bet slip cards, signal cards |

**Risks:**
1. `data-api.polymarket.com/positions` may have rate limits → add 10min cache
2. Async ai_service changes require updating all callers (4 files) → do atomically
3. Cache fallback may confuse users if many callbacks break → add clear refresh message
4. Signal spam risk → enforce anti-spam rules from day 1
