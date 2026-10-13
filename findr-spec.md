# Findr — Product Specification

**Status:** Draft v0.1
**Stack:** Nuxt 4 (Vue 3, TypeScript) frontend · FastAPI (Python) backend
**New in v0.1:** app shell with Sources and Modules navigation, visual style, and a theme system with editable colors.

---

## 1. Overview

Findr is a web app for working with tabular data stored in files. The user picks a data source (a CSV or Excel file), sees its data in a table, edits it directly from the UI, and saves the changes back to the original source.

### 1.1 Goals

- Open a CSV or Excel file as a data source in a few clicks.
- Show the data of the selected source in a fast, readable table.
- Let the user add, edit, and delete rows from the UI and persist the changes to the file.
- Make it safe: no silent data loss, clear feedback, undo.
- Give the app one consistent look that each user can change: light, dark or system mode, ready-made presets, and their own colors.
- Show where the product is going (Dashboard, Users, Roles, History) as static previews, without building them yet.

### 1.2 Non-goals (MVP)

- Multi-user real-time collaboration.
- Databases (SQL / NoSQL), REST API sources. These are planned for Part Two.
- Complex formulas, pivot tables, or cell styling from Excel.
- Working Dashboard, Users, Roles and History modules. In the MVP they are static previews with example data and become live in Part Two. Appearance is the one module that works in the MVP.

### 1.3 Users

Anyone who keeps data in spreadsheets or flat files and wants a simple way to browse, search, and fix it without opening Excel.

---

# PART ONE — MVP

## 2. Core concepts

| Concept | Definition |
|---|---|
| **Source** | A registered file (CSV or Excel) that Findr can read and write. |
| **Sheet** | A single table inside a source. A CSV has one; an Excel file can have many. |
| **Row** | One record in a sheet. Identified internally by a stable row ID. |
| **Column** | A named field with a detected type (text, number, date, boolean). |
| **Change** | A pending edit (insert, update, delete) not yet saved to the file. |

## 3. User stories

1. As a user, I can add a CSV or Excel file as a source so I can work with it.
2. As a user, I can see a list of my sources and select one.
3. As a user, when a source has several sheets, I can choose which sheet to view.
4. As a user, I can see the selected sheet's data in a table with pagination.
5. As a user, I can sort by a column and search/filter the rows.
6. As a user, I can edit a cell inline.
7. As a user, I can add a new row and delete existing rows.
8. As a user, I can review my pending changes, then save or discard them.
9. As a user, I can undo/redo changes before saving.
10. As a user, I can remove a source from Findr without deleting the file.
11. As a user, I can move between **Sources** and **Modules** from the header without losing unsaved changes.
12. As a user, I can open the Dashboard, Users, Roles and History modules to see what they will offer (example data only until v2).
13. As a user, I can choose light, dark or system mode and a preset, and change any of the main colors, and the app remembers my choice.
14. As a user, I can make the table more compact or more spacious.

## 4. Functional requirements

### 4.1 Source management

- **FR-1** Add a source by uploading a file or by selecting a file path available to the backend.
- **FR-2** Supported formats: `.csv`, `.tsv`, `.xlsx`. (`.xls` is read-only if supported.)
- **FR-3** For CSV/TSV the user can confirm or change: delimiter, encoding (default UTF-8), header row (yes/no), quote character.
- **FR-4** Each source stores: id, display name, type, location, created date, last opened date.
- **FR-5** Sources can be renamed and removed. Removing a source never deletes the underlying file.
- **FR-6** If a source file is missing or unreadable, the source shows an error state with a "Locate file" or "Remove" action.

### 4.2 Viewing data

- **FR-7** Selecting a source loads its first sheet (or the sheet last used).
- **FR-8** Data is displayed in a table with a sticky header row and column types shown in the header.
- **FR-9** Data loads in pages (default 100 rows, options 50/100/250/500). Large files must not be fully sent to the browser.
- **FR-10** Sorting by any column, ascending/descending.
- **FR-11** Global search across all columns, plus per-column filters (contains, equals, greater/less than, is empty).
- **FR-12** Show the total row count, filtered row count, and column count.
- **FR-13** Column visibility can be toggled; column widths can be resized. These settings are remembered per source.

### 4.3 Editing data

- **FR-14** Double-click (or Enter) on a cell to edit it inline. Escape cancels, Enter/Tab commits to a pending change.
- **FR-15** Values are validated against the column type. Invalid input is rejected with an inline message.
- **FR-16** "Add row" inserts a blank row at the top or bottom of the sheet.
- **FR-17** Rows can be selected (single and multi-select) and deleted.
- **FR-18** Edited, added, and deleted rows are visually marked until saved (e.g., highlight color, strikethrough for deletions).
- **FR-19** A **Pending changes** panel lists every unsaved change with a count, and lets the user revert any single change.
- **FR-20** **Save** writes all pending changes to the source file. **Discard** drops all pending changes.
- **FR-21** Undo/redo for pending changes (Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z).
- **FR-22** Leaving the page or switching source with unsaved changes shows a confirmation.

### 4.4 Saving and file safety

- **FR-23** Before the first write in a session, Findr creates a timestamped backup copy of the file (e.g., `data.csv.bak-20261004-1845`). Backup retention is configurable (default: keep last 5).
- **FR-24** Saves are atomic: write to a temporary file, then replace the original. A failed save must leave the original untouched.
- **FR-25** If the file changed on disk since it was loaded, Save is blocked and the user chooses: reload, or overwrite.
- **FR-26** For Excel, saving preserves other sheets and, where possible, column widths and number formats. Unsupported features (macros, charts, pivot tables) are not modified; if they cannot be preserved, Findr warns before saving.
- **FR-27** CSV saves preserve the original delimiter, encoding, and line endings.

### 4.5 Export

- **FR-28** Export the current view (with active filters and sort) to CSV or XLSX.

### 4.6 App shell and navigation

- **FR-29** A persistent header shows the Findr mark, two primary items, **Sources** and **Modules**, the global search, a **Theme** menu and **Export**. Search and Export apply to Sources only and are hidden inside modules.
- **FR-30** **Sources** opens the data workbench described in 4.1 to 4.5. While a module is open, a dot on the Sources item shows that a source has unsaved changes.
- **FR-31** **Modules** opens a menu with Dashboard, Users, Roles, History and Appearance. Each entry has a one-line description and a tag: `v2` for static previews, `Live` for Appearance.
- **FR-32** The sidebar follows the header. Under Sources it lists the sources and the Add source button. Under Modules it lists the modules.
- **FR-33** In the MVP, Dashboard, Users, Roles and History are static previews built from fixture files. They make no API calls and change no data. Each shows the notice "Example data. This module becomes live in v2." Buttons that would change something (Invite user, New role, Restore, Edit) answer with "<Action> arrives in v2".
- **FR-34** Appearance is fully working in the MVP (see 4.7).
- **FR-35** Switching between Sources and Modules never discards pending changes.
- **FR-36** Routes: `/sources/:id/:sheet?` and `/modules/:name`. Module pages are lazy-loaded so they add nothing to the Sources bundle.

| Module | MVP | Example content shown | Goes live |
|---|---|---|---|
| Dashboard | Static | Tiles (sources, rows, changes saved in 14 days, files changed on disk), changes-per-day bar chart, recent activity, source health | Part Two, V3 |
| Users | Static | Eight example users with role, status, source access and last activity; search | Part Two, V5 |
| Roles | Static | Admin, Editor, Viewer and Auditor with a permission matrix | Part Two, V5 |
| History | Static | Log of saved changes: when, who, source, action, summary, Restore | Part Two, V4 |
| Appearance | Live | Mode, presets, colors, density, theme file | MVP |

### 4.7 Theme and appearance

- **FR-37** **Mode:** System (default, follows the device), Light or Dark. The choice applies immediately and is remembered.
- **FR-38** **Presets:** Teal (default), Indigo, Graphite, Copper and Plum. Each preset defines a complete light palette and a complete dark palette.
- **FR-39** **Custom colors:** for the active mode the user can change eight base colors: Accent, Background, Surface, Text, Added, Edited, Deleted and Notice. Each has a color picker and a hex field. Changes apply live while the picker moves.
- **FR-40** All other colors are derived from the eight base colors (borders, muted text, hover, selected rows, row-state tints, accent tint). One change recolors the whole app, including added, edited and deleted rows.
- **FR-41** The text color on accent buttons is chosen automatically, white or near-black, whichever reads better.
- **FR-42** **Readability checks** show the contrast ratio for text on surface, text on background, accent on surface and button text on accent. Anything under 4.5 : 1 (WCAG AA) is flagged "Low". The app warns and never blocks.
- **FR-43** **Density:** Compact (32 px rows), Default (38 px) or Comfortable (46 px).
- **FR-44** **Reset:** reset the colors of the current mode to the preset, or reset all appearance settings.
- **FR-45** **Theme file:** the full theme can be copied as JSON and pasted back to apply it, which also lets a team share one look. Invalid values are ignored with a message that names them.
- **FR-46** **Persistence:** the theme is stored per user in the browser (MVP). The saved theme is applied before first paint so there is no flash of the wrong theme. If storage is unavailable the app uses the defaults.
- **FR-47** A **Theme** menu in the header offers mode and presets for quick changes, with a link to Appearance for the full editor.
- **FR-48** The app respects `prefers-color-scheme` and `prefers-reduced-motion`, and keeps focus outlines visible in every theme.

## 5. Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | First page of a 100k-row file displays in under 2 s; scrolling and paging stay under 300 ms per request after load. |
| Scale | Handle files up to 500 MB / 1M rows via server-side paging and indexed access. |
| Reliability | No partial writes; automatic backup before first save. |
| Accessibility | Keyboard-navigable table; visible focus; WCAG 2.1 AA contrast. |
| Responsiveness | Usable on desktop and tablet widths; mobile is view-only. |
| Privacy | Files stay on the user's machine/server; nothing is sent to third parties. |
| i18n | UI text in a translation file from day one (English first; French and Arabic with RTL planned). |
| Theming | A color or mode change applies in under 100 ms with no page reload. The saved theme is applied before first paint. Every color in the UI comes from a token, never a literal. |
| Contrast | Default presets meet 4.5 : 1 for text in both modes. User colors are checked and flagged, not blocked. |

## 6. UI specification

### 6.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Findr [Sources] [Modules ▾]  [Search…]  [Theme] [Export]     │
├──────────────┬───────────────────────────────────────────────┤
│ SOURCES      │  orders.xlsx  ▸ Sheet: [Orders ▾]             │
│  ▸ orders    │  [+ Add row] [Delete] [Undo] [Redo]           │
│  ▸ clients   │  [Filters ▾] [Columns ▾]     3 pending changes│
│  ▸ stock     │ ┌─────┬───────────┬──────────┬──────────────┐ │
│              │ │ id  │ customer  │ amount   │ date         │ │
│ [+ Add]      │ ├─────┼───────────┼──────────┼──────────────┤ │
│              │ │ 1   │ Karim     │ 120.00   │ 2026-09-01   │ │
│              │ │ 2   │ Amel  ✎   │ 80.50    │ 2026-09-02   │ │
│              │ └─────┴───────────┴──────────┴──────────────┘ │
│              │  « ‹ Page 1 of 42 › »   100 rows ▾            │
│              │                       [Discard]  [Save changes]│
└──────────────┴───────────────────────────────────────────────┘
```

### 6.2 Screens and components

- **App header**: Findr mark, **Sources** and **Modules** items, search, Theme menu, Export. The current area is highlighted.
- **Modules menu**: Dashboard, Users, Roles, History, Appearance, each with a short description and a `v2` or `Live` tag.
- **Theme menu**: mode (System, Light, Dark), presets, and a link to Appearance.
- **Sidebar**: source list, add-source button, status icon per source (ok / missing / unsaved changes). While a module is open it lists the modules instead.
- **Module pages**: Dashboard, Users, Roles and History with example data and an "Example data" notice; Appearance with live controls.
- **Add source dialog**: file picker, format options (delimiter, encoding, header row), preview of the first 10 rows, confirm.
- **Data table**: virtualized rows, sticky header, inline editing, row selection checkboxes.
- **Toolbar**: add row, delete, undo/redo, filters, column visibility, pending changes counter.
- **Pending changes drawer**: grouped by Added / Edited / Deleted, with per-change revert.
- **Save bar**: appears when there are unsaved changes; Save and Discard buttons.
- **Conflict dialog**: shown when the file changed on disk (Reload / Overwrite / Cancel).

### 6.3 States

- Empty (no sources yet): illustration plus "Add your first file".
- Loading: skeleton rows.
- Error: inline banner with the reason and a suggested action.
- Saving: Save button shows progress and the table is locked.
- Saved: brief confirmation toast; pending markers cleared.
- Module preview: page shows a notice that the data is an example; controls that would change data answer with a "arrives in v2" message.

### 6.4 Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Enter / double-click | Edit cell |
| Esc | Cancel edit |
| Tab / Shift+Tab | Next / previous cell |
| Ctrl/Cmd+S | Save changes |
| Ctrl/Cmd+Z / Shift+Z | Undo / redo |
| Delete | Delete selected rows |
| Ctrl/Cmd+F | Focus search |

### 6.5 Visual style

The look is calm and dense: a data tool that stays out of the way. Color is kept for meaning (one accent, plus the states of a row), so a change on screen is easy to spot.

| Area | Decision |
|---|---|
| UI typeface | Schibsted Grotesk (400, 500, 600, 700), with the system UI font as fallback |
| Data typeface | JetBrains Mono for identifiers, numbers, dates and file paths, with the system monospace as fallback. Numeric columns use tabular figures and align right |
| Type scale | 11 px uppercase labels (letter-spacing .09em) · 12 px meta · 13 px table data · 14 px body and controls · 16 to 17 px section titles and brand · 20 to 22 px page titles |
| Spacing | 4 px base unit: 4, 8, 12, 16, 20, 24. Page gutter 16 px at every width |
| Corners | 6 px controls · 8 px menus and cards · 10 px panels and dialogs · 3 to 4 px tags and bar tops |
| Borders and depth | 1 px hairlines using the derived line color. Surfaces are separated by borders, not shadows. Shadows only on things that float: menus, the drawer, dialogs, toasts |
| Icons | 16 px outline icons, 1.9 px stroke, round caps, drawn in the current text color |
| Motion | A short fade for toasts only. Nothing else animates. Reduced-motion users get none |
| Focus | 2 px accent outline with a 2 px offset on every interactive element |

**Row states.** Added, edited and deleted rows use a tinted background and a darker text color of the same hue. Color is never the only signal: deleted rows are struck through, an edited cell shows its previous value on hover, and generated ids on new rows read "auto".

**Charts.** One series uses the accent. Bars have 4 px rounded tops, a small gap between them and recessive gridlines. Only the peak and the latest value are labeled directly; every bar has a hover value. A chart also exposes its numbers as a table for screen readers.

**Layout.** Header on top, sidebar on the left (240 px), content on the right. Below 760 px the sidebar becomes a horizontal strip of chips above the content, tables scroll sideways inside their own container, and the save bar sticks to the bottom of the screen.

### 6.6 Theme system

#### 6.6.1 Base tokens

Eight colors per mode are editable. The values below are the default Teal preset.

| Token | Used for | Light | Dark |
|---|---|---|---|
| `--accent` | Primary buttons, current item, links, chart bars | `#0A6B60` | `#3FC1AE` |
| `--ground` | App background | `#EDF0EF` | `#0E1413` |
| `--surface` | Header, sidebar, table, panels | `#FAFBFA` | `#151D1B` |
| `--ink` | Primary text | `#16201E` | `#E3EBE8` |
| `--add` | Added rows | `#1F8A4C` | `#4CC37A` |
| `--edit` | Edited cells, unsaved indicators | `#C98A00` | `#E3B341` |
| `--del` | Deleted rows, destructive actions | `#CC3B3B` | `#EF6B6F` |
| `--info` | Notices and informational tags | `#2F6FCB` | `#6FA3EA` |

`--accent-ink` (the text on accent buttons) is computed from `--accent`. `--scrim` and `--shadow` are fixed per mode.

#### 6.6.2 Derived tokens

Derived tokens are written once, with `color-mix`, and recalculate whenever a base token changes.

| Token | Formula |
|---|---|
| `--raise` | `--ink` 6% into `--surface` (hover, table header) |
| `--line` | `--ink` 15% into `--surface` (borders) |
| `--ink2` | `--ink` 68% into `--surface` (secondary text) |
| `--ink3` | `--ink` 54% into `--surface` (hints, type badges) |
| `--accent-soft` | `--accent` 16% into `--surface` (current item, selected row) |
| `--add-bg`, `--edit-bg`, `--del-bg`, `--info-bg` | the state color 16% into `--surface` |
| `--add-fg`, `--edit-fg`, `--del-fg`, `--info-fg` | the state color 58% into `--ink` (readable text on its tint) |
| `--row-h`, `--head-h` | set by density: 32 / 34, 38 / 40, 46 / 46 px |

#### 6.6.3 Presets

| Preset | Character | Accent (light / dark) |
|---|---|---|
| Teal (default) | Cool green-blue, neutral greys | `#0A6B60` / `#3FC1AE` |
| Indigo | Blue-violet, slightly cool greys | `#4338CA` / `#8E9BFF` |
| Graphite | Near-monochrome, steel blue accent | `#2F4B66` / `#9DB9D6` |
| Copper | Warm paper greys, orange-brown accent | `#B04E16` / `#E8935A` |
| Plum | Soft purple greys, magenta accent | `#8A2B77` / `#D98BCB` |

Every preset defines all eight base colors for both modes. The state colors (Added, Edited, Deleted, Notice) are shared by all presets unless a preset overrides them.

#### 6.6.4 How a theme is applied

The page can be in three states: the root element has `data-theme="light"`, `data-theme="dark"`, or no attribute (System). Components only use tokens; no component CSS contains a literal color.

```css
:root {                       /* light values, plus every derived token */
  --ground:#EDF0EF; --surface:#FAFBFA; --ink:#16201E; --accent:#0A6B60;
  --line: color-mix(in srgb, var(--ink) 15%, var(--surface));
  --row-h: 38px;              /* ...and the rest of the tokens */
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* dark base tokens */ color-scheme: dark }
}
:root[data-theme="dark"]  { /* dark base tokens */ color-scheme: dark }
:root[data-density="compact"]     { --row-h: 32px; --head-h: 34px }
:root[data-density="comfortable"] { --row-h: 46px; --head-h: 46px }
```

The user's colors are written by the app into a generated `<style>` element placed after the base stylesheet, using the same three selectors. Because the derived tokens are computed from the base tokens, nothing else needs to be rewritten.

#### 6.6.5 Theme file

```json
{
  "findrTheme": 1,
  "mode": "system",
  "preset": "teal",
  "density": "default",
  "colors": {
    "light": { "accent": "#0A6B60", "ground": "#EDF0EF", "surface": "#FAFBFA", "ink": "#16201E",
               "add": "#1F8A4C", "edit": "#C98A00", "del": "#CC3B3B", "info": "#2F6FCB" },
    "dark":  { "accent": "#3FC1AE", "ground": "#0E1413", "surface": "#151D1B", "ink": "#E3EBE8",
               "add": "#4CC37A", "edit": "#E3B341", "del": "#EF6B6F", "info": "#6FA3EA" }
  }
}
```

Rules: colors are six-digit hex; unknown keys are ignored; a missing key keeps the preset value; an invalid value is skipped and reported. To add a preset, add one entry with its two palettes to the presets file. No component changes are needed.


## 7. Architecture

### 7.1 Overview

```
 Nuxt 4 (Vue 3 + TS)  ──HTTP/JSON──▶  FastAPI  ──▶  Source adapters  ──▶  Files
   Pinia store                          Services       (CSV / Excel)       (disk)
   Table + pending changes              Change engine
```

### 7.2 Frontend (Nuxt 4)

- **State (Pinia):** `sources`, `activeSource`, `activeSheet`, `pageState` (page, size, sort, filters), `pendingChanges`, `undoStack`, `redoStack`. A separate `theme` store holds `mode`, `preset`, `density` and `custom { light, dark }`, persisted to local storage.
- **Components:** `AppHeader`, `ModulesMenu`, `ThemeMenu`, `SourceList`, `AddSourceDialog`, `DataTable`, `Toolbar`, `PendingChangesDrawer`, `SaveBar`, `ConflictDialog`, `ModuleNotice`, `AppearancePage`.
- **Module pages:** `pages/modules/dashboard.vue`, `users.vue`, `roles.vue`, `history.vue` read from fixture files in `/fixtures` (plain JSON, clearly named `*.example.json`). They call no API. In Part Two the fixtures are replaced by the real endpoints behind the same components.
- **Theming:** a `useTheme()` composable applies the theme: it sets or removes `data-theme` and `data-density` on the root element, writes the generated style element, and exposes `setMode`, `setPreset`, `setColor`, `resetColors`, `exportTheme` and `importTheme`. It runs in an early plugin so the saved theme is applied before first paint.
- **Data access:** a typed API client (`useApi`) wrapping the endpoints below.
- Pending changes are held client-side and sent to the backend only on Save.

### 7.3 Backend (FastAPI)

- **Adapter interface** (one per format) so new connectors can be added in Part Two without changing the API:

```python
class SourceAdapter(Protocol):
    def list_sheets(self) -> list[SheetInfo]: ...
    def get_schema(self, sheet: str) -> list[Column]: ...
    def read_page(self, sheet: str, page: int, size: int,
                  sort: Sort | None, filters: list[Filter]) -> Page: ...
    def apply_changes(self, sheet: str, changes: ChangeSet) -> SaveResult: ...
    def fingerprint(self) -> str: ...   # detect external modification
```

- **CSV adapter:** reads with a chunked/indexed reader; for large files builds a row-offset index so paging is fast.
- **Excel adapter:** reads and writes with a workbook library that preserves sheets and formats.
- **Change engine:** validates a `ChangeSet`, applies it to a temp copy, then atomically replaces the original.
- **Backup service:** creates and prunes backups.

### 7.4 API (MVP)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/sources` | List sources |
| POST | `/api/sources` | Add a source (upload or path) with format options |
| PATCH | `/api/sources/{id}` | Rename, update format options |
| DELETE | `/api/sources/{id}` | Remove source (file untouched) |
| GET | `/api/sources/{id}/sheets` | List sheets |
| GET | `/api/sources/{id}/sheets/{sheet}/schema` | Column names and types |
| GET | `/api/sources/{id}/sheets/{sheet}/rows` | Paged rows (`page`, `size`, `sort`, `filter`, `q`) |
| POST | `/api/sources/{id}/sheets/{sheet}/changes` | Save a change set (`fingerprint`, `inserts`, `updates`, `deletes`) |
| GET | `/api/sources/{id}/sheets/{sheet}/export` | Export current view |

### 7.5 Data model

```
Source   { id, name, type, location, options{}, created_at, last_opened_at }
Column   { name, type, nullable, position }
Row      { row_id, values{ column: value } }
ChangeSet {
  fingerprint,
  inserts: [{ temp_id, values }],
  updates: [{ row_id, values }],        // only changed columns
  deletes: [row_id]
}
SaveResult { ok, new_fingerprint, applied_counts, errors[] }
```

Source metadata (the list of sources and per-source view settings) is stored in a small local SQLite database. The data itself always stays in the original file.

### 7.6 Row identity

Files have no primary key, so Findr assigns each row a stable ID per load, based on its position and fingerprint. If the file changes on disk, row IDs are invalidated and the user must reload. An optional "key column" setting lets the user pick a column to use as the identifier instead.

## 8. Edge cases

- Empty file, header-only file, or file with duplicate/blank column names (auto-rename, e.g., `column_2`).
- Mixed types in a column (treated as text, with a warning).
- Very long cell values (truncated in view, full value in edit).
- Dates and numbers: locale-aware parsing; the original format is preserved on save when unchanged.
- Excel merged cells, formulas: formulas are shown as their computed values and are read-only; merged cells are read-only.
- File locked by another program (Excel open): save fails with a clear message and nothing is changed.
- Read-only file or folder: source opens in read-only mode.
- Two browser tabs editing the same source: the fingerprint check prevents silent overwrite.

## 9. Acceptance criteria (MVP)

- [ ] Adding a CSV and an XLSX file shows each in the sidebar with correct sheets.
- [ ] Selecting a source displays its data with pagination, sorting, and search.
- [ ] Editing a cell, adding a row, and deleting a row mark them as pending.
- [ ] Save writes exactly those changes to the file and nothing else; reopening the file in Excel/a text editor shows them.
- [ ] A backup exists after the first save.
- [ ] A forced failure during save leaves the original file byte-identical.
- [ ] Editing the file externally, then saving in Findr, triggers the conflict dialog.
- [ ] Discard and Undo restore the original values.
- [ ] A 100k-row CSV opens and pages within the performance targets.
- [ ] The header shows Sources and Modules; Modules lists Dashboard, Users, Roles, History and Appearance.
- [ ] Switching from a source with unsaved changes to a module and back keeps the changes.
- [ ] Dashboard, Users, Roles and History show example data and the "Example data" notice, and no network request is made when they open.
- [ ] Choosing Dark, Light or System changes the whole app at once, including table row states.
- [ ] Choosing a preset changes all eight base colors; choosing a color in the picker updates the app while the picker moves.
- [ ] A theme exported as JSON and pasted back produces the same look.
- [ ] A reload keeps the theme with no flash of the default look.
- [ ] A low-contrast color pair is flagged "Low" but still applied.

## 10. MVP milestones

1. **M0 — Shell and design system:** tokens, light/dark/system modes, presets, color editor, density, header with Sources and Modules, static module previews.
2. **M1 — Read-only viewer:** add source, list sheets, paged table, sort, search.
3. **M2 — Editing:** inline edit, add/delete rows, pending changes, undo/redo.
4. **M3 — Persistence:** change engine, atomic save, backups, conflict detection.
5. **M4 — Polish:** export, column settings, keyboard shortcuts, error states, accessibility pass.

---

# PART TWO — v2.0

## 11. Goals

Extend Findr beyond files to databases and services, and make views reusable.

## 12. New features

### 12.1 More connectors

- **SQL databases:** PostgreSQL first, then MySQL/SQLite.
- **MS Access** (`.accdb`/`.mdb`).
- **REST API** sources (read, and write where the API allows).
- **NoSQL** (e.g., MongoDB) with documents shown as flattened tables.
- Each connector implements the same `SourceAdapter` interface; credentials are stored encrypted.

### 12.2 Saved views

- Save the current sort, filters, visible columns, and page size as a named **view** on a source.
- Views can be renamed, duplicated, and deleted; the last used view opens by default.

### 12.3 Charts and widgets

- Turn any view into a chart (bar, line, pie, table summary) by choosing the X axis, Y axis, and aggregation.
- Charts are saved with the view and can be edited at any time from the UI (change type, columns, or the underlying filters) without rebuilding from scratch.
- A dashboard page can hold several saved charts.

### 12.4 Advanced editing

- Bulk edit: set a column value for all selected rows.
- Find and replace across a column or sheet.
- Import rows from another file into the current sheet, with column mapping.
- Column operations: add, rename, reorder, change type.

### 12.5 History

- A change log per source (who/when/what) with the ability to restore a previous version.

### 12.6 Multi-user

- Accounts, roles (viewer, editor, admin), and per-source permissions.
- Row-level locking while a user is editing, to avoid conflicts.

### 12.7 Query editor (database sources)

- A visual filter builder, plus a raw query editor for SQL sources with run, save, and edit-in-place.
- Results open in the same table and can be edited when the query maps to a single table.

### 12.8 Modules go live

The four static previews from the MVP become real pages on the same layout, with the same components. Each gets its API and its permission checks.

| Module | What becomes real | Endpoints (new) |
|---|---|---|
| Dashboard | Tiles and charts computed from real sources and the change log; the charts are saved views | `GET /api/dashboard`, `GET /api/dashboards/{id}` |
| Users | Invite, edit, suspend and remove users; assign roles and source access | `GET/POST /api/users`, `PATCH/DELETE /api/users/{id}` |
| Roles | Create and edit roles; the permission matrix becomes editable | `GET/POST /api/roles`, `PATCH/DELETE /api/roles/{id}` |
| History | The real change log with filters, and Restore | `GET /api/history`, `POST /api/history/{id}/restore` |

Menu tags change from `v2` to `Live` as each module ships. Modules the signed-in user may not use are hidden from the menu.

### 12.9 Workspace theme

- An admin can set a default preset and colors for the whole workspace and a workspace logo.
- Users keep their own mode, density and color changes unless the admin locks the theme.
- Themes are stored per user on the server so they follow the user across browsers. The same theme file format is used for import and export.

## 13. Additional non-functional requirements

- Connection pooling and timeouts for database sources.
- Secrets encrypted at rest; audit trail for write operations.
- Pluggable adapter packaging so new connectors ship independently.

## 14. v2.0 milestones

1. **V1 — Connectors:** PostgreSQL, MS Access, REST.
2. **V2 — Saved views and column operations.**
3. **V3 — Charts and dashboards; the Dashboard module goes live.**
4. **V4 — History, bulk edit, find/replace; the History module goes live.**
5. **V5 — Accounts, roles, and locking; the Users and Roles modules go live; workspace theme.**

## 15. Open questions

- Hosted web service, desktop wrapper, or both? This affects how file paths and uploads work.
- Should edits write directly to the original file, or to a working copy with an explicit "publish" step?
- What is the maximum supported file size for the first release?
- Which languages must ship in the first release?
- Should a theme belong to the user only (MVP), or can an admin set a workspace default and lock it (proposed for Part Two)?
- Which modules, beyond Dashboard, Users, Roles and History, should appear in the Modules menu (for example Connectors or Saved views)?
