# Trail-Search Frontend — Design Spec

> Status: **recommendation only, not yet implemented.** Produced from two analyses
> (a frontend-design lead pass + the `ui-ux-pro-max` design-intelligence skill),
> synthesized. Accent + font pairing is an **open decision** (see §4).
> Current code (`src/App.jsx`) is unchanged.

---

## 1. Subject

A search instrument over real WTA hiking trip reports. Users arrive with a
condition query already formed ("snow on the pass", "bugs at the Enchantments")
and want the most relevant trip reports **ranked**. The BM25 rank order is the
entire value proposition; the UI's job is to put that ranked list in front of
eyes fast, with enough context (trail + region) to pick the first click.

API result shape (per item): `{ id, trail_name, region, url, score }`.

---

## 2. Universal fixes — do these regardless of aesthetic direction

Both analyses flagged these independently. They are correctness/UX, not taste.

| # | Gap in current `App.jsx` | Fix | Severity |
|---|---|---|---|
| 1 | `score` is fetched + stored but **never rendered** | Render it (normalized bar + rank number). This is the whole point of a ranked search and is invisible today. | Highest |
| 2 | Placeholder is the only label | Add a visible `<label htmlFor>` on the search input | High |
| 3 | Empty state = bare "no results found" | Add a suggestion: "Try a broader condition — 'snow', 'water', 'bugs'." | Medium |
| 4 | Loading = plain "searching…" text | Skeleton/ghost rows with a shimmer animation | High |
| 5 | No `aria-live` on results; no `aria-label` on result links | `aria-live="polite"` on results container; `aria-label={`${trail_name}, ${region} — opens WTA trip report`}` on each link | Medium (a11y) |
| 6 | All styling is inline | Move to CSS classes (`index.css` / `App.css`) | Cleanup |
| 7 | `key={r.id}` | **Already correct** — keep. (Index keys would be a High bug; you're clean.) | ✓ |

---

## 3. Score rendering (the core of fix #1)

Raw BM25 scores are not human-interpretable. Treatment:

```js
const maxScore = results[0]?.score || 1;      // top result = 1.0
const rel = r.score / maxScore;                // 0..1 relative match
```

- Draw a filled bar of `width: ${rel * 100}%` in the accent color, at the bottom
  of each result row/card. Animate on render.
- Show an explicit rank ordinal (`#01`, `#02`) in a distinct color so order is
  read, not counted.
- Optional readable label: `${Math.round(rel * 100)}% match` (relative within the
  result set — accurate, not a false confidence score).
- **Score-cliff "Top Match" badge:** when `results[1] && results[1].score / results[0].score < 0.4`,
  the top result is meaningfully ahead — mark result #1 with a badge or separator.
  This surfaces real information the raw list hides.

---

## 4. Aesthetic direction — recommended, with one open decision

Both lenses independently converged on **dark, data-forward**. Recommended spine:
the frontend-design "Survey Instrument" direction (cartographic/field-GPS
reference), softened per the skill's guidance.

**Open decision (pick at build time):**

### Option A — Teal + IBM Plex Mono (design lead's pick — most distinctive)
Mono reads like records retrieved from a database; form matches the retrieval content.

| Role | Hex | Name |
|---|---|---|
| Page background | `#0B1219` | Midnight Survey |
| Card / input surface | `#152030` | Deep Chart |
| Primary accent (interactive, bars) | `#2A9D8F` | GPS Aqua |
| Primary text | `#E9F0F5` | Arctic White |
| Muted text | `#4A6FA5` | Surveyor Blue |
| Rank ordinal only | `#E76F51` | Marker Orange |

- Display: **Syne** 700–800 (map-legend character)
- Body/UI/data: **IBM Plex Mono** 400/500
- Import: `@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');`

### Option B — Green/amber + Newsreader (skill's pick — more literally "outdoor")
Editorial warmth; treats trip reports as journalism.

| Role | Hex |
|---|---|
| Background (dark) | `#0B1219`–`#050506` |
| Primary / accent | `#15803D` forest green |
| Secondary accent | `#D97706` trail amber |
| Foreground | `#EDEDEF` |
| Muted | `#8A8F98` |
| Border | `rgba(255,255,255,0.08)` |

- Heading: **Newsreader**, Body: **Roboto**
- Import: `@import url('https://fonts.googleapis.com/css2?family=Newsreader:wght@400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap');`

> Note: the skill warns against pure `#000000`/`#020203` backgrounds (OLED smear) —
> both options use `#0B1219` as the base.

### Light fallback (both options)
Add `@media (prefers-color-scheme: light)` → parchment palette for bright-sun
mobile use. Layout, type, and score-viz transfer unchanged.

| Role | Hex |
|---|---|
| Background | `#F4F2EE` warm gray (not cream) |
| Card | `#FFFFFF` |
| Text/headings | `#1E3A5F` deep sky navy |
| Rank | `#B87333` copper |
| Muted | `#6B7280` |

---

## 5. Layout

- **Kill the centered 700px column.** Left-aligned, full-width.
- Header (page title in the display font) + search bar spanning ~70% width.
- Results = flush-left vertical list with a fixed rank gutter (64px, `#01/#02`
  in the display font + rank color) then trail data to the right.
- `region` rendered small/muted with a small geo-marker glyph preceding it.
- The whole row is the `<a href={r.url}>`; never show the raw URL.

---

## 6. Motion — CSS only (no library needed)

The app has **no** GSAP/motion lib installed; all of the below are zero-dependency
and compositor-friendly. Both analyses gave the same stagger technique.

**Staggered results entrance** — set `style={{ '--i': index }}` per row:
```css
@media (prefers-reduced-motion: no-preference) {
  .result-row {
    animation: rowIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
    animation-delay: calc(var(--i) * 55ms);
  }
  @keyframes rowIn {
    from { opacity: 0; transform: translateY(14px) scale(0.97); }
    to   { opacity: 1; transform: none; }
  }
}
```
> Skill note: don't stagger more than ~8 visible children heavily; later items feel laggy.

**Score bar fill** — `transition: width 0.5s cubic-bezier(0.4,0,0.2,1)` from 0 to `rel%`.

**Input focus glow** — `box-shadow: 0 0 0 2px <accent>, 0 0 12px <accent-glow>` on focus
(reads like a GPS unit acquiring signal).

**Result hover** — `transform: translateY(-3px)` + soft shadow, `transition ~150ms`.

**Loading skeleton** — ghost rows with a moving `linear-gradient` shimmer
(`background-size: 200% 100%; animation: shimmer 1.4s infinite linear`) instead of
the "searching…" text.

---

## 7. Accessibility

- **Contrast:** Option A `#E9F0F5` on `#0B1219` ≈ AAA. GPS Aqua `#2A9D8F` on dark ≈ 5:1 —
  AA for large text only; do not use for body text < 18px. Skill's Glacier Blue
  `#5B8DB8` on white fails AA for normal text — use only for the graphical score bar.
- **Focus:** explicit `outline: 2px solid <accent>; outline-offset: 3px` on input,
  button, and result links. Never bare `outline: none`.
- **Results region:** `aria-live="polite" aria-atomic="false"`; consider `aria-busy`
  during fetch.
- **Links:** `aria-label` including trail + region + "opens WTA trip report".
- Keyboard: current Enter-to-search is correct; keep tab order input → button → links.

---

## 8. Responsive

- List layout (Option A) works at all widths. Below 480px: rank gutter 64px → 32px,
  rank numeral 32px → 20px.
- If a card/grid variant is used: `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`
  (natural collapse, no hard breakpoint).
- Search input + button: 44px min tap height on mobile; stack button full-width below
  input under 480px.

---

## 9. Optional future (not needed now)

- Live search: debounce with `useDeferredValue`; autocomplete dropdown (skill: Medium).
- Large result sets (100+): profile first (React DevTools); if render cost is real,
  `@tanstack/react-virtual` (no GSAP conflict).
- `loading="lazy"` on any below-fold images if result cards gain imagery.

---

## Source
Synthesized from a frontend-design analysis pass and the `ui-ux-pro-max` skill
(styles / colors / typography / ux / gsap / react-stack domains). Hex values,
font names, and import strings are as returned by those sources.
