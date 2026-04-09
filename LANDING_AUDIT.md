# PolyScore Landing Page — Full Redesign Audit

**Site:** https://polyscore-bot.vercel.app
**Date:** March 21, 2026
**Auditor:** Product/UX/Conversion specialist

---

## 1. Executive Verdict

The current PolyScore landing page functions like a feature dump with a hype wrapper. It has strong product depth (9 features, 15 academy lessons, 12 languages, security architecture) but buries that substance under competing visual noise, overclaimed copy, trust contradictions, and a scattered information hierarchy. The hero alone contains a badge, two headings, a paragraph, two CTAs, four stat counters, a scrolling ticker, and six floating animated shapes — all fighting for attention simultaneously. The comparison table is self-reported with no proof. Claims like "Never been hacked," "can never happen to you," and "Bot earns for you" create compliance risk and reduce credibility rather than building it. The page needs to be stripped down to a clean, premium, conversion-focused flow that leads with clarity over quantity.

---

## 2. What Feels Broken Right Now

- **Hero is a visual anxiety attack.** Badge + h1 + subtitle + 2 CTAs + 4 stat counters + scrolling ticker + 7 floating shapes + 2 glow layers + particle animations + grid background + pulsing CTA border — all competing above the fold. Nothing has priority.
- **"Bot earns for you" as headline** — sounds like a scam bot ad on Telegram, not a premium fintech product. The strongest products never say "earns for you." They say what the product does precisely.
- **"Official Polymarket Builder"** in ticker + title tag, but footer says **"Not affiliated with Polymarket Inc."** — direct trust contradiction. A user who reads both will distrust the entire page.
- **"Never been hacked"** as a trust signal — this is a temporal claim that ages catastrophically. The day it's no longer true, it becomes a legal liability. Also, no product that's been live for months can credibly make this claim; it's like a restaurant saying "never poisoned anyone."
- **"This can never happen to you"** — absolute guarantees about security are amateur and legally risky. Nothing "can never happen."
- **Comparison table is 100% self-reported** — no citations, no links, no third-party verification. Claiming "✓ Never hacked" vs competitors' "✓" gives PolyScore no differentiation and looks like it was made up.
- **"Everything competitors forgot to build"** — arrogant framing. It implies competitors are stupid. Premium products don't punch down; they demonstrate superiority through product, not trash talk.
- **Markets section says "Every sport. Every outcome"** — but the bot now supports crypto, politics, business, science, and world markets. The landing page is outdated.
- **9 feature cards** is too many for one grid. After card 4-5, cognitive load kills engagement. Users don't read 9 cards.
- **Section order makes no persuasion sense.** Features → Compare → How it Works → Security → Markets → Academy → Languages → CTA. Security should be earlier (objection handling). How it Works should be much earlier. Markets should not be a separate section.
- **Ticker strip** with "★ OFFICIAL POLYMARKET BUILDER" × 2 and "★ 20% FROM PROFIT ONLY" feels like a crypto scam marquee, not a premium product signal.
- **Footer stat inconsistency:** hero says "$22B Polymarket 2025 volume" but footer says "$7B+ monthly volume" — which is it? Even if both are true (annual vs monthly), the user sees different numbers and loses trust.
- **CTA button has infinite pulsing glow animation** — this screams "click me!" in a desperate way. Premium products use static or very subtle hover states.
- **Mobile: two full-width stacked buttons** in hero push the stats below the fold entirely. The hero on mobile is likely: badge → large title → paragraph → Telegram button → See Features button → then scroll for anything else. That's a lot of dead space before the user sees any social proof or value.
- **The light-mode body with dark hero/CTA/footer** creates a disjointed feel — like three different design systems stitched together.
- **30+ CSS animations** running simultaneously (particles, glows, orbits, pulses, shimmers, floats, spins, tickers) — performance concern on low-end devices, visual clutter on all devices.

---

## 3. Critical Trust and Messaging Risks

| Problematic Element | Why It Hurts | What To Do Instead |
|---|---|---|
| **"Bot earns for you"** (h1) | Sounds like a get-rich-quick bot ad. Regulators flag this language. | → "Automated trading on Polymarket" or "AutoTrade algorithm for Polymarket" |
| **"Official Polymarket Builder"** + **"Not affiliated with Polymarket"** | Direct contradiction. User sees "Official" then "Not affiliated" — destroys trust in one scroll. | → Use "Polymarket Builder Program member" (factual, not "Official"). Remove from ticker/title tag. Keep only as a small badge. |
| **"Never been hacked"** | Unfalsifiable temporal claim. Becomes a liability the moment it's false. | → "AES-256 encryption + self-custody option" — describe the architecture, not the outcome. |
| **"This can never happen to you"** | Absolute security guarantee = legal risk + credibility damage. | → "Our architecture is designed to prevent this class of attack." |
| **"We never see your key"** | Only true for self-custody mode. Misleading for managed wallets. | → Clarify: "In self-custody mode, your key never leaves your device." |
| **"We win on every metric"** | Self-awarded victory in a self-made table. Arrogant + unverifiable. | → "How PolyScore compares" — neutral framing, let the data speak. |
| **"Everything competitors forgot to build"** | Punching down. Competitors didn't "forget" — they made different choices. | → "Built for traders who need more" or remove tagline entirely. |
| **"Earn on autopilot"** (step 3 + CTA) | Passive income language attracts regulatory scrutiny. | → "Your algorithm trades while you focus on other things." |
| **"Ready to earn on autopilot?"** (final CTA) | Same issue. "Earn" + "autopilot" together = red flag for financial regulators. | → "Ready to start AutoTrading?" |
| **Comparison: "✗ not disclosed"** for competitors' encryption | Implies they're hiding something, but you don't know their architecture. | → Use "—" (unknown) or remove encryption row entirely. |

---

## 4. Desktop UX Audit

### 4.1 Above the Fold (Hero)
**Problem:** 15+ competing elements. No single focal point. The eye bounces between the badge, the animated title, the subtitle paragraph, two buttons, four stat counters, a scrolling ticker, and floating shapes.

**Fix:**
- Remove ticker strip entirely
- Remove floating shapes (7 shapes, 2 glows, particles)
- Keep: badge (simplified) → h1 → one-line subtitle → single CTA → stat strip (3 stats max)
- Remove "See Features →" secondary CTA — it dilutes the primary action

### 4.2 Stats Bar
**Problem:** Four stats with large 38px numbers + labels feel like a dashboard, not a landing page. "24/7 AutoTrade hours" is a meaningless stat — every bot runs 24/7.

**Fix:** Reduce to 3 meaningful stats. Move to a horizontal bar below hero. Smaller treatment.

### 4.3 Features Grid
**Problem:** 9 cards in a grid is overwhelming. Cards have inconsistent content density. Some highlights are marketing ("Works while you sleep"), some are technical ("AES-256").

**Fix:**
- Lead with top 4 features in a 2×2 grid
- Remaining 5 collapse into an expandable section or relocate to dedicated pages
- Standardize card content: icon + title + 1-2 sentence description. Remove highlight badges from cards.

### 4.4 Comparison Table
**Problem:** Cramped on desktop, unusable on mobile (horizontal scroll with min-width: 700px). Self-reported data. "★ Best" badge on PolyScore column is self-awarded.

**Fix:**
- Redesign as vertical feature comparison cards (1 card per competitor) or a simpler checklist
- Remove the "★ Best" badge
- Soften language: "20% from profit ✓" → just "20% from profit"
- Remove claims you can't verify about competitors

### 4.5 Security Section
**Problem:** Good content, but the "hack warning" box (Polycule mention) reads as fear-mongering. The shield animation is distracting.

**Fix:**
- Lead with architecture description, not a competitor's hack story
- Move Polycule reference to a small footnote or case study link
- Remove shield floating animation
- Keep the 5 security points — they're the strongest content on the page

### 4.6 Spacing & Layout
- `section { padding: 100px 0; }` is excessive. 80px is sufficient.
- Feature cards have inconsistent padding and content height
- The `max-width: 1200px` container is fine but section headers should be text-centered with `max-width: 640px`
- `.section-sub { max-width: 560px; }` — good, but not centered (needs `margin: 0 auto`)
- Light body → dark hero → light sections → dark CTA → dark footer = 4 mode switches. Choose one: either full dark or light with dark hero only.

---

## 5. Mobile UX Audit

### 5.1 Hero (< 768px)
- Two full-width stacked buttons: `flex-direction: column; gap: 12px;` — the secondary "See Features" button takes up prime mobile real estate for a scroll action. **Remove it.**
- `min-height: 100svh` forces the entire viewport to be hero. On a small phone, this means badge + title + subtitle + 2 buttons fill the screen, and stats require scrolling. The hero should be tall but not forced to 100vh on mobile.
- `padding-top: 100px !important` — too much padding. The nav is 68px, so 80px top padding is sufficient.

### 5.2 Feature Cards
- `grid-template-columns: 1fr` with `gap: 14px` — 9 cards stacked vertically = massive scroll distance. On a 390px phone, this is ~3600px of feature cards alone.
- **Fix:** Show 3-4 cards, collapse the rest behind "Show all features" toggle.

### 5.3 Comparison Table
- `min-width: 560px` forces horizontal scroll on all phones. Tables with horizontal scroll are hostile on mobile.
- **Fix:** Replace with stacked cards on mobile, or a vertical checklist format.

### 5.4 Markets Grid
- `grid-template-columns: repeat(3, 1fr)` with `gap: 10px` — 8 chips in 3 columns means uneven last row (2 chips in a 3-col grid). Looks broken.
- **Fix:** Use `repeat(2, 1fr)` on mobile, or redesign as a horizontal scroll strip.

### 5.5 Security Grid
- `grid-template-columns: 1fr` with visual card moved to `order: -1` — this means on mobile the shield visual appears first, then the 5 security points. The visual is decorative; the points are the content. **Remove the visual card on mobile entirely**, or make it very small.

### 5.6 Typography
- `h1: clamp(36px, 9vw, 58px)` on mobile — on a 390px phone, 9vw = 35px. The clamp minimum is 36px. Fine.
- But `h2: clamp(26px, 7vw, 40px)` — 7vw on 390px = 27px. This is small for section headers.
- Fix: `clamp(28px, 8vw, 44px)` for h2 on mobile.

### 5.7 CTA Section
- `padding: 72px 0` is fine.
- `h2: clamp(28px, 8vw, 48px)` — adequate.
- CTA button is full-width which is correct.

### 5.8 Performance
- 30+ CSS animations + 2 canvas elements + intersection observers + multiple radial gradients = heavy paint. On mobile: `#blockchain-canvas`, `#network-canvas`, `.hero-shape` are hidden (`display: none`), which is good.
- But `body::before` (fixed background gradient) and `.grid-bg` (fixed grid lines) still render on mobile — these should be hidden too.

---

## 6. Recommended New Information Architecture

### Section 1: Nav (sticky)
- **Goal:** Brand + primary CTA always visible
- **Content:** Logo | (desktop: Features, Security, Academy) | CTA button
- **UI:** Dark, glass-blur nav. No ticker.
- **Mobile:** Logo + CTA button only. Hamburger optional.

### Section 2: Hero
- **Goal:** Communicate what this is, who it's for, single CTA
- **Content:**
  - Small badge: "Polymarket Builder Program"
  - h1: "AutoTrade on Polymarket." (full stop, no second line)
  - Subtitle: "Algorithm trades 24/7 across crypto, sports, politics, and more. Connect your wallet, set your strategy. We take 20% from profit only."
  - One CTA: "Open in Telegram"
  - Trust strip below: "AES-256 encryption · 12 languages · On-chain settlement"
- **UI:** Dark gradient, clean. No shapes, no particles, no ticker.
- **Mobile:** Badge → h1 → subtitle → CTA → trust strip. No 100vh lock.

### Section 3: How It Works (moved UP)
- **Goal:** Reduce friction immediately — show it's easy
- **Content:** 3 steps: Open bot → Fund USDC → AutoTrade starts
- **UI:** Horizontal 3-card strip with numbered badges. Light background.
- **Mobile:** Vertical stack, no connector lines.

### Section 4: Key Features (reduced)
- **Goal:** Show top 4 differentiators
- **Content:**
  1. AutoTrade Algorithm
  2. Copy Trading
  3. AI Market Analysis
  4. Price Alerts
- **UI:** 2×2 grid. Clean cards, no highlight badges.
- **CTA:** "See all 9 features →" link (not button)
- **Mobile:** 1 column, 4 cards max visible.

### Section 5: Markets
- **Goal:** Show breadth of tradeable markets
- **Content:** Updated for new categories: Sports, Crypto, Politics, Business, Science, World
- **UI:** Horizontal chip strip or icon grid. Minimal.
- **Mobile:** 2-column grid or horizontal scroll.

### Section 6: Security (objection handling)
- **Goal:** Address "is my money safe?" early
- **Content:** 4 key points (AES-256, cloud-only master key, self-custody option, on-chain settlement). No Polycule hack story above the fold.
- **UI:** Clean list with small icons. No floating shield.
- **Mobile:** Vertical stack.

### Section 7: Comparison (proof)
- **Goal:** Show why PolyScore is better, without arrogance
- **Content:** Redesigned as "PolyScore vs. others" — focus on 5 key differentiators only (languages, alerts, academy, encryption, AI analysis)
- **UI:** Simple checklist or card format. Remove full table.
- **Mobile:** Stacked cards, not horizontal table.

### Section 8: Academy (depth)
- **Goal:** Show educational value
- **Content:** 5 modules with XP
- **UI:** Horizontal scroll strip of module cards
- **Mobile:** Horizontal scroll (not stacked)

### Section 9: Languages (social proof)
- **Goal:** Demonstrate global reach
- **Content:** 12 language pills
- **UI:** Centered flex row. Keep minimal.
- **Mobile:** Wrap to 3-4 per row.

### Section 10: Final CTA
- **Goal:** Convert
- **Content:** "Start AutoTrading on Polymarket" + CTA button + small trust reminder
- **UI:** Dark section, one button, no animations
- **Mobile:** Full-width button.

### Section 11: Footer
- **Goal:** Legal + links
- **Content:** Links, copyright, risk disclaimer
- **UI:** Simple dark footer
- **Fix:** Remove "Not affiliated" if you also remove "Official" claims. Or keep both but never in contradicting positions.

---

## 7. Design System Direction

### Typography
- **Font:** Inter (keep)
- **h1:** 56-72px desktop, 36-42px mobile. Weight 800. Letter-spacing: -2px.
- **h2:** 36-48px desktop, 28-36px mobile. Weight 800.
- **Body:** 16px, line-height 1.7, color: `#475569`
- **Labels/tags:** 11-12px, weight 700, uppercase, 2px letter-spacing

### Spacing
- **Section padding:** 80px desktop, 56px mobile
- **Container:** max-width 1100px (reduce from 1200px)
- **Section header text:** max-width 600px, centered
- **Card grid gap:** 20px desktop, 14px mobile

### Cards
- **Border-radius:** 16px (standardize; currently varies 12-24px)
- **Border:** 1px solid `rgba(0,0,0,0.06)`
- **Padding:** 28px desktop, 20px mobile
- **Shadow:** `0 1px 3px rgba(0,0,0,0.04)` (reduce from current heavy shadows)
- **Hover:** subtle border-color change only, no translateY, no box-shadow explosion

### Buttons
- **Primary:** `background: var(--poly-green)` solid, no gradient, no glow animation, no `::before` border rotate
- **Border-radius:** 10px
- **Padding:** 14px 28px
- **Hover:** darken 10%, subtle shadow
- **One primary CTA per viewport.** No competing buttons.

### Badges & Tags
- **Section tags:** Keep but simplify. Remove border, just `background: rgba(0,200,83,0.08); color: var(--poly-green); padding: 4px 12px; border-radius: 6px;`
- **Feature highlights:** Remove entirely. Move that info into card descriptions.

### Tables
- **Remove comparison table.** Replace with card-based comparison or simple checklist.
- If table must stay: `min-width: auto`, use `@media` to stack on mobile.

### Backgrounds
- **Choose one mode.** Recommendation: dark theme throughout (like the hero). Consistent dark bg eliminates the jarring light↔dark transitions.
- **OR:** Light theme with dark hero/CTA only (current approach, but cleaner).
- **Remove:** `.grid-bg`, `body::before` gradient, `#network-canvas`, `#blockchain-canvas`.

### Motion
- **Kill:** all infinite CSS animations. Ticker, particle float, glow breathe, shield float, step glow pulse, grad-shift, shape orbits, ring-spin, CTA glow, badge pulse.
- **Keep:** `fadeUp` on scroll (intersection observer reveal). Card hover border-color transition.
- **Rule:** No element should animate unless the user interacts with it or scrolls it into view. Once.

### Icons
- **Standardize:** All SVG icons should be 24x24, stroke-width 1.5, same color family.
- **Feature icons:** 48x48 container with 24x24 icon inside. Consistent bg treatment.

### Color
- **Green:** `#00C853` as accent. Use sparingly — CTA, badges, active states only.
- **Blue:** `#1565C0` as secondary. Minimal usage.
- **Text:** `#0f172a` headings, `#475569` body, `#64748b` muted.
- **Remove:** All `text-shadow`, `filter: drop-shadow` on text, colored `box-shadow` on text elements.

---

## 8. Copy Rewrite Direction

| Current Pattern / Claim | Problem | Better Direction |
|---|---|---|
| "AutoTrading on Polymarket. Bot earns for you." | "Bot earns for you" = scam bot energy | "AutoTrade on Polymarket." (clean, product-led) |
| "Everything competitors forgot to build" | Arrogant, punching down | "Built for traders who want more." or remove |
| "We win on every metric" | Self-awarded victory | "How PolyScore compares" |
| "Side-by-side against the top Polymarket bots. The numbers speak for themselves." | Self-referential boasting | "A quick comparison with other Polymarket tools." |
| "Connect wallet → bot finds arbitrage → you earn" | Oversimplified promise chain | "Connect wallet → configure your strategy → AutoTrade executes 24/7" |
| "Earn on autopilot" / "Ready to earn on autopilot?" | Passive income language, regulatory risk | "Start AutoTrading" / "Ready to start?" |
| "Never been hacked" | Temporal claim, ages badly | "AES-256 encrypted · self-custody available" |
| "This can never happen to you" | Absolute guarantee = liability | "Our architecture is designed to prevent this." |
| "We never see your key" | Only true for self-custody | "In self-custody mode, your key never leaves your device." |
| "No competitor offers this" (about Price Alerts) | Unverifiable superlative | "A feature most competitors lack" or just describe the feature |
| "The only prediction market education" | Superlative claim | "Comprehensive trading education — built in" |
| "★ OFFICIAL POLYMARKET BUILDER" (ticker, title) | Conflicts with "Not affiliated" in footer | "Polymarket Builder Program member" — use once, small |
| "Every sport. Every outcome." (Markets heading) | No longer true — bot now has crypto, politics, etc. | "Crypto. Sports. Politics. All Polymarket markets." |
| "Coming soon: Crypto markets, election markets..." | Already live in the bot! Landing page is outdated. | Remove "coming soon" — show the actual categories |
| "$22B Polymarket 2025 volume" (hero) vs "$7B+ monthly volume" (footer) | Two different numbers = confusion | Pick one. "$22B+ traded on Polymarket in 2025" and remove the other. |
| "Powered by Polymarket · Built on Polygon · $7B+ monthly volume" (footer) | "Powered by" implies affiliation | "Trades on Polymarket · Polygon network" |

---

## 9. Prioritized Action Plan

### Critical (Do First)
1. **Fix trust contradictions:** Remove "Official" from ticker/title. Align Builder status language. Resolve $22B vs $7B discrepancy.
2. **Rewrite hero h1:** Remove "Bot earns for you." Replace with clean product statement.
3. **Remove infinite animations:** Kill ticker, particle system, glow breathe, shield float, CTA pulse, shape orbits. Keep only scroll-triggered fadeUp.
4. **Update Markets section:** "Every sport. Every outcome" → reflect actual categories (crypto, politics, etc.). Remove "Coming soon" for features already live.
5. **Soften security claims:** "Never been hacked" → describe architecture. "Can never happen" → "designed to prevent."

### High Priority
6. **Restructure section order:** Hero → How It Works → Features (4 max) → Security → Comparison → Academy → CTA
7. **Reduce hero density:** Remove secondary CTA, reduce to 3 stats, remove ticker strip.
8. **Redesign comparison:** Replace table with cards/checklist. Remove self-awarded badges. Remove unverifiable competitor claims.
9. **Reduce feature cards from 9 to 4** above the fold, with expandable section for rest.
10. **Fix mobile:** Remove 100vh hero lock. Replace table with stacked cards. Limit feature cards.

### Medium Priority
11. **Unify color theme:** Either full dark or clean light-with-dark-hero. Remove grid background and body gradients.
12. **Standardize card system:** Consistent padding, radius, shadow, hover behavior.
13. **Improve mobile markets grid:** Fix uneven 3-column layout.
14. **Remove all text-shadows and colored drop-shadows.**
15. **Simplify CTA buttons:** Solid color, no gradient glow, no animated border.

### Nice-to-Have
16. **Add real social proof:** User count, Telegram member count, or testimonial.
17. **Add a product screenshot or animation** showing the actual bot interface.
18. **Dark mode toggle** or commit to one theme.
19. **Add a FAQ section** answering: "Is this safe?", "How do fees work?", "What is Polymarket?"
20. **Performance audit:** Reduce CSS animation count, lazy-load below-fold content.

---

## 10. Build Brief for Frontend Refactor

### Instructions for implementation:

**REMOVE:**
- Entire ticker/marquee element (`.ticker`, `.ticker-inner`)
- All floating hero shapes (`.shape-1` through `.shape-7`, `.hero-glow`, `.hero-glow2`)
- Both canvas elements (`#network-canvas`, `#blockchain-canvas`)
- Particle system and related CSS/JS
- CTA button `::before` animated border
- All `@keyframes` except `fadeUp` and basic hover transitions
- `body::before` gradient overlay
- `.grid-bg` background grid
- "See Features →" secondary CTA button from hero
- "★ Best" winner badge from comparison table
- Feature highlight badges (`.feature-highlight`)
- Shield floating animation
- Stats counter animation JS (simple render is fine)
- All `text-shadow` and `filter: drop-shadow` on text elements

**SIMPLIFY:**
- Hero: badge → h1 → subtitle (1 line shorter) → 1 CTA → trust strip
- Feature cards: reduce to top 4 (AutoTrade, Copy Trading, AI Analysis, Price Alerts)
- Add "Show all features" expand link for remaining 5
- Comparison: convert table to card format or vertical checklist
- Stats: max 3 (remove "24/7 AutoTrade hours" — meaningless)
- Button styles: solid green background, no gradient, no glow, 10px radius

**REBUILD:**
- Markets section: new categories (Crypto, Politics, Business, Science, World, Sports) instead of sports-only
- Hero h1: "AutoTrade on Polymarket." — single clean line
- Hero subtitle: "Algorithm trades across crypto, sports, politics and more. 20% from profit only."
- Section order: Hero → How It Works → Features → Markets → Security → Compare → Academy → Languages → CTA → Footer
- Comparison: card-based, 3-4 key differentiators, neutral language
- Mobile comparison: stacked vertically, no horizontal scroll

**CENTRALIZE:**
- All section headers: `text-align: center; max-width: 600px; margin: 0 auto;`
- Container: reduce to `max-width: 1100px`
- Card padding: standardize to 28px desktop, 20px mobile
- Card border-radius: standardize to 16px
- Section padding: 80px desktop, 56px mobile

**FIX ON MOBILE:**
- Remove `min-height: 100svh` from hero on mobile — let it be natural height
- Comparison: stack cards vertically, never show table on < 768px
- Markets grid: `repeat(2, 1fr)` instead of `repeat(3, 1fr)` on mobile
- Remove `.container { padding-top: 100px !important }` — use 84px (68px nav + 16px breathing room)
- Security visual card: hide or minimize on mobile
- Remove body background effects on mobile (`.grid-bg`, `body::before`)

**VALIDATE AFTER:**
- No "Official" + "Not affiliated" contradiction exists
- No "bet/betting/ставка" words in user-facing text
- Markets section shows all 6 categories, not just sports
- "$22B" appears only once with clear context
- No infinite CSS animations remain
- Mobile hero fits in viewport without scroll to see CTA
- Comparison is readable on 375px screen without horizontal scroll
- Lighthouse performance score > 85 on mobile
- All 12 language translations are consistent with new copy

---

## 11. Self-Check

### Assumptions & Inferences:
- **Mobile layout inferred from CSS media queries** — not tested on actual device. Responsive breakpoints at 900px and 768px were read from code.
- **Lighthouse score not measured** — performance concern is inferred from animation count and canvas elements.
- **Competitor data unverified** — comparison table claims about PolyGun, PolyCop, PolyBot cannot be verified from this audit.
- **User count / traction data unknown** — audit assumes no social proof exists on page because none was found.
- **"Coming soon" features assumed to be live** based on the bot code changes made in this session (crypto, politics categories added to handlers).

### Constraint Review:
- ✅ Grounded in current site (all findings reference specific elements, CSS lines, or copy)
- ✅ Concrete and execution-focused (prioritized action plan, build brief)
- ✅ Desktop AND mobile covered throughout
- ✅ Copy distinguished as: keep / rewrite / soften / remove (table in section 8)
- ✅ Visual system references provided (spacing, typography, color rules)
- ✅ Trust/compliance risks flagged with specific alternatives
- ✅ No generic advice like "improve UX"
