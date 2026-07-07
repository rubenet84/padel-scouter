# Proposal: Landing Page Redesign

## Intent

Replace the minimal 56-line landing page with a full 10-section visual showcase that communicates Padel Scouter's value proposition. The current page lacks section separation and mixes all concerns in a single template — making it impossible to iterate on individual sections independently. DDR frontend architecture is applied from day one to prevent a monolithic HTML.

## Scope

### In Scope
- 10 visual sections: Hero (scouter panel), Trusted-by Metrics bar, Features (6 cards), Analytics Dashboard preview (radar, stat bars, charts, win-rate donut), Rankings (table + top-player cards), AI Analysis (head-to-head, improvement plan), Phone Mockups showcase, CTA
- 8 new partials under `app/templates/partials/` with `_landing_` prefix, one per visual section (navbar and footer stay in base.html)
- New `app/static/css/landing.css` for section-specific styles, animations, keyframes
- New `app/static/js/landing/` with sub-modules: scroll (IntersectionObserver), counters, scouter timer, charts
- `index.html` as orchestrator — includes partials, no inline sections
- Add `{% block head_styles %}` to `base.html` before `</head>`
- Update `views.py` index route to pass mock data context
- All partials accept Jinja context variables, never hardcoded mock data
- Navbar/footer remain in `base.html` (global); conditional `show_landing_nav` flag for landing-specific CTA
- Dark theme consistent with existing `#0A0A0F` palette

### Out of Scope
- New domain functionalities, API changes, stats, or ranking modifications
- Removing Tailwind CDN (pre-existing risk, deferred)
- Chatbot widget, auth, or dashboard changes
- Changes to `main.js` or `scouter.css` (unless trivial shared class additions)

## Capabilities

### New Capabilities
- `landing-page`: Frontend-only visual landing page with DDR architecture. Purely presentational — no API capabilities.

### Modified Capabilities
None. This is a visual-only change with zero spec-level behavior changes.

## Approach

1. **Partial extraction**: One `_landing_<section>.html` per visual section under `app/templates/partials/`. Accept data exclusively via Jinja context variables.
2. **Orchestrator template**: `index.html` extends `base.html`, then `{% include %}` each partial sequentially in page order.
3. **base.html injection**: Add `{% block head_styles %}` before `</head>` for landing-specific CSS. Landing sections `{% include %}` in `{% block content %}`. `landing.js` loads via existing `{% block scripts %}`.
4. **CSS split**: New `landing.css` for section styles, scroll-reveal keyframes, scan-line animation. Shared utilities stay in `scouter.css`.
5. **JS split**: `landing.js` entry orchestrates sub-modules: IntersectionObserver scroll-reveal, numeral counter animation, scouter power-level scan, Chart.js radar/donut instances.
6. **View update**: `views.py` `index()` passes a `landing_data` context dict with mock values. Partial templates reference `{{ landing_data.section.field }}`.
7. **No backend entanglement**: All mock data is replaceable by real API data without touching template partials.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/templates/index.html` | Modified | 56-line hero+cards → partial orchestrator |
| `app/templates/base.html` | Modified | Add `{% block head_styles %}` |
| `app/templates/partials/_landing_*.html` | New | 8 partials, one per section |
| `app/static/css/landing.css` | New | Section-specific styles and keyframes |
| `app/static/js/landing/*.js` | New | 4 sub-modules + landing.js entry |
| `app/api/v1/views.py` | Modified | Add `landing_data` context mock dict |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Page weight with 10 sections + Chart.js | Medium | Lazy-load below-fold sections; debounced IntersectionObserver |
| Mock data → real API coupling | Medium | Partial design uses `{{ landing_data.* }}` — swap source not template |
| Chatbot z-index overlap (9999) | Low | Set mockups section z-index below 9999 |
| Animation jank on low-end devices | Low | `will-change: transform`, `content-visibility: auto`, debounced observer |

## Rollback Plan

Revert `index.html`, `base.html`, and `views.py` to previous commit. Delete `landing.css` and `landing/` JS directory. All changes are additive — zero data or API impact.

## Dependencies

- None. Tailwind, Chart.js, and Google Fonts already loaded via `base.html`.
- Phone mockup images to be created externally (not part of this change).

## Success Criteria

- [ ] All 10 sections render correctly across mobile, tablet, and desktop
- [ ] Each partial accepts data via Jinja context — zero hardcoded strings in templates
- [ ] `landing.css` loads without conflicting with `scouter.css`
- [ ] Chart.js instances (radar, donut) render without console errors
- [ ] Scroll animations trigger via IntersectionObserver with no visible jank
- [ ] Adding/removing a section requires touching exactly one partial + its CSS/JS
