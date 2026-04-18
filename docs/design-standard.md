# AI.JBHerrera — Design Standard

The visual + structural standard for every page in `/public/`. Apple-inspired: light by default, dark on toggle, generous whitespace, soft shadows, restrained color, large radii, system typography.

All shared styles live in `public/styles/base.css` and are loaded as `<link rel="stylesheet" href="/styles/base.css">`. Per-page styles only contain page-specific layout.

---

## 1. Theming

- Light is the default. Users toggle to dark via the navbar control.
- Theme preference is persisted in `localStorage` under key `theme` (`"light" | "dark"`).
- First-paint script (inline, before `<body>`) sets `data-theme` on `<html>` from `localStorage`, falling back to `prefers-color-scheme`. This avoids a light-flash for dark-mode users.
- Never hardcode color values in page CSS. Use the `--color-*` tokens.

```html
<!-- In <head>, before any visible content -->
<script>
  (function(){
    var s = localStorage.getItem('theme');
    var d = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', s || d);
  })();
</script>
```

## 2. Color tokens

| Token | Light | Dark | Use |
|---|---|---|---|
| `--color-primary` | `#667eea` | `#667eea` | Brand, links, active states |
| `--color-primary-hover` | `#5a67d8` | `#5a67d8` | Hover on primary |
| `--color-secondary` | `#764ba2` | `#764ba2` | Gradient end |
| `--gradient-brand` | `linear-gradient(135deg, #667eea, #764ba2)` | (same) | Hero accents only |
| `--color-bg` | `#ffffff` | `#000000` | Page background |
| `--color-bg-secondary` | `#f5f5f7` | `#1c1c1e` | Subtle fills |
| `--color-surface` | `#ffffff` | `#1c1c1e` | Cards, panels |
| `--color-text` | `#1d1d1f` | `#f5f5f7` | Primary text |
| `--color-text-secondary` | `#6e6e73` | `#a1a1a6` | Body / muted text |
| `--color-text-tertiary` | `#86868b` | `#6e6e73` | Captions, footer |
| `--color-border` | `#d2d2d7` | `#38383a` | Inputs, dividers |
| `--color-border-subtle` | `#e8e8ed` | `#2c2c2e` | Card borders |

Status colors: `--color-success #34c759`, `--color-warning #ff9500`, `--color-danger #ff3b30`, `--color-info #007aff` — Apple system colors. Use sparingly, only for state.

The brand gradient `--gradient-brand` is reserved for the home hero and CTA accents — not body backgrounds.

## 3. Typography

- Family: `-apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', sans-serif`. SF Pro is automatic on Apple devices; Inter is the fallback elsewhere.
- Body baseline: 17px / 1.47.
- Headlines use weight 600 (never 700+) and negative letter-spacing for the Apple feel.
- Use the type-scale classes; do not redefine sizes per page.

| Class | Size | Weight | Line-height | Tracking |
|---|---|---|---|---|
| `.text-display` | clamp(40, 6vw, 56) | 600 | 1.07 | -0.022em |
| `.text-h1` | clamp(32, 4vw, 40) | 600 | 1.10 | -0.020em |
| `.text-h2` | clamp(24, 3vw, 32) | 600 | 1.20 | -0.015em |
| `.text-h3` | 20 | 600 | 1.30 | -0.010em |
| `.text-body` | 17 | 400 | 1.47 | 0 |
| `.text-body-sm` | 15 | 400 | 1.45 | 0 |
| `.text-caption` | 13 | 400 | 1.40 | 0 |
| `.text-eyebrow` | 12 | 600 | 1.30 | 0.06em / UPPERCASE |

## 4. Spacing & layout

- 4px scale: `--space-1`..`--space-12` (4, 8, 12, 16, 24, 32, 48, 64, 96).
- Container widths: `--container-max 1200px` (page), `--content-max 800px` (prose / hero / forms).
- Use `.container` and `.container-narrow` instead of redefining max-widths.
- Vertical rhythm: sections use `--space-10` top/bottom (`.section`).

## 5. Radius, shadow, motion

- Radii: `--radius-sm 6 / -md 12 / -lg 18 / -xl 28 / -full 9999`. Cards default to `-lg`. Buttons are `-full` (Apple pill).
- Shadows are layered and very soft. `--shadow-md` for hover-lift on cards. Never use a heavy black shadow.
- Motion: `--ease-out cubic-bezier(0.32, 0.72, 0, 1)` (Apple's house easing). Durations: 150 / 250 / 400ms. Honour `prefers-reduced-motion` (handled in base.css).

## 6. Components

### Navbar
Sticky, 56px tall, translucent with `backdrop-filter: blur(20px) saturate(180%)`. One brand on the left, links + theme toggle on the right. Structure:

```html
<nav class="navbar">
  <a href="/" class="navbar-brand">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"></circle>
      <path d="M12 16v-4"></path>
      <path d="M12 8h.01"></path>
    </svg>
    AI.JBHerrera
  </a>
  <div class="navbar-links">
    <a href="/digest"   class="navbar-link">AI Digest</a>
    <a href="/ai-stack" class="navbar-link">AI Stack</a>
    <a href="/skills"   class="navbar-link">Skills</a>
    <a href="https://jbherrera.com" class="navbar-link" target="_blank" rel="noopener">Main Site</a>
    <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <svg class="icon-sun"  viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
    </button>
  </div>
</nav>
```

Add `class="active"` to the link matching the current page. Toggle script (paste once, near `</body>`):

```html
<script>
  document.getElementById('themeToggle').addEventListener('click', function(){
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
  });
</script>
```

### Buttons
- `.btn` is the base. Variants: `.btn-primary`, `.btn-secondary`, `.btn-ghost`. Sizes: default, `.btn-lg`, `.btn-sm`.
- Always pill-shaped (`--radius-full`). Primary = brand fill, secondary = subtle gray fill, ghost = transparent.
- Never put a button without one of the variant classes.

### Cards
- `.card` for static surfaces. Add `.card-interactive` if the whole card is a link.
- White surface on light, `#1c1c1e` on dark. Border `--color-border-subtle`. Radius `--radius-lg`. Padding `--space-6`.
- Hover on interactive cards: lift 2px, soft shadow, border darkens. No background change.

### Form controls
- `.input`, `.select`, `.textarea` for fields. `.label` for field labels.
- Focus ring is a 3px halo of `--color-primary-soft`. No browser default outlines.

### Badges / tags
- `.badge` (pill) for status: `.badge-success / -warning / -info / -neutral`. Use a `.badge-dot` inside for the dot pattern.
- `.tag` (square chip) for taxonomies / metadata, never status.

### Hero
- `.hero` wrapper, optional `.hero-tag` eyebrow pill, then `<h1 class="text-display">`, then a 19px subhead in `--color-text-secondary`.
- Center-aligned, capped at 860px.

### Footer
- `.site-footer`, single line of caption text, links in `--color-text-secondary`.

## 7. Page conventions

Every page must:

1. Load `/styles/base.css` before any inline styles.
2. Include the first-paint theme script in `<head>`.
3. Use the standard `.navbar` + `.theme-toggle` block, with the matching link marked `.active`.
4. Use `.site-footer` for the footer.
5. Use the type-scale classes for all headings — do not set `font-size` inline.
6. Use tokens (`var(--color-*)`) for all colors. No hex literals in page CSS.
7. Page-specific styles live in a single `<style>` block scoped under a unique page class on `<body>` (e.g. `body class="page-stack"`) to avoid leaking into shared components.

## 8. Accessibility

- Color contrast: text on background must clear WCAG AA in both themes. The token pairs above are pre-checked.
- Every interactive control needs a visible focus state — `.btn` and form fields handle this; custom controls must follow.
- Theme toggle has `aria-label="Toggle theme"`.
- `prefers-reduced-motion: reduce` is honoured globally in base.css.
- Tap targets ≥ 36px on mobile.

## 9. What changes when

- Adding a new page → start by copying the `<head>` + nav + footer scaffold from `ai-stack.html` (the reference implementation). Only add page-specific CSS.
- Adding a new color → add it to `:root` and `[data-theme="dark"]` in `base.css`. Never inline a one-off hex.
- New shared component (e.g. modal, tooltip) → add to `base.css` with both light and dark token usage. Document it in this file.
- One-off page accent (e.g. the per-layer colors on `/ai-stack`) → keep scoped to that page's `<style>`, but read tokens for surfaces and text so the dark toggle still works.

---

## Reference implementation

`/public/ai-stack.html` is the canonical example of the standard applied. When in doubt, mirror that file's structure.
