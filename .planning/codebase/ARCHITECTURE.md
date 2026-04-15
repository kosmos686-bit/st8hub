# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** Multi-agent routing system with Telegram bot frontend, Claude AI backbone, scheduled task worker, and persistent memory.

**Key Characteristics:**
- **Agent-based dispatch:** Route user messages to specialized agents (12 builtin + external)
- **Stateful conversation:** Persistent memory (conversation history + long-term context)
- **Scheduled automation:** Daily recurring tasks (morning briefing, lead generation, reports)
- **Watchdog pattern:** Auto-restart on crash with exponential backoff
- **Claude cascade:** Haiku→Sonnet cost optimization with LRU cache and prompt caching

## Layers

**Telegram Bot Layer:**
- Purpose: Receive and send messages via Telegram Bot API
- Location: `jarvis.py` lines 1981-2027 (`poll_jarvis()` async loop)
- Contains: Polling loop, message handling, file extraction (PDF/DOCX)
- Depends on: Bot token (JARVIS_BOT_TOKEN), Telegram library, message processing layer
- Used by: User via Telegram chat (ST8-AI founder's personal chat)

**Message Processing Layer:**
- Purpose: Determine message type and route to appropriate handler
- Location: `jarvis.py` lines 1866-1952 (`process_incoming_message()`)
- Contains: Weather detection, lead detection, command parsing, agent routing
- Depends on: Agent routing system, weather API, lead extraction
- Used by: Telegram polling layer, scheduler context functions

**Agent Routing & Execution:**
- Purpose: Identify appropriate agent and execute with Claude AI
- Location: `jarvis.py` lines 393-416 (`route_to_agent()`), lines 613-695 (`process_with_agent()`)
- Contains: Agent selection logic, prompt construction, Claude API calls, session logging
- Depends on: Builtin agent prompts, external agents (from `~/.claude/agents/`), Claude client, memory
- Used by: Message processing layer

**Builtin Agent Prompts:**
- Purpose: Define 12 specialized agent personalities for sales, strategy, security, development
- Location: `jarvis.py` lines 75-349 (BUILTIN_AGENTS dict)
- Contains: Sales Hunter, Sales Closer, Objection Handler, KP Writer, Deal Analyst, KP Architect, Sales Strategist, HoReCa Consultant, Bot Developer, Backend Architect, Security Auditor, AI Director
- Depends on: None (pure prompt text)
- Used by: Agent routing layer

**Memory Subsystem:**
- Purpose: Store and retrieve conversation history and agent memory
- Location: `jarvis.py` lines 1203-1229 (conversation history), lines 891-975 (agent memory per client)
- Contains: Conversation history (JSON), per-client agent memory (Markdown), session log
- Depends on: Filesystem, mem0 optional long-term memory, qdrant vector store
- Used by: Message processing, agent execution, memory search

**Long-Term Memory (Optional):**
- Purpose: Semantic search and recall of important business context
- Location: `jarvis.py` lines 35-68 (_get_mem0() lazy init)
- Contains: Mem0 with Anthropic Claude + HuggingFace embeddings + Qdrant vector store
- Depends on: mem0 library, Qdrant collection at `mem0_db/`
- Used by: Agent system prompts (via _build_jarvis_system_prompt)

**Hub Data & Leads:**
- Purpose: Centralized storage of leads with metadata and status
- Location: `st8hub/leads.json` (JSON database), `st8hub/mempalace.yaml` (entity store)
- Contains: Lead objects with company_name, phone, status, source, timestamps
- Depends on: Filesystem
- Used by: Scheduler (lead generation), message processing (smart_add_lead), reporting

**Memory Bank (Strategic Context):**
- Purpose: Single source of truth for business strategy, clients, patterns
- Location: `st8-memory-bank/` directory (Markdown + YAML files)
- Contains: productContext, systemPatterns, clientPipeline, activeContext, decisionLog, progress
- Depends on: Filesystem
- Used by: Agent system prompts, memory searches (mempalace queries)

**Scheduler Layer:**
- Purpose: Execute recurring tasks on schedule (leads, reports, analytics)
- Location: `scheduler.py` (entire file)
- Contains: Job definitions, schedule config, Tavily search integration, 2GIS API calls
- Depends on: Schedule library, Tavily API, 2GIS API, Claude AI, Telegram bot
- Used by: Standalone process (run alongside jarvis.py)

**Watchdog Layer:**
- Purpose: Monitor jarvis.py process and auto-restart on crash
- Location: `jarvis_watchdog.py` (entire file)
- Contains: Process supervision, crash detection, exponential backoff
- Depends on: Windows mutex (process locking)
- Used by: System startup (run jarvis_watchdog.py instead of jarvis.py directly)

## Data Flow

**Incoming Message → Response:**

1. Telegram polls for updates → `poll_jarvis()` (async)
2. Extract message text or document → `extract_file_text()` if PDF/DOCX
3. Load conversation history → `load_memory()`
4. Route to handler via `process_with_agent()`:
   - Check if weather question → return `get_moscow_weather()`
   - Check if smart add-lead → return lead confirmation
   - Check if command (e.g., `/план`, `/лиды`) → call command handler
   - Check if agent/chain trigger → call `run_agent_or_chain()`
   - Otherwise → call `generate_smart_response()`
5. Claude processes message with agent system prompt
6. Append to history → `save_memory()`
7. Send reply via Telegram → `bot.send_message()`

**Scheduled Task Execution:**

1. `scheduler.py` checks schedule every minute
2. If time matches (e.g., 08:00) → execute job function
3. Job may call Claude, Tavily, 2GIS APIs
4. Generate Markdown/JSON output
5. Send to Telegram via `send_jarvis_message()` or `send_lead_card()`
6. Update `st8hub/leads.json` if applicable

**Watchdog Supervision:**

1. `jarvis_watchdog.py` launches `jarvis.py` as subprocess
2. Monitor exit code and runtime duration
3. If crash detected:
   - Count fast crashes (< 30 sec)
   - After 5 fast crashes → pause 5 minutes
   - Restart up to 20 times total
4. On clean exit (code 0) → stop watchdog

## State Management

**Conversation History:**
- Format: JSON list of {role, content, ts} objects
- Location: `memory.json` (in working directory)
- Scope: Lifetime of bot instance (single user context)
- Persisted: Yes, loaded at startup

**Agent Memory (Per Client):**
- Format: Markdown with client name as key
- Location: `agent_memory/{client_slug}.md`
- Scope: Per-client conversation history with agent actions
- Persisted: Yes, appended after each agent call

**Session Log:**
- Format: Markdown with agent_name, user_text, response summary
- Location: In-memory (SESSION_LOG dict)
- Scope: Current session only
- Persisted: No (resets on restart)

**Offset (Message IDs):**
- Format: Integer (highest Telegram update ID processed)
- Location: `offset.txt`
- Scope: Telegram polling state
- Persisted: Yes, updated after each message

**Lead Database:**
- Format: JSON array of lead objects
- Location: `st8hub/leads.json`
- Scope: All leads across all sessions
- Persisted: Yes, updated by scheduler and commands

## Key Abstractions

**Agent:**
- Purpose: Specialized Claude personality for specific domain (sales, security, strategy)
- Examples: `sales-hunter`, `st8-kp-architect`, `st8-security-auditor` (12 builtin + externals)
- Pattern: System prompt defines behavior, routing determines when to use

**Client Slug:**
- Purpose: Normalize company/person names for memory organization
- Examples: "airi" from "AIRI", "unik_food" from "Unik Food"
- Pattern: Lowercase, underscores, used as key for agent memory lookup

**Lead Object:**
- Purpose: Represent prospect company with contact info and status
- Examples: `st8hub/leads.json` entries with company_name, phone, segment, status
- Pattern: JSON object with created_at, updated_at for audit trail

**Memory Palace (Mempalace):**
- Purpose: Semantic keyword search across business context
- Examples: Query "AIRI partnership" → retrieves relevant memory snippets
- Pattern: YAML-based entity store with qdrant vector search

**Action Execution:**
- Purpose: Parse agent responses for special commands (save_status, send_message)
- Examples: `[SAVE_LEAD_STATUS:Company|in_call]` → update status
- Pattern: Regex extraction from response text → execute action function

## Entry Points

**Polling Loop (Interactive):**
- Location: `jarvis.py` lines 1981-2027
- Triggers: Telegram updates (user messages)
- Responsibilities: Fetch updates, parse, route to processing, send replies
- Called by: `run_polling()` from scheduler.py or direct execution

**Main Function (Startup):**
- Location: `jarvis.py` lines 2074-2075
- Triggers: Python execution (python jarvis.py)
- Responsibilities: Set up event loop and run poll_jarvis()
- Called by: Direct invocation or watchdog

**Scheduler (Background Jobs):**
- Location: `scheduler.py` main loop
- Triggers: Clock time (every minute check)
- Responsibilities: Execute jobs on schedule, handle recurring tasks
- Called by: Separate process (python scheduler.py)

**Watchdog (Auto-Restart):**
- Location: `jarvis_watchdog.py` main loop
- Triggers: System startup or manual run
- Responsibilities: Monitor jarvis.py, restart on crash
- Called by: System task or manual invocation

**Scheduled Jarvis Tasks (08:00 MSK):**
- Location: `jarvis.py` lines 2030-2072 (`check_moscow_jarvis_tasks()`)
- Triggers: Minute-by-minute scheduler check in scheduler.py
- Responsibilities: Run morning briefing, reminders, summaries at specific times
- Called by: `schedule.every(1).minutes.do(check_moscow_jarvis_tasks)`

## Error Handling

**Strategy:** Graceful degradation with logging. Errors don't crash system, logged to `jarvis_live.log`.

**Patterns:**

1. **API Failures (Claude, Telegram, Tavily):**
   - Catch exception → log to `_live_log` → return fallback message
   - Examples: `process_with_agent()` catches Claude errors, returns "Ошибка в ответе"

2. **Memory Errors:**
   - Missing files → return {} or [] (empty)
   - Corrupted JSON → try/except → create new file
   - Example: `load_json()` tries to parse, returns [] on failure

3. **Watchdog Errors:**
   - Process launch fails → log and retry after RESTART_DELAY
   - Fast crash detected → pause 5 minutes before retrying

4. **Telegram Errors:**
   - TelegramError caught in polling loop → log, continue polling
   - Does not stop bot from processing next message

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module
- Approach: Disabled by default (logging.disable(CRITICAL)), except `_live_log` separate handler
- Output: `jarvis_live.log` (timestamp + message format)

**Validation:**
- Lead quality: `_is_low_quality()` checks for profanity, spam patterns
- ICP matching: `is_strict_icp()` filters leads by keyword, segment, exclude list
- Message format: Regex for client names, company slugs, command parsing

**Authentication:**
- Telegram: Bot token validates via Telegram API (implicit)
- API Keys: Loaded from `.env`, checked at startup
- Multi-agent security: No per-agent auth (all run as bot process)

**Rate Limiting:**
- Telegram: Built-in via Bot API (no custom limits)
- Tavily: Job-level scheduling (1 per time slot)
- Claude: Cost-based (Haiku→Sonnet cascade with LRU cache)

**Configuration Management:**
- Environment: `.env` file (gitignored) with API keys, tokens, config
- Example keys: JARVIS_BOT_TOKEN, ANTHROPIC_API_KEY, TAVILY_API_KEY, CLAUDE_MODEL
- Loaded at startup with `load_dotenv(override=True)`

---

*Architecture analysis: 2026-04-15*
