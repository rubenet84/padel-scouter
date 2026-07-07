## Exploration: Landing Page Redesign

### Current State

The current landing page (`app/templates/index.html`, 56 lines) is minimal:
- Hero section with emoji icon, title "Padel Scouter", subtitle, FIP 2026 badge, and two CTA buttons (login, API docs)
- Three feature cards (Power Level, AI Analysis, FIP 2026 Regulation)
- No landing-specific JS, no landing-specific CSS, no partial extraction
- Dark background inherited from base.html (`#0A0A0F`)

### Affected Areas

| File | Role | Impact |
|------|------|--------|
| `app/templates/index.html` | Landing page template | Full replacement — 56 lines → 10 sections |
| `app/templates/base.html` | Base template (navbar, footer, bg effects, fonts, Tailwind config, Chart.js, chatbot) | Navbar/footer may need minor updates for landing context. Auth check inline script stays. |
| `app/static/css/scouter.css` | Shared CSS (31 lines: emoji fix, power-glow, tab-active, scrollbar, card-hover) | May grow if new landing-specific shared utility classes emerge. Keep shared, add `landing.css` for section-specific styles. |
| `app/static/js/main.js` | Shared JS (logout, checkAuth, password strength) | Unchanged. Landing JS will be separate. |
| `app/api/v1/views.py` | View function serving `/` | Minimal change — may need to pass more context (mock stats, rankings, etc.) |
| `app/templates/partials/` | Partial conventions | Naming: `_section_name.html`. Currently 7 partials for player_detail. |

### Volatility Table

| Section | What Changes | Volatility Class |
|---------|-------------|------------------|
| **Navbar** | Auth state (logged-in vs anonymous), active page highlight, links | Navigation + Data |
| **Hero** | Power level display (mock vs real), scouter animation, CTA links | Design + Interaction + Data |
| **Trusted-by Metrics** | Counter values (mock vs API), counter animation speed | Data + Interaction |
| **Features** | Card copy, icons, order, number of cards (currently 3 → 6) | Design |
| **Analytics Preview** | Radar chart data, stat bars, win-rate donut (Chart.js), mock vs real | Design + Interaction + Data |
| **Rankings** | Table rows (mock vs API), column order, top-player cards | Data + Design |
| **AI Analysis** | Comparison content, improvement plan text, progress bar values | Data + Design |
| **Phone Mockups** | Image assets, layout, animation | Design |
| **CTA Section** | Button text, destination URL, urgency copy | Design + Navigation |
| **Footer** | Links, social icons, copyright year | Navigation + Design |

### Cohesion Map

```
Navbar ─────────────── auth state (from base.html)
  │
Hero ───────────────── stand-alone (scouter panel visual)
  │
Trusted-by Metrics ─── stand-alone (numeral counter animation)
  │
Features ───────────── stand-alone (static cards, no data dep)
  │
Analytics Preview ──── Chart.js (already in base.html CDN)
  │
Rankings ───────────── stand-alone (table + cards)
  │
AI Analysis ────────── stand-alone (progress bars + text)
  │
Phone Mockups ──────── static images
  │
CTA Section ────────── stand-alone (button links)
  │
Footer ─────────────── stand-alone (links)
```

All sections are **vertically independent** — no section depends on another. The page is a linear scroll with each section being a self-contained visual block.

Chart.js is the only external dependency shared across sections (analytics preview), and it's already loaded in `base.html`.

### Boundary Recommendations

#### Partial Files (one per visual section)
```
app/templates/partials/
├── _landing_navbar.html        (or keep in base.html — navbar is global)
├── _landing_hero.html          scouter panel, power level, CTA
├── _landing_metrics.html       trusted-by stats counter bar
├── _landing_features.html      6 feature cards grid
├── _landing_analytics.html     radar chart, stat bars, win-rate donut
├── _landing_rankings.html      rankings table + top player cards
├── _landing_ai_analysis.html   head-to-head comparison, improvement plan
├── _landing_mockups.html       phone showcase
├── _landing_cta.html           final call to action
├── _landing_footer.html        (or keep in base.html)
```

**Rationale**: DDR frontend rule says extract by *visual section responsibility and independent reason to change*. Every section above has a different reason to change — copy, data source, animation, layout, navigation links. Mixing them into one file would create a coupling nightmare.

#### CSS Split
- **Keep in `scouter.css`**: shared utility classes (`.power-glow`, `.card-hover`, scrollbar, emoji fix) — these are reused across pages
- **New `landing.css`**: landing-specific animations (scroll-reveal, counter-tick, scouter-scan-line), section-specific backgrounds, keyframes
- **Inline styles in Tailwind config**: color palette extensions (already in base.html `tailwind.config`)

#### JS Split
- **Keep `main.js`**: logout, checkAuth, password strength — shared across pages
- **New `landing.js`**: orchestration module
  - `landing_scroll.js` — scroll-reveal / intersection observer animations
  - `landing_counters.js` — numeral counter animation for metrics
  - `landing_scouter.js` — power level scan animation / timer
  - `landing_charts.js` — Chart.js instances for the analytics preview (radar, donut)
- Naming convention follows existing `player_detail/` pattern (one file per concern)

#### What Stays in `base.html` vs Moves to Landing
| Component | Keep in base.html? | Rationale |
|-----------|-------------------|-----------|
| Background effects (gradient, grid) | ✅ Yes | Global — all pages share the dark theme |
| Google Fonts (Inter + Rajdhani) | ✅ Yes | Global |
| Tailwind config + CDN | ✅ Yes | Global |
| Chart.js CDN | ✅ Yes | Global — used by player_detail too |
| Navbar | ⚠️ Partial extract | Auth login button changes for landing (CTA vs "Acceder"), but navbar structure is global. Generate a flag `show_landing_nav` to conditionally render landing-specific CTA vs standard auth buttons. |
| Footer | ✅ Yes (keep) | But add landing-specific social icons via template variable |
| Chatbot widget | ✅ Yes | Global — included from base.html |
| `scouter.css` | ✅ Yes | Already linked in base.html |
| `main.js` | ✅ Yes | Already linked in base.html |
| New `landing.js` | In index.html block | Load via `{% block scripts %}` in index.html only |
| New `landing.css` | In index.html block | Load via `{% block styles %}` (need to add this block to base.html) or inline in index.html |

#### Recommended Addition to `base.html`
```jinja
{% block head_styles %}{% endblock %}
```

To allow landing-specific CSS to be injected before the closing `</head>`. Currently `base.html` has no `{% block head_styles %}`.

### Risks

1. **Page size / load time**: 10 sections with Chart.js renders, animations, and images (phone mockups) will significantly increase page weight. Consider lazy loading below-fold sections and using a lightweight scroll-reveal library (IntersectionObserver-based, not jQuery).

2. **Tailwind CDN in production**: Currently using `cdn.tailwindcss.com` (dev version, includes compiler). This is 3-4MB uncompressed. For a rich landing page with many Tailwind classes, consider generating a static CSS build instead. This is a pre-existing risk, not introduced by this change, but the landing page will amplify it.

3. **Mock data coupling**: If the analytics preview and rankings sections embed mock data in templates, switching to real API data later becomes a template rewrite. Design the partials to accept data via template context from the start, even if views.py initially passes mock data.

4. **Animation performance**: Scroll-triggered animations on 10 sections can cause jank on low-end devices. Use `will-change: transform`, `content-visibility: auto`, and debounced IntersectionObserver.

5. **Chatbot overlap**: The chatbot widget (fixed bottom-right, z-index 9999) may visually overlap with the phone mockups section. Ensure z-index layering accounts for this.

### Ready for Proposal
**Yes** — the codebase is small and well-structured. The exploration reveals clear boundaries, existing conventions to follow, and no blockers. Proposal should address:
- Whether to generate a Tailwind static build vs keep CDN
- Mock data strategy (inline in partials vs Jinja context variables)
- Whether to add `{% block head_styles %}` to base.html
- Scroll-reveal library choice (custom IntersectionObserver vs lightweight lib)
