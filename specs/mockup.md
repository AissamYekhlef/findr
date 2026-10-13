# Findr Frontend Mockups

This document shows wireframes and layout specs for the Findr MVP UI. All measurements use the 4 px base unit. Colors reference the design token system in `tech-stack.md`.

---

## 1. Top Application Bar

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Findr       [Sources]  [Modules ▾]       🔍 [Search...]                   │
│                                           🌓 [Theme] ▾  [Export]           │
└────────────────────────────────────────────────────────────────────────────┘
```

**Layout & Dimensions:**
- Height: 56 px
- Logo (Findr): 16 px left padding, 20 px bold (Schibsted Grotesk)
- Navigation tabs: [Sources] [Modules ▾], left-aligned after logo
- Search bar: centered, 200 px wide, gray placeholder text
- Theme menu: dropdown button, 40 px, icon + label
- Export button: right-aligned, 80 px
- Total horizontal padding: 16 px left and right

**States:**
- Active tab (Sources): accent text color + 2 px underline
- Inactive tab (Modules): secondary text, underline on hover
- Theme dropdown: shows when clicked, positioned below button

### Theme Menu Dropdown

```
┌──────────────────────────┐
│ MODE                     │
│  ○ System                │
│  ● Light     ○ Dark      │
├──────────────────────────┤
│ PRESETS >               │
├──────────────────────────┤
│ Appearance ↗            │
└──────────────────────────┘
```

Width: 200 px, corners: 8 px, shadow: floating

---

## 2. Left Sidebar (Sources Panel)

### Structure

```
┌──────────────────────────┐
│ SOURCES                  │
├──────────────────────────┤
│ 📁 Table (csv, xlsx)     │ ◄─ Group header
│   ▸ orders.xlsx         │ ◄─ Selected/active
│   ▸ clients.csv         │
│   ▸ stock.tsv           │
├──────────────────────────┤
│ 📁 SQL Databases         │
│   🗄️  PostgreSQL (prod)  │
│   🗄️  MySQL (analytics)  │
│   🗄️  Snowflake (DW)     │
├──────────────────────────┤
│ 📁 NoSQL Databases       │
│   🍃 MongoDB (user data) │
│   🔴 Redis (cache)       │
├──────────────────────────┤
│ 📁 Text                  │
│   📄 logs.txt            │
│   📄 notes.md            │
├──────────────────────────┤
│ [+ Add source]           │
└──────────────────────────┘
```

**Dimensions:**
- Width: 240 px (fixed)
- Section header: 11 px uppercase, secondary text, 16 px padding, 8 px top margin
- Group icon: 16 px, muted color
- Item: 38 px height, 16 px left padding, 12 px icon + text
- Expand triangle: 12 px, rotates on expand
- Source icon: 16 px (file, database, or text type)
- Source name: 13 px, primary text

**States:**
- Active source: `--accent-soft` background tint, accent text color
- Hover: `--raise` background color
- Group expanded/collapsed: triangle rotates
- Missing file: warning icon, muted text, opacity 60%
- Unsaved changes: dot indicator (4 px circle, `--edit` color) next to name

**Scrolling:** sidebar scrolls independently if content exceeds viewport height

---

## 3. Main Content Panel

### 3.1 Breadcrumb & Context Header

```
orders.xlsx  /  Sheet: [Orders ▾]
```

- Left: source file name, 14 px bold
- Separator: `/` (muted)
- Right: "Sheet:" label + dropdown
- Height: 32 px, padding: 8 px horizontal

### 3.2 Toolbar

```
[+ Add row] [Delete] | [Undo] [Redo]        3 pending changes
```

- Left group: Add row (primary, 40 px), Delete (danger, 40 px)
- Divider: 1 px line, `--line` color
- Center group: Undo (40 px, disabled if no history), Redo (40 px, disabled if no history)
- Right: Pending changes counter (inline badge, `--edit-bg` background)
- Height: 44 px, padding: 8 px between groups, 12 px horizontal margins

Below toolbar:

```
[🔍 Search...] [Filters ▾] [Columns ▾]
```

- Search input: 200 px, placeholder text
- Filters button: shows filter panel on click
- Columns button: shows column visibility menu on click

### 3.3 Data Grid Editor

```
┌───┬──────┬──────────┬────────┬─────────────┐
│ ✓ │ id   │ customer │ amount │ date        │
├───┼──────┼──────────┼────────┼─────────────┤
│   │ 1    │ Karim    │ 120.00 │ 2026-09-01  │
│ ✏️ │ 2    │ Amel ✏️  │ 80.50  │ 2026-09-02  │ ◄─ In-edit state
│   │ 3    │ Amel     │ 80.50  │ 2026-09-02  │
│   │ 4    │ Torah    │ 140.00 │ 2026-09-01  │
│   │ 5    │ Karim    │ 120.00 │ 2026-09-02  │
│   │ 6    │ Kanth    │ 75.00  │ 2026-09-01  │
│   │ 7    │ Karim    │ 40.50  │ 2026-09-02  │
│   │ 8    │ Amel     │ 100.00 │ 2026-09-02  │
│   │ 9    │ Senth    │ 30.00  │ 2026-09-01  │
│   │ 10   │ Customer │ 120.00 │ 2026-09-01  │
│   │ 11   │ Amel     │ 80.50  │ 2026-09-02  │
└───┴──────┴──────────┴────────┴─────────────┘
```

**Column Structure:**
- Checkbox column: 40 px wide (for row selection)
- Data columns: auto-width or fixed per column type
  - `id`: numeric, right-aligned, tabular figures
  - `customer`: text, left-aligned
  - `amount`: numeric, right-aligned, tabular figures
  - `date`: date, center-aligned

**Header:**
- Background: `--surface`
- Text: 12 px, secondary text, uppercase label
- Sticky: stays at top during scroll
- Sortable: click to toggle asc / desc / none (column header shows sort direction icon ▲ ▼)

**Rows:**
- Height: 38 px (default density)
- Padding: 8 px horizontal, 10 px vertical
- Hover: `--raise` background color
- Virtualized: only visible rows rendered

**Cell States:**
- **Normal:** `--ink` text on `--surface` background
- **Edited:** edited cell shows ✏️ icon, light `--edit-bg` tint, darker `--edit-fg` text
- **Added row:** light `--add-bg` tint, darker `--add-fg` text, row ID shows "auto"
- **Deleted row:** strikethrough text, light `--del-bg` tint, darker `--del-fg` text, dimmed
- **In-edit (focused cell):** 2 px `--accent` outline, input mode active
- **Selected:** checkbox checked, row has light `--accent-soft` background tint

**Row Actions:**
- Checkbox: multi-select for batch delete
- Double-click or Enter: enter edit mode for cell
- Escape: cancel edit, revert value
- Tab / Shift+Tab: move to next / previous cell (in edit mode)
- Delete key: delete selected rows

### 3.4 Pagination & Footer

```
«  <  Page 1 of 42  >  »      100 rows ▾      [Discard]  [Save changes]
```

- **Left:** Pagination controls (previous, next, page indicator)
- **Center:** Row count dropdown (50 / 100 / 250 / 500 rows per page)
- **Right:** Action buttons
  - Discard: secondary button, 80 px
  - Save changes: primary accent button, 100 px

- Height: 48 px, padding: 12 px horizontal, aligned bottom of content
- Background: `--surface`
- Border-top: 1 px `--line` color
- Sticky: stays at bottom during scroll

---

## 4. Full Application Layout (Combined View)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Findr       [Sources]  [Modules ▾]       🔍 [Search...]                   │
│                                           🌓 [Theme] ▾  [Export]           │
├──────────────┬──────────────────────────────────────────────────────────────┤
│ SOURCES      │ orders.xlsx  /  Sheet: [Orders ▾]                           │
│              │                                                              │
│ 📁 Table     │ [+ Add row] [Delete] | [Undo] [Redo]    3 pending changes   │
│   ▸ orders   │ [🔍 Search...] [Filters ▾] [Columns ▾]                     │
│   ▸ clients  │                                                              │
│   ▸ stock    │ ┌───┬──────┬──────────┬────────┬──────────────┐            │
│              │ │ ✓ │ id   │ customer │ amount │ date         │ ▲         │
│ 📁 SQL       │ ├───┼──────┼──────────┼────────┼──────────────┤            │
│   🗄️ Postgres│ │   │ 1    │ Karim    │ 120.00 │ 2026-09-01   │            │
│   🗄️ MySQL   │ │ ✏️ │ 2    │ Amel ✏️  │ 80.50  │ 2026-09-02   │            │
│   🗄️ Snowflk │ │   │ 3    │ Amel     │ 80.50  │ 2026-09-02   │            │
│              │ │   │ 4    │ Torah    │ 140.00 │ 2026-09-01   │            │
│ 📁 NoSQL     │ │   │ 5    │ Karim    │ 120.00 │ 2026-09-02   │            │
│   🍃 MongoDB │ │   │ 6    │ Kanth    │ 75.00  │ 2026-09-01   │            │
│   🔴 Redis   │ │   │ 7    │ Karim    │ 40.50  │ 2026-09-02   │            │
│              │ │   │ 8    │ Amel     │ 100.00 │ 2026-09-02   │ ▼         │
│ 📁 Text      │ │   │ 9    │ Senth    │ 30.00  │ 2026-09-01   │            │
│   📄 logs.txt│ │   │ 10   │ Customer │ 120.00 │ 2026-09-01   │            │
│   📄 notes   │ │   │ 11   │ Amel     │ 80.50  │ 2026-09-02   │            │
│              │ └───┴──────┴──────────┴────────┴──────────────┘            │
│              │                                                              │
│ [+ Add]      │ «  <  Page 1 of 42  >  »    100 rows ▾                     │
│              │                    [Discard]  [Save changes]                │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 5. Empty State (No Sources)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Findr       [Sources]  [Modules ▾]       🔍 [Search...]                   │
│                                           🌓 [Theme] ▾  [Export]           │
├──────────────┬──────────────────────────────────────────────────────────────┤
│ SOURCES      │                                                              │
│              │                                                              │
│ [+ Add]      │                     📁                                       │
│              │              No sources yet                                  │
│              │                                                              │
│              │          [+ Add your first file]                            │
│              │                                                              │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

**Copy & Style:**
- Icon: 48 px, muted color
- Heading: 22 px, secondary text
- Button: 16 px, accent background, white text

---

## 6. Add Source Dialog

```
┌──────────────────────────────────────────────┐
│ Add a source                            [×]  │
├──────────────────────────────────────────────┤
│                                              │
│  [Upload file]    [Select from server]       │
│                                              │
│  File: [📎 orders.csv____________]           │
│                                              │
│  Format: [CSV ▾]                             │
│  Delimiter: [,]   Encoding: [UTF-8 ▾]       │
│  Header row: [✓]                            │
│                                              │
│  Preview (first 10 rows):                   │
│  ┌─────┬──────────┬────────────┬──────────┐ │
│  │ id  │ customer │ amount     │ date     │ │
│  ├─────┼──────────┼────────────┼──────────┤ │
│  │ 1   │ Karim    │ 120.00     │ 2026-09  │ │
│  │ 2   │ Amel     │ 80.50      │ 2026-09  │ │
│  └─────┴──────────┴────────────┴──────────┘ │
│                                              │
│                  [Cancel]  [Add source]      │
└──────────────────────────────────────────────┘
```

**Dimensions:**
- Modal width: 480 px (desktop), full width - 32 px (mobile)
- Modal max-height: 80 vh
- Corners: 10 px
- Button group: right-aligned, 16 px gap
- Preview table: max 10 rows shown

---

## 7. Pending Changes Drawer

```
Pending Changes (3)
═══════════════════════════════════════════════════════

ADDED (1)
───────────────────────────────────────────────────────
Row: new_1
  customer: [empty] → "Amel"
  amount:   [empty] → 250.00
  date:     [empty] → 2026-09-15
                                         [Revert]

EDITED (1)
───────────────────────────────────────────────────────
Row: 2
  customer: "Amel" → "Amel Ahmed"
                                         [Revert]

DELETED (1)
───────────────────────────────────────────────────────
Row: 3
  customer: "Youssef"
  amount:   250.00
  date:     2026-09-15
                                         [Revert]
```

**Dimensions:**
- Width: 320 px (fixed, right side of screen, or drawer below table on mobile)
- Corners: 8 px
- Section padding: 16 px
- Group label: 11 px uppercase, secondary text, 12 px top margin
- Item padding: 12 px
- Revert button: 12 px, right-aligned

---

## 8. Appearance Module (Full Theme Editor)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Findr       [Sources]  [Modules ▾]       🔍 [Search...]                   │
│                                           🌓 [Theme] ▾  [Export]           │
├──────────────┬──────────────────────────────────────────────────────────────┤
│ MODULES      │ APPEARANCE                                                   │
│              │                                                              │
│              │ MODE                                                         │
│              │ ○ System  ● Light  ○ Dark                                   │
│              │                                                              │
│              │ DENSITY                                                      │
│              │ ● Compact (32px) | Default (38px) | Comfortable (46px)     │
│              │                                                              │
│              │ PRESET COLORS                                                │
│              │ ● Teal  Indigo  Graphite  Copper  Plum  [Reset]            │
│              │                                                              │
│              │ CUSTOM COLORS (Light mode)                                  │
│              │                                                              │
│              │ ACCENT                                                       │
│              │ ┌─────────────┐              Hex: [#0A6B60]                │
│              │ │      ■       │ ← Picker                                  │
│              │ └─────────────┘                                            │
│              │                                                              │
│              │ GROUND, SURFACE, INK, ADD, EDIT, DEL, INFO (same layout)   │
│              │                                                              │
│              │ CONTRAST CHECK                                               │
│              │ Text on surface:     4.8:1  ✓ AA                            │
│              │ Text on background:  4.2:1  ✓ AA                            │
│              │ Button text:         7.1:1  ✓ AAA                           │
│              │ Accent on surface:   3.2:1  ⚠ Low                           │
│              │                                                              │
│              │ EXPORT / IMPORT THEME                                       │
│              │ [📋 Copy as JSON]  [📄 Paste]  [Reset all]                 │
│              │                                                              │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

**Color Picker:**
- Width: 240 px
- Saturation/lightness grid: 200 × 200 px
- Hue slider: full width below grid
- Hex input: 80 px, monospace font

**Contrast badges:**
- AA (pass): green bg, white text
- AAA (excellent): green bg, white text
- Low: orange bg, dark text

---

## 9. Modules Menu

```
┌──────────────────────────────────────────────────┐
│ MODULES                                          │
├──────────────────────────────────────────────────┤
│ Dashboard                                 [v2]   │
│ See sources, row counts, changes, activity.      │
├──────────────────────────────────────────────────┤
│ Users                                    [v2]   │
│ Invite, manage, assign roles & permissions.      │
├──────────────────────────────────────────────────┤
│ Roles                                    [v2]   │
│ Create custom roles, define permissions.         │
├──────────────────────────────────────────────────┤
│ History                                  [v2]   │
│ View and restore previous versions.              │
├──────────────────────────────────────────────────┤
│ Appearance                              [Live]  │
│ Customize colors, mode, and density.             │
└──────────────────────────────────────────────────┘
```

**Menu item:**
- Height: 60 px
- Padding: 12 px horizontal, 8 px vertical
- Title: 14 px bold
- Description: 12 px secondary text
- Tag: 11 px uppercase, 4 px padding, accent or muted background tint

---

## 10. Module Preview (Dashboard with Example Data)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Findr       [Sources]  [Modules ▾]       🔍 [Search...]                   │
│                                           🌓 [Theme] ▾  [Export]           │
├──────────────┬──────────────────────────────────────────────────────────────┤
│ MODULES      │ ℹ Example data. This module becomes live in v2.              │
│              │                                                              │
│              │ STATISTICS                                                   │
│              │ ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│              │ │ 8        │ │ 24.5k    │ │ 342      │                     │
│              │ │ Sources  │ │ Rows     │ │ Changes  │                     │
│              │ └──────────┘ └──────────┘ └──────────┘                     │
│              │                                                              │
│              │ CHANGES PER DAY (Last 14 days)                              │
│              │ │ ▁▁▂▃▃▄▅▆▆▇▇█▆▅ │                                         │
│              │ 0 ├─────────────┤ 42                                        │
│              │                                                              │
│              │ RECENT ACTIVITY                                              │
│              │ Oct 13  orders.xlsx    +3 rows                              │
│              │ Oct 12  clients.csv    1 edit                               │
│              │ Oct 11  stock.xlsx     -2 rows                              │
│              │                                                              │
│              │           [Invite user] → "Invite arrives in v2"           │
│              │                                                              │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

**Notice bar:**
- Background: info color tint (`--info-bg`)
- Text: info color darker (`--info-fg`)
- Icon: ℹ (16 px)
- Height: 40 px, centered vertically
- Padding: 12 px

**Stat tiles:**
- Width: 160 px each (3 per row, 16 px gap)
- Height: 80 px
- Corners: 8 px
- Number: 24 px bold, accent color
- Label: 12 px secondary text

**Chart:**
- Height: 120 px
- Bars: 4 px rounded tops, 8 px gap
- Hover tooltip: small value display

---

## 11. Interaction States

### 11.1 Editing a Cell

```
Normal:
│ Karim    │

Double-click or Enter:
│ [Karim_____] │ ← Focused, 2 px accent outline

Tab or Enter (commit):
│ Karim    │ ✏️ ← Marked edited, light `--edit-bg` tint

Escape (cancel):
│ Karim    │ ← Reverted
```

### 11.2 Adding a Row

```
[+ Add row]  →  Blank row inserted at top or bottom

│ auto │ [____] │ [____] │ [____] │ ← Editable, light `--add-bg` tint
```

### 11.3 Deleting Rows

```
Select:
│✓│ Karim    │

[Delete]:
│✓│ Karim ✕  │ ← Strikethrough, light `--del-bg`, marked pending
```

### 11.4 Focus Outline

All interactive elements:
- Outline: 2 px solid `--accent`
- Offset: 2 px
- Radius: match element radius + 2 px

---

## 12. Responsive Breakpoints

| Screen | Width | Layout | Notes |
|---|---|---|---|
| **Desktop** | ≥1024 px | Header + Sidebar (240 px) + Content | Sidebar always visible |
| **Tablet** | 760–1024 px | Header + Sidebar chips (horizontal strip) + Content | Sidebar collapses to chips |
| **Mobile** | <760 px | Header + Sidebar chips + Full-width content | Tables scroll horizontally |

**Mobile adjustments:**
- Sidebar: 100% width as chip strip, ~60 px height
- Table: scrollable container, columns stay visible
- Buttons: ≥44 px touch target
- Modals: full width - 32 px padding

---

## 13. Color & Token Reference

### 13.1 Light Mode (Teal Preset)

```css
--accent: #0A6B60
--ground: #EDF0EF
--surface: #FAFBFA
--ink: #16201E
--add: #1F8A4C
--edit: #C98A00
--del: #CC3B3B
--info: #2F6FCB

/* Derived */
--raise: ink 6% into surface
--line: ink 15% into surface
--ink2: ink 68% into surface
--ink3: ink 54% into surface
--accent-soft: accent 16% into surface
--add-bg/fg, --edit-bg/fg, --del-bg/fg, --info-bg/fg (formula-based)
```

### 13.2 Dark Mode (Teal Preset)

```css
--accent: #3FC1AE
--ground: #0E1413
--surface: #151D1B
--ink: #E3EBE8
--add: #4CC37A
--edit: #E3B341
--del: #EF6B6F
--info: #6FA3EA
```

---

## 14. Typography Scale

| Use | Size | Weight | Line-height |
|---|---|---|---|
| Page title | 22 px | 600 | 1.2 |
| Section title | 17 px | 600 | 1.2 |
| Body, controls, table data | 14 px | 400 | 1.5 |
| Table data (monospace) | 13 px | 400 | 1.4 |
| Meta, hints | 12 px | 400 | 1.4 |
| Labels (uppercase) | 11 px | 500 | 1.2 |

**Fonts:**
- UI: Schibsted Grotesk (400, 500, 600, 700); fallback: system sans-serif
- Data: JetBrains Mono (400); fallback: system monospace

---

## 15. Spacing Scale (4 px base)

```
4 px   (gap within groups)
8 px   (gap between groups, button padding)
12 px  (vertical spacing within sections)
16 px  (padding within containers, section margins)
20 px  (vertical space between major sections)
24 px  (outer padding, gutters)
```

---

## 16. Component States Summary

| Component | Default | Hover | Active | Disabled | Focus |
|---|---|---|---|---|---|
| Button (primary) | accent bg, white text | darker accent | pressed down | 50% opacity | 2 px outline |
| Button (secondary) | line border, ink text | raise bg | accent text | 50% opacity | 2 px outline |
| Input | line border, ink text | raise bg, ink border | accent border | 50% opacity | 2 px outline |
| Link | accent text | accent underline | accent-darker | 50% opacity | 2 px outline |
| Tab | ink text | raise bg | accent text + underline | — | 2 px outline |
| Table row | surface | raise bg | accent-soft bg | — | managed by table |
| Checkbox | unchecked border | raise bg | checked (accent bg) | 50% opacity | 2 px outline |

---

## 17. Animations

- **Theme switch:** instant (no fade)
- **Modal entrance:** instant (MVP)
- **Toast:** fade-in 200 ms, fade-out 1 s
- **Hover/Active:** instant
- **Respects:** `prefers-reduced-motion: reduce` (no motion)

