# Landing Page Specification

## Purpose

Defines the visual and interactive behavior of the Padel Scouter landing page — a 10-section showcase communicating the product's value proposition with zero backend API dependencies. Purely presentational domain.

## Requirements

### Requirement: Layout & Responsiveness

The landing page MUST render correctly across mobile (≥320px), tablet (≥768px), and desktop (≥1280px) viewports without horizontal overflow, using a single-column linear flow that adapts grid layouts per breakpoint.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 1 | Mobile single-column | viewport is 375px wide | page loads | all sections stack vertically, no content clipped, no horizontal scroll |
| 2 | Tablet 2-column grids | viewport is 768px wide | page renders | feature cards and analytics use 2-column layout |
| 3 | Desktop multi-column | viewport is 1440px wide | page renders | rankings table uses full width, feature cards use 3-column grid |

### Requirement: Section Rendering

The system SHALL render each section (Hero, Metrics, Features, Analytics, Rankings, AI Analysis, Phone Mockups, CTA, navbar, footer) without JavaScript errors. Each section SHALL be encapsulated in its own partial template.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 4 | All partials render | landing page loads | Jinja evaluates `{% include %}` directives | no TemplateNotFound or render errors logged |
| 5 | Section order preserved | page renders | partials are sequentially included | DOM order matches: navbar → hero → metrics → features → analytics → rankings → ai-analysis → mockups → cta → footer |

### Requirement: Mock Data Injection

All sections SHALL receive display data exclusively through Jinja context variables (`landing_data`). No partial SHALL contain hardcoded display values.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 6 | Context populated | view returns `landing_data` dict | page renders | each section reads `landing_data.section.field`, no undefined variable errors |
| 7 | Empty data fallback | `landing_data` has empty values | page renders | sections render with zero states (0 counters, empty tables, no JS errors) |

### Requirement: Styling Isolation

The system SHALL load `landing.css` for section-specific styles and keyframes. `landing.css` MUST NOT conflict with `scouter.css`.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 8 | Landing CSS loaded | page loads via `{% block head_styles %}` | landing.css is injected | all landing sections apply intended styles, animations, and keyframes |
| 9 | No class collision | both CSS files loaded | scouter.css class used on non-landing page | page renders identically — landing.css selectors are scoped (e.g. `[class*="landing-"]`) |

### Requirement: Chart Rendering

Chart.js instances (radar for player profile, donut for win-rate) SHALL render without console errors.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 10 | Radar chart renders | valid chart data in `landing_data` | `landing_charts.js` initializes | radar `<canvas>` renders correct labels and dataset, no Chart.js errors |
| 11 | Donut chart renders | win-rate data present | donut initializes | donut renders with correct percentage and legend |
| 12 | Chart.js CDN fails | Chart.js fails to load | page renders | section displays degraded placeholder text — no uncaught TypeError |

### Requirement: Scroll Animation

Sections SHALL animate into view via IntersectionObserver. The observer SHALL be debounced to prevent jank on rapid scroll.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 13 | Section enters viewport | section is below fold | user scrolls to 15% visibility | section gains `.is-visible`, CSS opacity/translate animation plays once |
| 14 | Rapid scroll | user scrolls past 5 sections in <500ms | observer fires | animations are debounced — ≤1 animation frame per 16ms |

### Requirement: Scouter Timer

The Hero panel SHALL display a live-updating power level value with scan-line animation, incrementing from 0 to a target value.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 15 | Power level animates | target value is 8400 | page loads | counter increments 0→8400 over ~2s, each integer step visible |
| 16 | Timer completes | counter reaches target | animation ends | displayed value stops at target, scan-line glow continues looping |

### Requirement: Responsive Navigation

The navbar SHALL adapt CTA for landing context using a `show_landing_nav` flag.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 17 | Landing nav active | `show_landing_nav` is true | page renders | navbar shows "Empezar" CTA instead of standard auth buttons |
| 18 | Authenticated user on landing | user has valid token | page renders | navbar shows user avatar/username and dashboard link per existing auth flow |

### Requirement: Phone Mockups

Mockup images SHALL load with descriptive `alt` attributes and a fallback mechanism for missing assets.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 19 | Image loads | mockup URL is valid | `<img>` src resolves | image displays with correct dimensions and descriptive alt text |
| 20 | Image 404s | mockup image returns 404 | `<img>` onerror fires | fallback placeholder (colored div + icon) renders in place |

### Requirement: Separation of Concerns

Each section SHALL span exactly one partial + its CSS and JS. No section SHALL depend on logic from another section's partial.

| # | Scenario | GIVEN | WHEN | THEN |
|---|----------|-------|------|------|
| 21 | Remove one section | developer removes one `{% include %}` from index.html | remaining 9 sections load | no broken references, no JS errors from removed modules, layout reflows naturally |
| 22 | Independent JS modules | `landing_charts.js` references chart data | `landing_scouter.js` runs | no variable cross-contamination — each module operates on its own DOM scope |
