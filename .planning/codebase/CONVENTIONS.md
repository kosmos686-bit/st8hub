# Coding Conventions

**Analysis Date:** 2026-04-15

## Naming Patterns

**Files:**
- Lowercase with underscores: `jarvis.py`, `scheduler.py`, `leads.py`
- Backup/backup files: `jarvis_backup.py`, `jarvis_watchdog.py`
- Domain scripts: `stealth_parser.py`, `bankrot_efrs.py`, `map_parser.py`

**Functions:**
- snake_case for all functions: `load_memory()`, `save_offset()`, `generate_jarvis_text()`
- Private/internal functions prefixed with underscore: `_get_mem0()`, `_cache_md5()`, `_is_low_quality()`, `_truncate_context()`
- Agent-related functions: `route_to_agent()`, `process_with_agent()`, `detect_chain_hint()`
- Utility functions grouped logically: file I/O (`load_json()`, `read_file()`), API calls (`get_moscow_weather()`, `_tavily_search()`)

**Variables:**
- snake_case for local/module variables: `user_message`, `lead_data`, `cache_key`
- UPPERCASE for module-level constants: `MOSCOW_TZ`, `BASE_DIR`, `MAX_MEMORY`, `POLL_INTERVAL`, `MEMORY_PATH`, `CLAUDE_MODEL`
- Abbreviated constants for models: `_HAIKU_MODEL`, `_SONNET_MODEL`, `_HAIKU_KEYWORDS`, `_SONNET_KEYWORDS`
- Dictionary/cache constants: `_RESPONSE_CACHE`, `_JARVIS_PROMPT_CACHE`, `AGENT_KEYWORDS`, `AGENT_CHAINS`, `CLIENT_SLUGS`
- Protected module-level: `_mem0_instance`, `_MEMPALACE_CLIENT`, `_live_log`, `_router`

**Types:**
- Classes use PascalCase: `ST8ModelRouter`, `Anthropic`, `Bot`
- Type hints used sparingly (Python 3.7 compatible approach)

**Environment Variables:**
- SCREAMING_SNAKE_CASE: `JARVIS_BOT_TOKEN`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, `GITHUB_TOKEN`, `GMAIL_USERNAME`

## Code Style

**Formatting:**
- Line length: Mixed (many lines >100 chars, no strict enforcement detected)
- Indentation: 4 spaces (Python standard)
- String quotes: Single quotes preferred for consistency
- UTF-8 encoding explicitly specified: `encoding='utf-8'` in all file operations

**Imports:**
- Standard library imports first (asyncio, os, json, re, etc.)
- Third-party imports follow (dotenv, anthropic, telegram, etc.)
- Import errors suppressed: `warnings.filterwarnings('ignore')`, `logging.disable(logging.CRITICAL)`

**Linting:**
- No formal linting configuration detected (.flake8, .pylintrc, etc.)
- Code follows PEP 8 loosely but pragmatically
- Some Unicode encoding issues present (Cyrillic text sometimes appears as escaped sequences in literals)

## Import Organization

**Order (observed in jarvis.py):**
1. Standard library: `asyncio`, `hashlib`, `json`, `os`, `re`, `time`, `urllib`, `warnings`, `logging`
2. Date/time: `datetime`, `timedelta`, `pytz`
3. Third-party: `dotenv`, `anthropic`, `telegram`, `chromadb` (optional)
4. Local module imports: None (monolithic structure), but conditional imports used
5. Lazy imports: `from mem0 import Memory` wrapped in function with try/except for optional dependencies

**Path Aliases:**
- Uses `os.path.join()` and `os.path.dirname()` extensively
- `BASE_DIR = os.path.dirname(__file__)` as root reference
- Conditional path construction: `os.path.join(os.path.expanduser('~'), '.mempalace', 'palace')`

## Error Handling

**Patterns:**
- Broad try/except blocks with generic `Exception` catch:
  ```python
  try:
      # operation
  except Exception as e:
      return None  # or default value
  ```
- Silent failures common: errors logged to print/file or silently caught with return None
- TelegramError handled specifically: `except TelegramError as exc:`
- Retry logic for API overload: checks for "529" or "overloaded" in error string, sleeps 10-15s, retries

**Error Messages:**
- Localized: Russian error messages ("Ошибка Claude:", "Jarvis failed to send message:")
- Contextual logging: Print statements for debugging and state tracking

**Lazy Initialization:**
- `_get_mem0()`: Returns None if mem0 import fails, globals managed with `_mem0_instance`
- Optional dependencies never crash the main application

## Logging

**Framework:** Custom logger + print statements

**Pattern:**
- Live log created separately from disabled main logging:
  ```python
  _live_log = logging.getLogger('jarvis_live')
  _live_log.setLevel(logging.INFO)
  _live_log.handlers = [FileHandler('jarvis_live.log')]
  ```
- Cost tracking logged: `_live_log.info('model=%s tokens_in=%d tokens_out=%d estimated_cost=$%.5f', ...)`
- Cache hits logged: `_live_log.info('cache_hit=True key=%s', cache_key[:8])`
- Print statements used for temporary diagnostics: `print(f"[{category}] ...")` with contextual prefixes

**Levels:**
- INFO: Cost tracking, cache operations, API calls
- No ERROR or WARNING levels used (main logging disabled)
- stderr not explicitly used

## Comments

**When to Comment:**
- Section dividers: `# ── Section Name ────` (visual separators)
- Agent definitions: Brief inline descriptions within BUILTIN_AGENTS dict
- Complex regex patterns: Inline comments before pattern definition
- Minimal inline comments; code is generally self-documenting

**Style:**
- Russian language predominant (matching user context)
- Brief: "Cascade router Haiku→Sonnet with LRU cache, prompt caching, and cost logging."
- No JSDoc/docstrings used (only one class has minimal docstring: `ST8ModelRouter`)

## Function Design

**Size:** 
- Range: 10-50 lines typical, some up to 100+ (make_good_morning, process_with_agent)
- No strict enforcement; complexity varies by domain

**Parameters:**
- Positional: text, model, client, messages, history
- Keyword arguments for configuration: `max_tokens=1000`, `max_chars=1800`
- Optional parameters with defaults: `path: str`, `max_chars: int = 1800`

**Return Values:**
- Explicit: Functions return data structures or status strings
- None: Used for "not found" or "error" conditions (e.g., `load_memory()` returns [] on error, not None)
- Tuple returns for multi-value: `(telegram_text, max_text)`, `(jarvis_prompt, hub_block)`
- String returns for user-facing responses (Telegram messages)

**Side Effects:**
- File I/O common: `load_json()`, `save_memory()`, `_save_lead_to_hub()`
- Global state modification: `_mem0_instance`, `_RESPONSE_CACHE`, `_JARVIS_PROMPT_CACHE`
- API calls: All model.create() calls have side effects (cost tracking, logging)

## Module Design

**Exports:**
- Functions exported at module level: No explicit `__all__` defined
- Everything public unless prefixed with `_`
- Conditional exports: Functions that call other modules' functions directly

**Barrel Files:**
- Not used; monolithic structure in `jarvis.py` (2064 lines)
- Scheduler imports from jarvis: `from jarvis import check_moscow_jarvis_tasks, run_polling`

**Patterns:**
- Agent routing: `AGENT_KEYWORDS` dict maps keywords to agent names
- Agent chains: `AGENT_CHAINS` dict for sequential agent execution
- Memory bank: Multiple MD files loaded at runtime from `st8-memory-bank/` directory
- Lead hub: JSON file (`st8hub/leads.json`) as single source of truth for leads

## Database & State Management

**State Storage:**
- JSON files for persistence: `jarvis_memory.json`, `jarvis_offset.json`, `st8hub/leads.json`
- Markdown tables parsed: `leads_status.md` (pipe-separated, no formal parser)
- Optional Mem0 vector DB: Semantic search fallback with qdrant backend
- Optional ChromaDB: For mempalace integration

**Patterns:**
- Load-modify-save: `load_json()` → modify in memory → `dump(json.dump())`
- Atomic writes: Direct file overwrite, no transactional guarantees
- In-memory cache: `_RESPONSE_CACHE` (LRU with max size 256)

## API Integration Patterns

**Anthropic Claude:**
- `claude_client.messages.create(model=..., messages=..., system=...)`
- Prompt caching: `system=[{'type': 'text', 'text': prompt, 'cache_control': {'type': 'ephemeral'}}]`
- Cost tracking: tokens_in/out multiplied by model-specific rates
- Model selection: `_HAIKU_MODEL` for cheap tasks, `_SONNET_MODEL` for complex

**Telegram Bot:**
- `Bot(token=...)` with async send: `asyncio.run(bot.send_message(...))`
- Error handling: `TelegramError` caught separately
- Parse mode: 'Markdown' for formatting

**External APIs:**
- Tavily (search): `tavily_client.search(query=..., max_results=...)`
- 2GIS (contacts): `urllib.request` with SSL context bypass
- Open-Meteo (weather): `urllib.request` with JSON response parsing

## Async/Await Patterns

**Usage:**
- Minimal: Only in Telegram message sending via `asyncio.run()`
- Not used for API calls (Anthropic, Tavily are blocking)
- Threading used in scheduler for concurrent job execution

## Data Validation

**Approach:**
- Defensive: `.get()` with defaults everywhere
- Type coercion: `datetime.strptime()` with exception fallback
- String parsing: Regex patterns for extraction/validation
- JSON validation: Try/except `json.loads()` with fallback parsing using regex

**Example:**
```python
company = (row.get('company') or '').strip()
if not company or company.startswith('-'):
    continue  # Skip invalid rows
```

## Testing Patterns (if any)

- Test files exist: `test_search.py`, `test_search_now.py`
- Pattern: Direct script execution, no unittest/pytest framework
- Manual testing: Print statements for verification
- Integration tests implicit in scheduler execution

---

*Convention analysis: 2026-04-15*
