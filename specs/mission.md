⚠️ **IMPORTANT:** Before beginning implementation on the roadmap phases, use the AskUserQuestion tool to confirm:
1. **Backend preference:** Async end-to-end with FastAPI + asyncpg + PostgreSQL, or alternative stack?
2. **Frontend framework:** Nuxt 4 with Vue 3 + TypeScript, or alternative (SvelteKit, Next.js)?
3. **Deployment target:** Docker Compose for local dev, cloud platforms (AWS/GCP/Azure), or self-hosted?

These decisions affect tooling setup and all subsequent phases. Get explicit sign-off before proceeding to Phase 0.

---

# Findr Mission

## Purpose

Findr is a web application that makes working with tabular data simple and safe. Users can open CSV, TSV, or Excel files directly in the browser, browse and edit data with confidence, and save changes back to the original file without losing data or introducing corruption.

## Core Values

### Safety First
- No silent data loss. Every change is visible and reviewable before save.
- Atomic writes: a failed save leaves the original file untouched.
- Automatic backups before the first write in a session.
- Conflict detection: if a file changes on disk, the user chooses whether to reload or overwrite.

### Simplicity
- Open a file in a few clicks. No configuration, no accounts (MVP).
- Direct editing: see the data in a table, click to edit, save.
- One consistent visual style, customizable by color and density.
- Fast: large files (100k+ rows) page on demand, not loaded all at once.

### Speed
- First page of a 100k-row file displays in under 2 seconds.
- Scrolling and paging stay under 300 ms per request.
- Instant theme changes without a page reload.

## Target Users

Anyone who keeps data in spreadsheets or flat files and wants to:
- View, search, and fix data without opening Excel or a text editor.
- Make changes with visual feedback and the ability to undo or discard.
- Share data across a team with version control and change history (v2+).

## Success Metrics

**MVP (v0.1):**
- Users can add, edit, and delete rows in CSV/Excel files and save atomically.
- Theme is fully customizable and persists across sessions.
- Performance targets met: 2s first page, 300ms per request.
- Zero data loss in the test suite: saves are atomic, backups exist, conflicts are detected.

**Part Two (v2.0):**
- Support databases (PostgreSQL, MySQL, SQLite) and REST APIs alongside files.
- Enable multi-user collaboration with role-based permissions and change history.
- Charts and saved views let users analyze data without leaving Findr.

## Non-Goals (MVP)

- Real-time collaboration (planned for v2).
- Complex formulas, pivot tables, or cell styling (view-only or unsupported).
- Mobile app or offline mode (responsive web app only).
- Advanced data transformation or ETL workflows.
