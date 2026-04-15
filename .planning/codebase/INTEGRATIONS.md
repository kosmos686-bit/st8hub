# External Integrations

**Analysis Date:** 2026-04-15

## APIs & External Services

**AI/ML:**
- Anthropic Claude - Primary LLM for agents and responses
  - SDK/Client: `anthropic` package (v0.76.0)
  - Auth: `ANTHROPIC_API_KEY` environment variable
  - Models: `claude-haiku-4-5-20251001` (mem0 embedding), `claude-sonnet-4-20250514` (primary reasoning)
  - Usage in `jarvis.py` (line 683): `anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)`
  - Usage in `scheduler.py` (line 50): Claude client for outreach generation

**Web Search & Intelligence:**
- Tavily - Real-time web search for lead research
  - SDK/Client: `tavily` package (v0.7.23)
  - Auth: `TAVILY_API_KEY` environment variable
  - Function: `_tavily_search()` in `jarvis.py` (line 1379) - 3 max results per query
  - Used for: Researching company news, problems, director info during outreach

**Contacts & Location Data:**
- 2GIS API - Russian business directory and contact lookup
  - Auth: `DGIS_API_KEY` environment variable
  - Function: `search_2gis_contacts()` in `scheduler.py` (line 253)
  - Purpose: Extract phone, website, director info from 2GIS catalog
  - Endpoint: `https://catalog.api.2gis.com/3.0/items`

**Weather:**
- Open-Meteo - Free weather API (no auth required)
  - Endpoint: `https://api.open-meteo.com/v1/forecast`
  - Function: `get_moscow_weather()` in `jarvis.py` (line 1325)
  - Parameters: Moscow (lat=55.75, lon=37.62), daily forecast
  - Returns: Temperature, weather code, wind speed (see CLAUDE.md weather block)

## Data Storage

**Databases:**
- Qdrant (Vector DB) - Persistent semantic memory via mem0
  - Connection: Embedded path `mem0_db/` directory
  - Client: `mem0` package with Qdrant provider
  - Config: Collection `jarvis_mem`, embedding_model_dims=384
  - Purpose: Long-term conversation memory, agent context
  - Location: `jarvis.py` lines 56-63

- ChromaDB (Vector DB) - Mempalace semantic search
  - Connection: Local persistent client at `~/.mempalace/palace/`
  - Client: `chromadb.PersistentClient()`
  - Collection: `mempalace_drawers`
  - Purpose: Semantic search over user memory bank
  - Location: `jarvis.py` line 542-545

**File Storage:**
- Local JSON Files (Git-synced)
  - `st8hub/leads.json` - Lead database with statuses, contacts, metadata
  - `jarvis_memory.json` - Trimmed conversation history
  - `jarvis_offset.json` - Telegram update offset (resume point)
  - `jarvis_session_log.json` - Agent interaction log
  - `AGENT_MEMORY_DIR/` - Per-client JSON memory files

**Version Control:**
- GitHub (via GitPython)
  - Remote: `https://github.com/kosmos686-bit/st8hub.git` (configurable via `GITHUB_HUB_REMOTE`)
  - Auth: `GITHUB_TOKEN` environment variable
  - Function: `git_push_hub()` in `scheduler.py` (line 697)
  - Commits: Lead response updates, status changes

## Authentication & Identity

**Auth Provider:**
- Telegram Bot API (custom implementation)
  - Endpoint: `https://api.telegram.org/bot{JARVIS_BOT_TOKEN}/sendMessage`
  - Method: Token-based (bot token issued by BotFather)
  - Implementation: `python-telegram-bot` library with polling (see `poll_jarvis()` in `jarvis.py` line 1981)

**User Identification:**
- Telegram Chat IDs
  - `JARVIS_CHAT_ID` - Main polling chat
  - `YULIA_CHAT_ID` - Default recipient for messages
  - Hardcoded in environment, no user registration system

## Monitoring & Observability

**Error Tracking:**
- Not detected - Errors logged to `jarvis_live.log` only

**Logs:**
- File-based:
  - `jarvis_live.log` - Live activity log (separate handler, not suppressed by `logging.disable()`)
  - `jarvis_watchdog.log` - Watchdog restart events
  - `sched_*.txt` - Scheduler stdout/stderr
- Format: Plain text with timestamps
- Location: Project root directory
- Archival: Logs persist until manually cleaned

**Monitoring:**
- Process supervision: `jarvis_watchdog.py` auto-restarts crashed Jarvis with exponential backoff
  - Max 20 restart attempts per session
  - 10-second delay between restarts
  - 5-minute pause after 5 fast crashes (<30 sec)

## CI/CD & Deployment

**Hosting:**
- None detected - Pure CLI application running on Windows machine
- Execution: via `jarvis_watchdog.py` (supervisor) spawning `jarvis.py`

**CI Pipeline:**
- None detected - Manual deployment, git push via `git_push_hub()` function

**Scheduler:**
- `schedule` library (v1.2.2) - Cron-like job scheduling
- Jobs registered in `scheduler.py` (loaded via `run_polling()` from jarvis)
- Runs: 08:00 Moscow time daily summary, periodic lead enrichment, task checks

## Webhooks & Callbacks

**Incoming:**
- Telegram message polling (long polling, not webhooks)
  - Method: `bot.get_updates()` with offset tracking
  - Allowed updates: `['message', 'channel_post']`
  - Location: `poll_jarvis()` in `jarvis.py` line 1981

**Outgoing:**
- Telegram message sending
  - Method: Direct API call to `https://api.telegram.org/bot{token}/sendMessage`
  - Usage: Manual Telegram messages from Jarvis functions
  - Location: `jarvis.py` line 1013, multiple `tool_send_*` functions

- GitHub push events
  - Method: Git commit + push to remote
  - Triggered: When lead status changes, responses recorded
  - Location: `scheduler.py` line 693

## Environment Configuration

**Required env vars:**
- `JARVIS_BOT_TOKEN` - Telegram bot authentication
- `ANTHROPIC_API_KEY` - Claude API access
- `TAVILY_API_KEY` - Web search access
- `DGIS_API_KEY` - 2GIS contact lookup
- `BOT_TOKEN` - Secondary token (scheduler polling)
- `JARVIS_CHAT_ID` - Telegram chat ID for polling
- `YULIA_CHAT_ID` - Default recipient chat ID

**Optional env vars:**
- `GMAIL_USERNAME` / `GMAIL_PASSWORD` - Email delivery (defaults to Juliapopova2023@gmail.com)
- `GITHUB_TOKEN` - GitHub auth (if not in default git config)
- `GITHUB_HUB_REMOTE` - GitHub URL (defaults to kosmos686-bit/st8hub)

**Secrets location:**
- `.env` file in project root (loaded via `python-dotenv`)
- Never committed to git (should be in `.gitignore`)

## Integration Points Summary

| Service | Purpose | Required | Fallback |
|---------|---------|----------|----------|
| Anthropic Claude | AI reasoning, agents, responses | Yes | None - critical |
| Telegram Bot API | Chat interface | Yes | None - critical |
| Tavily Search | Lead research | Yes (for outreach) | CLI search fallback |
| 2GIS API | Contact extraction | No | Tavily web search |
| Open-Meteo | Weather forecasts | No | "No data" response |
| Qdrant (mem0) | Long-term memory | No (lazy init) | In-memory only |
| ChromaDB | Mempalace search | No (lazy init) | Search disabled |
| GitHub | Lead sync | Optional | Local JSON only |
| Gmail SMTP | Email delivery | No | Telegram only |

---

*Integration audit: 2026-04-15*
