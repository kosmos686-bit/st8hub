# CLAUDE.md — ST8 AI Hub

## Project Overview

**ST8 AI Hub** is a single-file sales CRM and AI-powered proposal generator built as a Telegram Mini App. It is a fully client-side application with no backend, build process, or package manager. The entire application lives in one file: `index .html` (note the space before the extension — this is the actual filename).

**Business context:** Internal sales tool for ST8 AI (Самара-based AI automation company). Used to manage B2B client pipeline in the HoReCa and enterprise sectors, and to generate personalized sales proposals (КП) and call scripts using the Anthropic Claude API.

---

## Repository Structure

```
/home/user/st8hub/
├── index .html     ← Entire application (HTML + CSS + JS, ~759 lines, ~56 KB)
└── CLAUDE.md       ← This file
```

There is no `package.json`, no `node_modules`, no build tooling, and no configuration files.

---

## Technology Stack

- **HTML5 / CSS3 / Vanilla JavaScript (ES5)** — no transpilation, no frameworks
- **Telegram Web App SDK** — loaded from `https://telegram.org/js/telegram-web-app.js`
- **Google Fonts** — Montserrat (weights 500–900)
- **Anthropic Claude API** — direct browser fetch to `https://api.anthropic.com/v1/messages`
  - Model: `claude-sonnet-4-20250514`
  - Max tokens: 1500
  - Auth header: `x-api-key` (user-supplied), `anthropic-dangerous-direct-browser-access: true`
- **Browser localStorage** — sole persistence layer

---

## Key Conventions

### Language
- All UI text, variable names in business logic, client data, and comments are in **Russian**.
- Code identifiers (function names, JS variables) are in **English**.

### JavaScript Style
- **ES5 only** — `var`, no `let`/`const`, no arrow functions, no template literals, no modules.
- **Global state** — all state lives in top-level `var` declarations.
- **Imperative DOM** — full re-render via `innerHTML` assignment (no virtual DOM, no diffing).
- **Inline event handlers** — `onclick="funcName()"` in HTML attributes is the pattern; event listener attachment via `.onclick =` is also used for nav buttons.
- No external linter or formatter is configured.

### CSS Style
- All CSS is inline in a `<style>` block in `<head>`.
- Short, abbreviated class names (`.hdr`, `.pg`, `.sc`, `.nb`, `.fb`, `.inp`, etc.).
- Design system colors are hardcoded constants:
  - Gold accent: `#D4A017`
  - Dark background: `#0A0F1A`
  - Surface: `#111827`
  - Border: `#1e2d45`
  - Muted text: `#6B7FA0`
  - Light text: `#E8EDF5`

---

## Application Architecture

### File Layout (inside `index .html`)

| Lines | Content |
|-------|---------|
| 1–8 | `<head>`: meta, title, Telegram SDK script, Google Fonts link |
| 9–141 | `<style>`: all CSS |
| 142–313 | `<body>`: HTML markup — header, nav, 6 tab panels, modal, toast |
| 315–759 | `<script>`: all JavaScript |

### Tab Panels
1. **`клиенты`** (clients) — KPI stats, filter row, client cards, detail panel
2. **`воронка`** (pipeline) — Kanban-style stage columns
3. **`кп`** (proposals) — Claude-powered КП generator form
4. **`звонок`** (call prep) — Claude-powered call script generator form
5. **`база кп`** (KP library) — pre-written proposal templates browser
6. **`настройки`** (settings) — API key input, data management

### Global State Variables

```javascript
var DEFAULT_CLIENTS = [...];   // Immutable seed data (11 clients)
var KPS = [...];               // Pre-written proposal templates (9 entries)
var STAGES = [...];            // Pipeline stages array (5 stages, in order)
var CLIENTS = loadClients();   // Active client list (from localStorage or DEFAULT_CLIENTS)
var curFilter = "все";         // Active stage filter string
var selId = null;              // Selected client ID (number or null)
var apiKey = "";               // Anthropic API key string
var openKP = null;             // Index into KPS array currently expanded
```

### Data Model — Client Object

```javascript
{
  id:        <number>,   // Auto-incremented unique ID via nextId()
  name:      <string>,   // Company name
  contact:   <string>,   // Contact person name
  city:      <string>,   // City
  type:      <string>,   // Business type (free text, e.g. "HoReCa / Сеть")
  stage:     <string>,   // One of STAGES values
  pkg:       <string>,   // Package tier (4 options: Старт, Оптимум, Максимум, Под ключ)
  potential: <number>,   // Deal value in RUB
  priority:  <string>,   // "high" | "medium" | "low"
  notes:     <string>    // Free-text notes
}
```

### Pipeline Stages (in order)
1. первый контакт
2. КП отправлено
3. переговоры
4. договор
5. закрыто

### Storage Keys
- `"st8_clients"` — JSON-serialized `CLIENTS` array
- `"st8_apikey"` — Anthropic API key string

---

## Key Functions Reference

### Rendering
- `renderStats()` — updates KPI cards (total clients, total potential)
- `renderFilters()` — rebuilds filter button row
- `renderCards()` — rebuilds client card list (respects `curFilter`)
- `renderDet(id)` — renders detail panel for selected client
- `renderPipeline()` — renders pipeline kanban view
- `renderKPLib()` — renders KP library list
- `render()` — calls all render functions (full refresh)

### Client CRUD
- `openAdd()` — opens modal in add mode
- `openEdit(id)` — opens modal pre-filled with client data
- `saveClient()` — creates or updates a client, saves to localStorage
- `delClient(id)` — removes client from array, saves
- `closeModal()` — hides the add/edit modal

### Navigation
- `switchTab(name)` — activates named tab and its nav button
- `setFilter(f)` — sets `curFilter` and re-renders cards
- `goKPGen(id)` — switches to КП tab with client context pre-filled
- `goCall(id)` — switches to call prep tab with client context pre-filled

### AI Features
- `genKP()` — builds prompt for proposal, POSTs to Claude API, streams result into `#kp-out`
- `genCall()` — builds prompt for call script, POSTs to Claude API, streams result into `#call-out`

### Helpers
- `sc(stage)` — returns hex color for a given pipeline stage
- `pi(priority)` — returns emoji for priority (`🔥` / `📌` / `💤`)
- `fmt(n)` — formats number as `"250к ₽"` or `"1.0М ₽"`
- `getTotalPot()` — sums all client potential values
- `nextId()` — returns max existing ID + 1
- `showToast(msg)` — displays a 2-second toast notification

### Data Management
- `exportData()` — copies JSON of `CLIENTS` to clipboard
- `importData()` — parses JSON from clipboard input, merges into `CLIENTS`
- `resetData()` — restores `CLIENTS` to `DEFAULT_CLIENTS` after confirmation

---

## Development Workflow

### Making Changes
Since there is no build step, changes to `index .html` take effect immediately on reload. To test:
1. Edit `index .html` directly.
2. Open in a browser (or Telegram Mini App preview).
3. No compilation, no `npm install`, no server required (can use any static file server or just `file://`).

### Deployment
The app is deployed via **GitHub Pages** from the `main` branch. Pushing to `main` triggers a Pages deploy. The deployment commit pattern used historically: `"trigger pages deploy"`.

### Git Workflow
- Feature work on `claude/add-claude-documentation-Ho6Cw` or similar branches.
- Merge to `main` to deploy.

### Adding a New Client Field
1. Add the field to the modal HTML (`#f-<fieldname>` input).
2. Read the field in `saveClient()`.
3. Display the field in `renderDet()` and `renderCards()` as needed.
4. Update `DEFAULT_CLIENTS` entries if the field should have default values.

### Adding a New Tab
1. Add a `<button class="nb" data-tab="<name>">` in `.nav`.
2. Add a `<div class="tab" id="tab-<name>">` in `.pg`.
3. Implement a render function and call it from `render()` or lazily on tab switch.

---

## AI Integration Details

### Anthropic API Call Pattern
```javascript
fetch("https://api.anthropic.com/v1/messages", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "x-api-key": apiKey,
    "anthropic-version": "2023-06-01",
    "anthropic-dangerous-direct-browser-access": "true"
  },
  body: JSON.stringify({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1500,
    messages: [{ role: "user", content: prompt }]
  })
})
```

### API Key Requirements
- Must start with `"sk-"` — validated before calls
- Stored in `localStorage` under `"st8_apikey"`
- Never sent to any server other than `api.anthropic.com`

---

## Important Constraints for AI Assistants

1. **Do not introduce a build system or package manager** unless explicitly requested. This project is intentionally dependency-free.
2. **Keep ES5 syntax** — no arrow functions, no `const`/`let`, no template literals, no destructuring.
3. **Do not split into multiple files** — single-file architecture is intentional.
4. **Preserve the filename** `index .html` (with the space) — changing it would break GitHub Pages.
5. **All UI text must remain in Russian** — this is a Russian-language product.
6. **Do not add a backend** — the application is designed to be client-side only.
7. **Do not encrypt or obfuscate localStorage data** — it is read directly by export/import tools.
8. **Test in mobile viewport** — the app is designed for Telegram Mini App (mobile-first).
