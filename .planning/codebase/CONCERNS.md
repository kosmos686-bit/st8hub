# CONCERNS.md — Technical Debt, Issues & Areas of Concern

## Critical Issues

### 1. Mojibake Encoding in jarvis.py
**Severity:** High  
**Location:** `jarvis.py` — lines 1879-1897, 1032-1048, and scattered throughout  
**Issue:** Russian Cyrillic text stored as `\uXXXX` escape sequences (cp1251 bytes embedded in UTF-8 file). Breaks readability and makes editing via text tools unreliable.  
**Fix:** Byte-level rewrite of affected sections, or full UTF-8 normalization pass.

### 2. Dead Code: `process_incoming_message()`
**Severity:** High  
**Location:** `jarvis.py` line 1866  
**Issue:** Function defined (with weather hook, lead detection logic, command routing) but **never called**. Actual message flow goes through `poll_jarvis()` → `process_with_agent()` directly. Weather fixes applied here have no effect.  
**Fix:** Either wire it into `poll_jarvis()` or remove it and apply logic directly in `poll_jarvis()`.

### 3. No .gitignore — API Keys at Risk
**Severity:** High  
**Location:** `.env` (root), `st8hub/` (git repo)  
**Issue:** No `.gitignore` exists. `.env` contains `ANTHROPIC_API_KEY`, `JARVIS_BOT_TOKEN`, `TAVILY_API_KEY` etc. Accidental `git add .` would expose credentials.  
**Fix:** Add `.gitignore` with `.env`, `*.log`, `__pycache__/`, `*.pyc`, `jarvis_memory.json`, `jarvis_offset.json`.

### 4. Zero Test Coverage
**Severity:** High  
**Location:** All `.py` files  
**Issue:** 2082 lines in `jarvis.py`, 1447 lines in `scheduler.py`, zero automated tests. `test_search.py` and `test_search_now.py` are ad-hoc manual scripts, not a test suite.  
**Fix:** Add pytest with unit tests for: agent routing, lead parsing, weather function, `make_good_morning()` priority logic.

---

## Medium Priority Issues

### 5. Silent Exception Handlers
**Severity:** Medium  
**Location:** `jarvis.py` — 38+ bare `except Exception:` blocks  
**Issue:** Errors suppressed silently. Example: `get_moscow_weather()` returns fallback string on any error without logging the actual exception.  
**Fix:** Add `_live_log.warning(f"...: {exc}")` in all exception handlers.

### 6. Duplicate Virtual Environments
**Severity:** Medium  
**Location:** `.venv/` and `venv_jarvis/`  
**Issue:** Two separate venvs exist. `jarvis_watchdog.py` uses `venv_jarvis`, manual runs use `.venv`. Package versions may differ, causing inconsistent behavior.  
**Fix:** Consolidate to one venv, update watchdog to use it, delete the other.

### 7. Unused Import in scheduler.py
**Severity:** Low-Medium  
**Location:** `scheduler.py` line 32  
**Issue:** `from jarvis import check_moscow_jarvis_tasks, run_polling` — `run_polling` is imported but never called. Comment in `__main__` says "Polling управляется через jarvis_watchdog.py".  
**Fix:** Remove `run_polling` from import.

### 8. Race Condition on Memory File
**Severity:** Medium  
**Location:** `jarvis.py` — `save_memory()` / `load_memory()`  
**Issue:** `jarvis_memory.json` read/write has no file locking. If `poll_jarvis` and `check_moscow_jarvis_tasks` run simultaneously (they run in separate threads), concurrent writes can corrupt the JSON.  
**Fix:** Use `threading.Lock()` or `filelock` around memory read/write.

### 9. Unbounded In-Memory Cache
**Severity:** Medium  
**Location:** `jarvis.py` — `_RESPONSE_CACHE` dict  
**Issue:** LRU cache capped at 256 entries (`_CACHE_MAX = 256`) but eviction logic may not work correctly — dict doesn't auto-evict. Cache grows until process restart.  
**Fix:** Use `functools.lru_cache` or implement proper LRU eviction (remove oldest key when limit reached).

### 10. `logging.disable(logging.CRITICAL)` Kills All Logs
**Severity:** Medium  
**Location:** `jarvis.py` line 13  
**Issue:** Standard logging completely disabled at startup. Only `jarvis_live.log` via separate handler works. Errors from libraries (telegram, anthropic) are silently swallowed.  
**Fix:** Remove `logging.disable(CRITICAL)`. Set appropriate log levels per logger instead.

---

## Low Priority / Cleanup

### 11. Hardcoded Chat ID
**Severity:** Low  
**Location:** `jarvis.py` line ~675  
**Issue:** `JARVIS_CHAT_ID` hardcoded in source. Should be in `.env`.

### 12. Aggressive Polling Interval
**Severity:** Low  
**Location:** `jarvis.py` — `POLL_INTERVAL = 3`  
**Issue:** 3-second polling vs Telegram best practice of 30-60s for non-critical bots. Increases API call volume unnecessarily.

### 13. Backup Files in Root
**Severity:** Low  
**Location:** Root directory  
**Issue:** `jarvis.pypython`, `jarvis_backup.py`, `jarvis_backup_original.py` — three backup files from encoding accident (Apr 12-13). Should be moved to `backups/` or deleted.

### 14. Hardcoded Date in Scheduler
**Severity:** Low  
**Location:** `jarvis.py` line 2033  
**Issue:** `datetime(2026, 4, 21)` hardcoded one-shot reminder. Date has passed → dead code. Should be cleaned up.

### 15. No README or Setup Docs
**Severity:** Low  
**Issue:** New developer has no way to understand how to set up the environment, what `.env` keys are needed, or how to run the system.

---

## Security Concerns

| Concern | Location | Risk |
|---------|----------|------|
| API keys in `.env` with no `.gitignore` | Root | High — accidental commit |
| `JARVIS_BOT_TOKEN` accessible to all code | `jarvis.py` global | Medium |
| No input sanitization on Telegram messages | `poll_jarvis()` | Medium — prompt injection |
| `subprocess.run()` in scheduler with git commands | `scheduler.py` 702-710 | Low — controlled inputs |

## Performance Concerns

| Concern | Location | Impact |
|---------|----------|--------|
| 3s polling loop | `jarvis.py` `POLL_INTERVAL` | Minor — Telegram API load |
| Full memory load on every message | `load_memory()` in `poll_jarvis` | Minor — small file |
| `schedule.every(1).minutes` check | `scheduler.py` | Acceptable |
| No connection pooling for HTTP calls | `urllib.request` | Minor |
