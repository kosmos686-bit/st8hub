# STRUCTURE.md — Directory Layout & Organization

## Root Directory: `c:\st8-workspace\`

### Core Application Files
```
jarvis.py                  # Main bot — 2082 lines, 111KB. Polling loop, agents, scheduler hooks
scheduler.py               # Background scheduler — 1447 lines. Daily jobs, news digest, lead gen
jarvis_watchdog.py         # Process watchdog — auto-restarts jarvis.py on crash, mutex guard
telegram_leads.py          # Telegram lead card sender
leads.py                   # Lead processing utilities
```

### Configuration & Environment
```
.env                       # API keys (ANTHROPIC_API_KEY, JARVIS_BOT_TOKEN, TAVILY_API_KEY, etc.)
CLAUDE.md                  # Jarvis behavior spec — role, morning briefing format, P0/P1/P2 priorities
```

### Data Directories
```
st8hub/                    # Lead hub (git repo)
  leads.json               # All leads — structured JSON array
  entities.json            # Named entities
  mempalace.yaml           # MemPalace MCP config
  index.html               # Hub web view

st8-memory-bank/           # Long-term project memory (markdown files)
  activeContext.md         # Current tasks and focus
  clientPipeline.md        # Client deal statuses
  airi_context.md          # AIRI partnership context
  productContext.md        # Product strategy
  systemPatterns.md        # Architecture decisions
  decisionLog.md           # Key decisions log
  progress.md              # Progress tracking

agent_memory/              # Per-client agent memory files
  airi.md                  # AIRI deal context
  bolshakova.md            # Bolshakova deal context
  target_clients.md        # Target client profiles
  st8_context.json         # ST8 system context
```

### Runtime State Files
```
jarvis_memory.json         # Conversation history (last N turns)
jarvis_offset.json         # Telegram polling offset
jarvis_session_log.json    # Agent session relay log
jarvis_live.log            # Live structured log (API costs, model used)
jarvis_watchdog.log        # Watchdog restart history
jarvis_stdout.log          # stdout from jarvis.py (usually empty)
leads_status.md            # Markdown table: date/company/lpr/status/comment
```

### Virtual Environments
```
.venv/                     # Dev venv (used when running jarvis.py manually)
venv_jarvis/               # Production venv (used by jarvis_watchdog.py)
```

### Parsers & Utilities
```
au_official.py             # Official AU parser
bankrot_efrs.py            # Bankruptcy EFRS parser
bankrot_playwright.py      # Playwright-based bankruptcy parser
map_parser.py              # 2GIS map parser for leads
sro_au_parser.py           # SRO AU parser
sro_moscow_parser.py       # SRO Moscow parser
stealth_parser.py          # Stealth web scraper
test_search.py             # Search test utilities
```

### Backup Files (cleanup candidates)
```
jarvis.pypython             # Backup from Apr 13 (97KB) — used for recovery
jarvis_backup.py            # Backup from Apr 12 (97KB)
jarvis_backup_original.py   # Backup from Apr 12 (97KB)
fix_yulia.py                # One-off fix script
upgrade_jarvis_agents.py    # One-off upgrade script
```

### Output / Reports
```
daily_digest_2026-04-*.md  # Daily news digests (auto-generated)
ab_results.md              # A/B test results
ab_analysis_*.md           # A/B analysis reports
MARKETING-AUDIT.md         # Marketing audit document
kp/                        # Commercial proposals (КП)
```

### Other Projects (co-located)
```
budget-app/                # Separate budget app project
ai-marketing-claude/       # AI marketing project
st8-voice-reanimator/      # Voice reanimator project
backups/                   # General backups
```

## Key Location Quick Reference

| What | Where |
|------|-------|
| Add/edit agent prompt | `jarvis.py` — `BUILTIN_AGENTS` dict (line ~75) |
| Agent routing rules | `jarvis.py` — `AGENT_ROUTER_PROMPT` (line ~373) |
| Scheduled tasks | `jarvis.py` — `check_moscow_jarvis_tasks()` + `scheduler.py` |
| Morning briefing | `jarvis.py` — `make_good_morning()` |
| Weather function | `jarvis.py` — `get_moscow_weather()` (line ~1322) |
| Lead storage | `st8hub/leads.json` |
| Conversation memory | `jarvis_memory.json` |
| Long-term memory | `st8-memory-bank/*.md` |
| API keys | `.env` |

## Naming Conventions

- **Functions**: `snake_case`, verb-first (`make_good_morning`, `get_moscow_weather`, `load_memory`)
- **Agent names**: kebab-case strings (`sales-hunter`, `st8-bot-developer`)
- **Private helpers**: underscore prefix (`_truncate_context`, `_is_low_quality`, `_RESPONSE_CACHE`)
- **Constants**: `UPPER_SNAKE_CASE` (`JARVIS_CHAT_ID`, `CLAUDE_MODEL`, `BASE_DIR`)
- **Log files**: `jarvis_*.log`
- **Backup files**: `jarvis_*.py` or `jarvis_backup*.py`
