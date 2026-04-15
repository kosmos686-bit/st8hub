# Technology Stack

**Analysis Date:** 2026-04-15

## Languages

**Primary:**
- Python 3.11.9 - Main application (Telegram bot, scheduler, ML workflows)

## Runtime

**Environment:**
- Python 3.11.9 (from `.venv/` virtual environment)

**Package Manager:**
- pip (via virtualenv at `/c/st8-workspace/.venv/`)
- Lockfile: Not detected (uses installed packages only)

## Frameworks

**Core Bot:**
- python-telegram-bot 22.7 - Telegram Bot API polling and webhook handling
- schedule 1.2.2 - Job scheduling and periodic tasks

**AI/ML:**
- anthropic 0.76.0 - Claude API integration (Haiku, Sonnet models)
- tavily-python 0.7.23 - Web search and information retrieval

**Memory & Embeddings:**
- mem0ai 1.0.11 - Long-term memory system using Anthropic + Qdrant
- qdrant-client 1.17.1 - Vector database for semantic search (embedded in mem0)
- chromadb 1.5.7 - Persistent vector storage for mempalace semantic search
- huggingface embeddings (lazy-loaded via mem0) - multi-qa-MiniLM-L6-cos-v1

**Data Processing:**
- pandas 3.0.2 - Data manipulation and analysis
- numpy 2.4.4 - Numerical computing (used by pandas/chromadb)

**Build/Dev:**
- streamlit 1.56.0 - Web UI framework (used in st8-voice-reanimator)
- python-docx 1.2.0 - Word document processing
- reportlab 4.0+ - PDF generation (optional, in ai-marketing-claude)

**Audio/Voice:**
- livekit 1.1.3 - Real-time communication platform
- livekit-agents 1.5.1 - Agent framework for audio processing
- livekit-plugins-openai 1.5.1 - OpenAI integration for voice (whisper)
- livekit-plugins-cartesia 1.5.1 - Cartesia voice synthesis

## Key Dependencies

**Critical:**
- python-dotenv 1.2.1 - Environment variable management (required for all API keys)
- requests 2.32.5 - HTTP client for API calls and web requests
- aiohttp 3.13.3 - Async HTTP client for concurrent API requests
- pytz 2026.1.post1 - Timezone handling (Moscow UTC+3 scheduling)

**Utilities:**
- python-dateutil 2.9.0 - Date/time utilities
- urllib3 2.6.3 - HTTP pooling (transitive via requests)
- gitpython 3.1.46 - Git operations (pushing leads to st8hub)
- google-api-python-client 2.188.0 - Google APIs (optional integration)

**File Processing:**
- fitz (PyMuPDF) - PDF text extraction from Telegram documents
- python-docx 1.2.0 - Word document parsing

## Configuration

**Environment:**
- Location: `.env` file in project root (see `load_dotenv()` calls in `jarvis.py`, `scheduler.py`)
- Critical vars required:
  - `JARVIS_BOT_TOKEN` - Telegram bot token
  - `ANTHROPIC_API_KEY` - Claude API key
  - `TAVILY_API_KEY` - Web search API key
  - `BOT_TOKEN` - Scheduler polling token (duplicate?)
  - `JARVIS_CHAT_ID` - Chat ID for polling
  - `YULIA_CHAT_ID` - Default recipient for Yulia messages
  - `GMAIL_USERNAME` / `GMAIL_PASSWORD` - Email (optional)
  - `GITHUB_TOKEN` - GitHub API access for st8hub
  - `DGIS_API_KEY` - 2GIS API for contact lookup

**Build:**
- No build config files detected (pure Python application)
- Windows-specific mutex handling via `ctypes.windll` (see `jarvis_watchdog.py`, `scheduler.py`)

## Platform Requirements

**Development:**
- Windows 11 (uses Windows API for mutexes)
- Python 3.11.9
- Virtual environment (`.venv`)
- Telegram desktop app or account for testing

**Production:**
- Deployment target: Windows machine (uses Windows kernel mutexes)
- Expects Telegram bot token from BotFather
- Requires internet connectivity (Telegram, Anthropic, Tavily, 2GIS APIs)
- Local storage: `.env`, `jarvis_memory.json`, `jarvis_offset.json`, `mem0_db/`, `st8hub/` repo

## Storage Layers

**Runtime Memory:**
- In-process: Session tracking, conversation history (kept in memory during polling)
- File-based: `jarvis_memory.json` (message history), `jarvis_offset.json` (Telegram update offset)

**Persistent Memory:**
- Vector DB: `mem0_db/` (Qdrant via mem0, Anthropic + HF embeddings)
- Semantic Search: `~/.mempalace/palace/` (ChromaDB persistent directory for mempalace integration)
- JSON Files: `st8hub/leads.json` (leads database, synced to GitHub)

**Per-Client Memory:**
- Location: `AGENT_MEMORY_DIR/` (agent memory per client slug)
- Format: JSON files with agent interactions

---

*Stack analysis: 2026-04-15*
