# PolyScore Landing Page — Redesign Blueprint

Production-ready spec. No audit repetition. Only solutions.

---

## 1. Final Landing Page Structure (top → bottom)

```
NAV (sticky)
HERO
TRUST STRIP (inline, not ticker)
HOW IT WORKS (3 steps)
FEATURES (4 visible + expand)
MARKETS (updated categories)
SECURITY (architecture-based)
COMPARISON (card format)
ACADEMY (compact)
LANGUAGES (compact)
FINAL CTA
FOOTER
```

Total: 11 sections. Down from 13. No ticker. No dividers between every section.

---

## 2. Section-by-Section Rewrite

### 2.1 NAV

**Keep:** Logo | Desktop links (Features, Security, Academy) | Language switcher | CTA button

**Changes:**
- Remove "Official Builder" from `<title>` tag
- New title: `PolyScore — AutoTrade Algorithm for Polymarket`
- New meta description: `AutoTrade algorithm for Polymarket. Trades 24/7 across crypto, sports, politics. AES-256 encryption. 12 languages. 20% from profit only.`
- Nav CTA text: `Open Bot →` (keep)
- Remove: no changes to nav layout, it works

**Nav CTA style fix:** Remove `box-shadow: 0 4px 18px rgba(0,200,83,0.4)` — replace with subtle `box-shadow: 0 2px 8px rgba(0,200,83,0.2)`

---

### 2.2 HERO

**Goal:** Single clear product statement → single CTA → 3 trust signals

**Final copy (EN):**

```
Badge: "Polymarket Builder Program"

h1 line 1: "AutoTrade"
h1 line 2: "on Polymarket."

Subtitle: "Algorithm trades 24/7 across sports, crypto, politics, and more. Connect your wallet, set your strategy. 20% from profit only."

CTA: "Open in Telegram" (single button, no secondary)

Trust strip (below CTA, small text):
"AES-256 encryption · 12 languages · On-chain settlement · Self-custody available"
```

**Final copy (RU):**

```
Badge: "Polymarket Builder Program"

h1 line 1: "Автоторговля"
h1 line 2: "на Polymarket."

Subtitle: "Алгоритм торгует 24/7 на рынках спорта, крипто, политики и других. Подключи кошелёк, выбери стратегию. 20% только с прибыли."

CTA: "Открыть в Telegram"

Trust strip:
"AES-256 шифрование · 12 языков · Расчёты на блокчейне · Можно подключить свой кошелёк"
```

**REMOVE from hero:**
- "See Features →" secondary button
- 4 stat counters (20%, 12, $22B, 24/7)
- Second badge ("Live on Telegram · 12 Languages")
- `h1 line 3` ("Bot earns for you." / gradient text)
- All floating shapes (.shape-1 through .shape-7)
- .hero-glow, .hero-glow2
- #particles-container
- hero::after pulsing line

**KEEP:**
- Dark gradient background
- Subtle `::before` mesh overlay (but reduce opacity to 0.08)
- .badge with green dot (but simplify to one badge)
- fadeUp animations (but run ONCE, not infinite)

**UI notes:**
- Hero should NOT be `min-height: 100vh`. Use `min-height: 80vh` desktop, `auto` mobile.
- Trust strip: `font-size: 13px; color: rgba(255,255,255,0.5); margin-top: 32px;` — inline text, not cards.
- Remove CTA `::before` animated border. Remove `cta-glow-btn` animation. Static green button with hover darken.

---

### 2.3 TRUST STRIP (replaces ticker)

**DELETE entirely:**
- "POLYMARKET POWER STRIP" (dark marquee with "★ OFFICIAL POLYMARKET BUILDER")
- Sports ticker (MLB, NBA, UFC odds)
- Both `<div>` elements between hero and features

**Replace with:** Nothing. The trust strip is now part of the hero (see 2.2).

---

### 2.4 HOW IT WORKS (moved to position 3, up from 6)

**Goal:** Show ease of use immediately after hero

**Final copy:**

```
Tag: "How it works"
h2: "Start in under 60 seconds"

Step 1: "Open the bot"
"Find @PolymarketMAMA_Bot on Telegram. Tap Start. Your Polygon wallet is created instantly."

Step 2: "Fund with USDC"
"Send USDC via Polygon network from any exchange. Arrives in 5–15 minutes."

Step 3: "AutoTrade begins"
"The algorithm identifies opportunities and trades across all Polymarket categories. You choose the strategy — it executes 24/7."
```

**RU:**
```
Tag: "Как это работает"
h2: "Старт за 60 секунд"

Шаг 1: "Открой бота"
"Найди @PolymarketMAMA_Bot в Telegram. Нажми Start. Кошелёк Polygon создаётся мгновенно."

Шаг 2: "Пополни USDC"
"Отправь USDC через сеть Polygon с любой биржи. Приходит за 5–15 минут."

Шаг 3: "AutoTrade запускается"
"Алгоритм находит возможности и торгует по всем категориям Polymarket. Ты выбираешь стратегию — он исполняет 24/7."
```

**Changes from current:**
- "Earn on autopilot" → "AutoTrade begins" (removes "earn" promise)
- Step 3 description completely rewritten — no "passive income" language
- "No app download. No registration. No KYC." subtitle — **keep**, it's good and factual

**UI notes:**
- 3 cards in a row, horizontal on desktop
- Step number circles: static green, no pulsing animation
- Remove step-connector lines (they break on mobile anyway)
- Remove step-arrow elements

---

### 2.5 FEATURES (reduced from 9 → 4+5)

**Goal:** Show top 4 differentiators. Expandable for completeness.

**Final copy:**

```
Tag: "Features"
h2: "Built for serious traders"
Sub: (remove entirely — the h2 is sufficient)
```

**RU:**
```
Tag: "Возможности"
h2: "Создан для серьёзных трейдеров"
```

**Primary 4 cards (always visible):**

| # | Title (EN) | Title (RU) | Description (EN) | Description (RU) |
|---|---|---|---|---|
| 1 | AutoTrade Algorithm | Алгоритм AutoTrade | Trades 24/7 across all Polymarket categories. Four strategies: cross-platform arbitrage, behavioral fades, micro market making, event-driven. 20% from profit only. | Торгует 24/7 по всем категориям Polymarket. Четыре стратегии: кросс-платформенный арбитраж, поведенческие фейды, микро маркет-мейкинг, событийная. 20% только с прибыли. |
| 2 | Copy Trading | Копитрейдинг | Follow top Polymarket traders by ROI. Set your copy percentage, choose traders, and mirror their positions automatically. | Следи за лучшими трейдерами Polymarket по ROI. Установи процент копирования и автоматически повторяй их позиции. |
| 3 | AI Market Analysis | AI-анализ рынков | Claude AI calculates edge on every market. See what the price implies vs what data suggests — before you trade. | Claude AI рассчитывает edge на каждом рынке. Увидь, что подразумевает цена и что говорят данные — до открытия позиции. |
| 4 | Price Alerts | Ценовые алерты | Set a target price on any market. Get instant Telegram notification when it hits. Works across all categories. | Установи целевую цену на любом рынке. Получи моментальное уведомление в Telegram. Работает по всем категориям. |

**Secondary 5 cards (collapsed, behind "Show all features" link):**

| # | Title | Description |
|---|---|---|
| 5 | AES-256 Encrypted Keys | Private keys encrypted with AES-256 + HMAC-SHA256. Master key stored in cloud environment only. Self-custody option available. |
| 6 | 12 Languages | Full localization: menus, alerts, academy, notifications. RU, EN, ES, PT, TR, ID, ZH, AR, FR, DE, HI, JA. |
| 7 | Built-in Academy | 5 modules, 15 lessons with quizzes and XP. Learn edge calculation, Kelly Criterion, whale watching, and trader psychology. |
| 8 | Parlay Builder | Combine 2–5 outcomes into a parlay. PolyScore calculates combined probability, implied odds, and expected value. |
| 9 | Leaderboard | Track traders by profit, win rate, and ROI. Share trade slips as cards. |

**REMOVE from all cards:**
- `.feature-highlight` badges ("Works while you sleep", "Bank-grade security", etc.)
- "No competitor offers this" language
- "Competitors: English only" language

**UI notes:**
- 2×2 grid desktop, 1 column mobile
- After 4 cards: `<button class="show-more">Show all features ↓</button>` — toggles visibility of remaining 5
- Cards: simplified — icon + title + description. No badges.
- Card descriptions: max 2 sentences.

---

### 2.6 MARKETS (updated)

**Goal:** Show breadth of categories. Remove sports-only framing.

**Final copy:**

```
Tag: "Markets"
h2: "Crypto. Sports. Politics. And more."
Sub: "PolyScore trades across all major Polymarket categories — not just sports."
```

**RU:**
```
Tag: "Рынки"
h2: "Крипто. Спорт. Политика. И другое."
Sub: "PolyScore торгует по всем основным категориям Polymarket — не только спорт."
```

**Market chips (updated for new categories):**

| Emoji | Name EN | Name RU | Sub |
|---|---|---|---|
| ₿ | Crypto | Крипто | BTC, ETH, DeFi |
| ⚽ | Sports | Спорт | MLB, NBA, UFC, F1 |
| 🏛️ | Politics | Политика | Elections, Policy |
| 💼 | Business | Бизнес | Tech, Finance |
| 🔬 | Science | Наука | AI, Space, Climate |
| 🌍 | World | Мир | Events, Culture |

**REMOVE:**
- "Every sport. Every outcome." heading
- "Coming soon: Crypto markets, 15-minute micro-markets, election markets" — these are already live
- Individual sport chips (MLB, NBA, UFC, NHL, F1, Soccer, NFL, Tennis) — replace with category chips above
- "From MLB to UFC to Formula 1" subtitle

**UI notes:**
- 6 chips in a 3×2 grid desktop, 2×3 mobile
- Chips: icon + name + sub text. Simple white cards.
- No sport-specific odds display

---

### 2.7 SECURITY

**Goal:** Architecture-based trust. No outcome claims.

**Final copy:**

```
Tag: "Security"
h2: "Your keys. Your funds. Protected by design."
Sub: "Non-custodial architecture with AES-256 encryption and self-custody option."
```

**RU:**
```
Tag: "Безопасность"
h2: "Ваши ключи. Ваши средства. Защита архитектурой."
Sub: "Некастодиальная архитектура с AES-256 шифрованием и возможностью самостоятельного хранения."
```

**Security points (keep 4, remove 1):**

1. **AES-256 Encrypted Keys** — "Private keys encrypted with AES-256 + HMAC-SHA256 before storage. Even if the database is compromised, keys are unusable without the separate master key."
2. **Cloud-Isolated Master Key** — "The encryption master key lives exclusively in cloud environment variables. An attacker would need both database and cloud access simultaneously."
3. **Self-Custody Option** — "Connect your own MetaMask or Polygon wallet. In self-custody mode, your private key never touches our infrastructure."
4. **On-Chain Settlement** — "All trades settle on Polymarket's smart contracts on Polygon. Funds go directly to your wallet when a market resolves."

**REMOVE:**
- **"Tamper Detection"** point — too technical for a landing page, covered by HMAC mention in point 1
- **"Never Been Hacked"** badge and visual card
- **Polycule hack warning box** — fear-mongering about a competitor's breach
- **Shield floating animation**
- **Entire right-column visual card** (`.security-visual`)

**Rewrite to REMOVE:**
- "this can never happen to you" → removed
- "We never see your key" → "In self-custody mode, your key never touches our infrastructure"
- "We built PolyScore so this can never happen" → removed

**UI notes:**
- Single column layout, no grid split
- 4 points as a clean list with small icons
- Light background section
- No floating shield, no hack warning card

---

### 2.8 COMPARISON (redesigned)

**Goal:** Neutral comparison. Card format. No table.

**Final copy:**

```
Tag: "Comparison"
h2: "How PolyScore compares"
Sub: (none — h2 is enough)
```

**RU:**
```
Tag: "Сравнение"
h2: "Чем PolyScore отличается"
```

**Format: 5 comparison rows (not a table)**

Each row is a simple `div` with:
- Feature name
- PolyScore value
- "Others" value (generalized, not specific competitors)

```
| Feature          | PolyScore              | Most competitors        |
|------------------|------------------------|-------------------------|
| Languages        | 12                     | English only            |
| Price alerts     | ✓ Any market           | —                       |
| Trading academy  | ✓ 15 lessons + quizzes | —                       |
| Key encryption   | AES-256 + self-custody | Not disclosed           |
| AI analysis      | ✓ Per-market edge calc | Limited or none         |
```

**REMOVE:**
- Full `<table>` element
- Named competitors (PolyGun, PolyCop, PolyBot) — we can't verify their features
- "★ Best" winner badge
- "We win on every metric" heading
- "The numbers speak for themselves" subtitle
- Row: "Platform fee" — leads to fee comparison which isn't a clear win (our 20% vs their 0.5-1%)
- Row: "Copy trading" — everyone has it, not a differentiator
- Row: "Security: ✓ Never hacked" — removed per audit
- Row: "Market translation" — minor feature

**UI notes:**
- Simple alternating rows or horizontal cards
- PolyScore column: green text/check. Others: gray text.
- No horizontal scroll on any device
- `max-width: 700px; margin: 0 auto;` — centered, not full-width

---

### 2.9 ACADEMY (compact)

**Keep as-is** with one change:

**Copy changes:**
- h2: "Learn to win. Inside Telegram." → **"Trading education. Built in."**
- h2 RU: "Учись побеждать. В Telegram." → **"Обучение трейдингу. Встроено."**
- Sub: remove "The only prediction market education built right into the trading experience" → **"5 modules. 15 lessons. Quizzes and XP."**

**UI notes:**
- Keep 5 module cards in horizontal scroll
- No changes to card layout

---

### 2.10 LANGUAGES (compact)

**Keep as-is** with copy change:

- h2: "12 languages. One bot." — **keep**
- Sub: "No other bot comes close." → **remove this line**
- Rest of sub: keep factual part

**UI:** No changes needed. It's clean.

---

### 2.11 FINAL CTA

**Final copy:**

```
h2: "Ready to start AutoTrading?"
Sub: "Algorithm trades 24/7. 20% only from profit. 12 languages."
CTA: "Open PolyScore in Telegram"
```

**RU:**
```
h2: "Готовы начать AutoTrading?"
Sub: "Алгоритм торгует 24/7. 20% только с прибыли. 12 языков."
CTA: "Открыть PolyScore в Telegram"
```

**REMOVE:** "Ready to earn on autopilot?" — regulatory risk language

**UI notes:**
- Dark background (keep)
- Remove `.cta-glow` animated element
- Remove CTA button pulsing glow
- Static button with hover darken
- `cta-section::before` mesh — reduce opacity to 0.1

---

### 2.12 FOOTER

**Final copy:**

```
Line 1: "Trades on Polymarket · Polygon network"
Line 2: Links: Telegram Bot | Polymarket | Security | Academy
Line 3: "© 2026 PolyScore. Polymarket Builder Program member. Not an investment advisor."
Line 4: "Trading involves risk. Only trade what you can afford to lose."
```

**REMOVE:**
- "Powered by Polymarket" → "Trades on Polymarket" (removes affiliation implication)
- "$7B+ monthly volume" — inconsistent with hero's $22B, remove
- "Not affiliated with Polymarket Inc." — reworded to be part of disclaimer line

---

## 3. Design System Spec

### Typography

```css
/* Headings */
h1 { font-size: clamp(40px, 5.5vw, 72px); font-weight: 800; letter-spacing: -2px; line-height: 1.05; }
h2 { font-size: clamp(28px, 4vw, 48px); font-weight: 800; letter-spacing: -1.5px; line-height: 1.1; }
h3 { font-size: 18px; font-weight: 700; line-height: 1.3; }

/* Body */
body { font-size: 16px; line-height: 1.7; color: #475569; }
.muted { font-size: 14px; color: #64748b; }
.small { font-size: 13px; color: #94a3b8; }

/* Labels */
.tag { font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
```

### Spacing

```css
section { padding: 80px 0; }
@media (max-width: 768px) { section { padding: 56px 0; } }

.container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }
@media (max-width: 768px) { .container { padding: 0 16px; } }

/* Section header centering */
.section-header { text-align: center; max-width: 600px; margin: 0 auto 48px; }
@media (max-width: 768px) { .section-header { margin-bottom: 32px; } }
```

### Cards

```css
.card {
  background: #ffffff;
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: border-color 0.2s;
}
.card:hover {
  border-color: rgba(0,200,83,0.25);
}
/* NO translateY on hover. NO box-shadow explosion. NO ::after glow. NO ::before top bar. */

@media (max-width: 768px) {
  .card { padding: 20px; }
}
```

### Buttons

```css
.btn-primary {
  display: inline-flex; align-items: center; gap: 8px;
  background: #00C853;
  color: #fff;
  font-weight: 700; font-size: 16px;
  padding: 14px 28px;
  border-radius: 10px;
  text-decoration: none;
  transition: background 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(0,200,83,0.2);
}
.btn-primary:hover {
  background: #00a846;
  box-shadow: 0 4px 16px rgba(0,200,83,0.3);
}
/* NO gradient. NO animated ::before border. NO infinite glow animation. */
/* ONE primary CTA per viewport. */

@media (max-width: 768px) {
  .btn-primary { width: 100%; justify-content: center; font-size: 15px; padding: 14px 24px; }
}
```

### Layout Grids

```css
/* Features: 2x2 desktop, 1 col mobile */
.features-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
@media (max-width: 768px) { .features-grid { grid-template-columns: 1fr; gap: 14px; } }

/* Markets: 3x2 desktop, 2x3 mobile */
.markets-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 768px) { .markets-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; } }

/* Steps: 3 col desktop, 1 col mobile */
.steps-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
@media (max-width: 768px) { .steps-grid { grid-template-columns: 1fr; gap: 16px; } }
```

### Colors

```css
:root {
  --green: #00C853;
  --green-hover: #00a846;
  --green-subtle: rgba(0,200,83,0.08);
  --green-border: rgba(0,200,83,0.2);
  --text-heading: #0f172a;
  --text-body: #475569;
  --text-muted: #64748b;
  --text-faint: #94a3b8;
  --bg: #f8fafc;
  --card: #ffffff;
  --border: rgba(0,0,0,0.06);
  --hero-bg: linear-gradient(145deg, #071a2e 0%, #0a2540 50%, #0d3320 100%);
  --cta-bg: linear-gradient(145deg, #071a2e 0%, #0a2540 50%, #0d3320 100%);
}
```

### Motion Rules

```
ALLOWED:
- fadeUp on scroll (intersection observer, run ONCE per element)
- Card hover: border-color transition 0.2s
- Button hover: background transition 0.2s
- Nav scroll: background opacity transition

BANNED — DELETE ALL:
- @keyframes ticker
- @keyframes particle-float
- @keyframes glow-breathe
- @keyframes glow2-drift
- @keyframes cta-pulse
- @keyframes shape-orbit1, shape-orbit3, shape-float2, shape-float4, ring-spin
- @keyframes cta-glow-btn
- @keyframes badge-pulse
- @keyframes step-glow-pulse
- @keyframes shield-float
- @keyframes hero-line-pulse
- @keyframes grad-shift
- @keyframes border-rotate
- @keyframes icon-float
- @keyframes connector-pulse
- @keyframes countFlash
- @keyframes shape-line
All these are infinite CSS animations that run forever.
Only animation allowed: fadeUp (runs once) and CSS transitions on hover/focus.
```

---

## 4. Mobile Version Strategy

### Hero (< 768px)
- Remove `min-height: 100svh` → use `min-height: auto; padding: 120px 0 60px;`
- Remove secondary CTA button entirely
- Single full-width primary CTA
- Trust strip below CTA as wrapped text
- No stat counters on mobile

### Features
- 1 column, 4 cards visible
- "Show all features" toggle for remaining 5
- Card padding: 20px

### Markets
- 2 columns (not 3)
- Gap: 12px

### Security
- Vertical list, no grid split
- Remove security visual card entirely on mobile

### Comparison
- Vertical stacked rows, full width
- No table element, no horizontal scroll
- Each row: feature name → PolyScore value → Others value

### Academy
- 2 columns on mobile (keep current)
- Card padding: 16px

### Steps
- 1 column, remove connector lines
- Remove step-arrow elements

### Performance
- Hide `body::before`, `.grid-bg` on mobile
- All canvases already hidden (good)
- No infinite animations = major perf improvement

---

## 5. Frontend Refactor Instructions

### REMOVE (delete from HTML + CSS + JS)

```
HTML elements to delete:
- .hero-shape.shape-1 through .shape-7 (7 elements)
- .hero-glow, .hero-glow2
- #particles-container
- POLYMARKET POWER STRIP (dark marquee div, lines 862-868)
- .ticker + .ticker-inner (sports odds marquee, lines 870-886)
- hr.section-divider (between ticker and features)
- .btn-secondary "See Features →" from hero
- All .feature-highlight spans
- .winner-badge from comparison table
- .security-visual card (shield, "Never Been Hacked", hack warning)
- .step-arrow elements
- .step-connector elements
- #blockchain-canvas
- #network-canvas
- .grid-bg div
- Stat counter "24/7 AutoTrade hours" (4th stat)

CSS to delete:
- All @keyframes EXCEPT fadeUp
- .ticker, .ticker-inner styles
- .particle styles
- .hero-glow, .hero-glow2 styles
- .hero-shape, .shape-1 through .shape-7 styles
- .hero::after (pulsing bottom line)
- .btn-primary::before (animated border)
- .feature-highlight styles
- .winner-badge styles
- .hack-warning styles
- .sec-shield animation
- .step-connector styles
- .step-arrow styles
- body::before gradient (or hide on mobile)
- .grid-bg styles
- All card ::after glow-follow effects
- 3D tilt perspective on cards
- .stat-val:hover scale transform
- .stat-val.counting animation

JS to delete/modify:
- Particle generation function
- Counter animation (simplify to just display the number)
- Card 3D tilt tracking
- Mouse-follow glow on cards
- Ticker speed/duplicate logic
```

### SIMPLIFY

```
Hero:
- 2 badges → 1 badge ("Polymarket Builder Program")
- h1: remove line 3 ("Bot earns for you")
- Subtitle: rewrite (see section 2.2)
- 2 CTAs → 1 CTA
- 4 stats → trust strip (text only)
- Remove all hero decorative elements

Features:
- 9 cards → 4 visible + 5 collapsed
- Remove highlight badges from all cards
- Standardize card descriptions to ≤2 sentences

Comparison:
- Full <table> → simple row-based div layout
- 4 named competitors → generalized "Others" column
- 10 rows → 5 rows

Security:
- 2-column grid → single column list
- 5 points → 4 points (remove Tamper Detection)
- Remove visual card, shield, hack warning

CTA:
- Remove .cta-glow element
- Static button (no pulsing animation)
```

### REBUILD

```
Markets section:
- New heading: "Crypto. Sports. Politics. And more."
- New subtitle: "PolyScore trades across all major Polymarket categories."
- 6 new category chips: Crypto, Sports, Politics, Business, Science, World
- Remove 8 individual sport chips
- Remove "Coming soon" text
- Update all 12 language translations for market section

Comparison section:
- Delete <table>
- Build row-based comparison component:
  <div class="compare-row">
    <span class="compare-feature">Languages</span>
    <span class="compare-us">12</span>
    <span class="compare-others">English only</span>
  </div>
- 5 rows, centered, max-width: 700px

"Show all features" toggle:
- Add <button> after 4th feature card
- Add .features-expanded container (hidden by default)
- JS: toggle visibility on click

Hero trust strip:
- New element below CTA button
- Simple inline text with · separators
- No cards, no counters, no animation
```

### VALIDATE (after deployment)

```
Content checks:
□ No "Official Polymarket" anywhere (search "Official")
□ No "Bot earns for you" anywhere
□ No "Never been hacked" anywhere
□ No "can never happen" anywhere
□ No "earn on autopilot" anywhere
□ No "bet/betting/ставка" in user-facing text
□ Markets section shows 6 categories, not 8 sports
□ No "Coming soon" for already-live features
□ "$22B" appears max once with clear context
□ No "$7B+ monthly volume" in footer (removed)
□ Footer says "Polymarket Builder Program member" not "Official"

UX checks:
□ Hero CTA is visible without scroll on 375px phone
□ No horizontal scroll on any section at 375px
□ No infinite CSS animations (search "@keyframes" — only fadeUp should remain)
□ Comparison is readable on 375px without scroll
□ Feature "Show all" toggle works
□ All 12 languages load correct translations

Performance checks:
□ No <canvas> elements in DOM
□ No particle generation JS running
□ Lighthouse mobile performance > 85
□ Total CSS animations: 1 (fadeUp) + hover transitions
□ No fixed-position background decorations on mobile
```

---

## 6. Final Notes

### i18n Impact
The copy changes affect ALL 12 languages. The JS translations object near the end of index.html must be updated for every language. Key keys to update:

```
hero_h1_3: DELETE (remove "Bot earns for you" line entirely)
hero_sub: REWRITE (all 12 languages)
feat_h2: REWRITE (all 12 languages)
feat_sub: DELETE
how_h2: REWRITE (all 12 languages)
step3_h: REWRITE (all 12 languages)
step3_p: REWRITE (all 12 languages)
mkt_h2: REWRITE (all 12 languages)
mkt_sub: REWRITE (all 12 languages)
mkt_soon / mkt_soon_list: DELETE
sec_h2: REWRITE (all 12 languages)
sec_sub: REWRITE (all 12 languages)
cmp_h2: REWRITE (all 12 languages)
cmp_sub: DELETE
acad_h2: REWRITE (all 12 languages)
acad_sub: REWRITE (all 12 languages)
cta_h2: REWRITE (all 12 languages)
cta_sub: REWRITE (all 12 languages)
ft_risk: KEEP
```

That's ~15 keys × 12 languages = ~180 string updates. This is the largest work item.

### Section reorder in HTML
Current order in HTML file:
1. Hero → 2. Power Strip → 3. Ticker → 4. Features → 5. Compare → 6. How It Works → 7. Security → 8. Markets → 9. Academy → 10. Languages → 11. CTA → 12. Footer

New order:
1. Hero → 2. How It Works → 3. Features → 4. Markets → 5. Security → 6. Compare → 7. Academy → 8. Languages → 9. CTA → 10. Footer

This requires moving HTML blocks, not just CSS reorder.

---

## 7. Self-Check

| Constraint | Status |
|---|---|
| One primary CTA per screen | ✅ Hero has 1 CTA, final CTA has 1 CTA |
| Clean hierarchy > feature quantity | ✅ 4 visible features, not 9 |
| Premium tone > aggressive marketing | ✅ All hype language replaced |
| Mobile clarity > desktop decoration | ✅ All decorations removed, mobile layouts specified |
| No generic advice | ✅ Every section has exact copy and exact CSS |
| No re-auditing | ✅ Solutions only, no problem re-description |
| Implementation-ready | ✅ Remove/Simplify/Rebuild/Validate lists provided |
| All 12 languages addressed | ✅ i18n impact noted with key list |
| Trust contradictions resolved | ✅ "Official" removed, claims softened |
| Regulatory language cleaned | ✅ "earn", "autopilot", "never" removed from CTAs |

### Assumptions:
- All translations will be written by the developer (I provide EN + RU; other 10 languages need manual translation or AI generation)
- The "Show all features" toggle requires ~10 lines of JS
- Section reorder is a copy-paste operation in the HTML file
- Comparison competitor data will be generalized to "Others" since specific claims are unverifiable
