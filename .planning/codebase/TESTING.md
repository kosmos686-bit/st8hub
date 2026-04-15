# Testing Patterns

**Analysis Date:** 2026-04-15

## Test Framework

**Runner:**
- No formal test framework detected (no pytest, unittest, or vitest)
- Test files use direct Python execution

**Test Files Found:**
- `test_search.py` — Manual testing of lead search functionality
- `test_search_now.py` — Integration test for lead discovery and git push

**Run Commands:**
```bash
python test_search.py              # Search leads and send to Telegram
python test_search_now.py          # Search leads, save to JSON, git push, notify
```

**Assertion Library:**
- None used; tests rely on print output and manual verification

## Test File Organization

**Location:**
- Test files at root level: `/c/st8-workspace/test_*.py`
- Not co-located with source modules

**Naming:**
- Convention: `test_*.py` for test files
- Module-specific: `test_search.py` tests `scheduler.search_leads()` and `send_leads()`

**Structure:**
- Direct script execution, no test class structure
- Linear execution with print statements for output verification
- Manual inspection of results (no assertions)

## Test Structure

**Pattern in test_search.py:**
```python
import asyncio
from scheduler import search_leads, send_leads

# Test execution
leads = search_leads("horeca", 3)
print(f"Найдено лидов: {len(leads)}")
for lead in leads:
    print(f"Компания: {lead['company_name']}, ЛПР: {lead['lpr']}, Сегмент: {lead['segment']}")

# Integration step
send_leads(leads)
print("Лиды отправлены в Telegram!")
```

**Pattern in test_search_now.py:**
```python
def main():
    # 1. Search leads
    leads = search_leads("horeca", 3)
    
    # 2. Save to file
    with open(leads_file, 'w', encoding='utf-8') as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)
    
    # 3. Git operations
    subprocess.run(['git', 'add', '.'], ...)
    subprocess.run(['git', 'commit', ...], ...)
    subprocess.run(['git', 'push'], ...)
    
    # 4. Notify
    send_text_notification(notification)
    
    # 5. Verify
    print output
```

## Mocking

**Framework:** None detected

**Patterns:**
- No explicit mocking
- Tests use real API calls to Tavily, Claude, Telegram
- Dependencies are real external services

**Test Data:**
- Hardcoded category: `search_leads("horeca", 3)` — always searches HoReCa segment
- Hardcoded lead count: `num_leads=3` for quick testing

## Fixtures and Factories

**Test Data (observed in test files):**
- No fixture files
- Hardcoded search queries in `search_leads()` function (not in test)
- Test data comes from live API responses

**JSON Structure (example from leads):**
```python
{
    "company_name": "Company Name",
    "lpr": "Director Name",
    "segment": "horeca",
    "phone": "phone or null",
    "email": "email or null",
    "pain": "pain description",
    "status": "new/negotiating/meeting_set",
    "source": "telegram/call/recommendation",
    "date": "ISO datetime",
    "updated_at": "ISO datetime"
}
```

## Coverage

**Requirements:** None enforced

**Type:** Integration testing only
- No unit test coverage defined
- No code coverage metrics tracked
- Tests verify end-to-end functionality (search → save → push → notify)

## Test Types

**Unit Tests:**
- Not present
- Would target: `load_json()`, `extract_lead_data()`, validation functions
- Currently: No isolated unit tests

**Integration Tests:**
- `test_search_now.py` — Full pipeline:
  1. Search Tavily API for leads
  2. Parse and validate company data
  3. Save to `st8hub/leads.json`
  4. Git commit and push
  5. Send Telegram notification
  6. Print results for manual verification

**E2E Tests:**
- Implicit in scheduler execution
- `scheduler.py` has scheduled tasks that trigger daily:
  - `make_good_morning()` — Morning briefing with weather, priorities, leads
  - `make_no_response_reminder()` — Follow-up for unresponsive leads
  - `make_day_summary()` — End-of-day report
  - Lead search and distribution

**Manual Testing:**
- Primary testing approach
- Visual inspection of print output
- Telegram message verification (read in chat)
- JSON file inspection for data integrity

## Common Patterns

**Async Testing:**
- Minimal async; only Telegram bot uses async via `asyncio.run()`
- Test does not explicitly test async behavior

**Error Scenarios (not tested but present in code):**
- API timeout: Handled with 5-second timeout in urllib
- JSON parse failure: Fallback to empty list or None
- Missing file: Returns empty list
- Missing env var: Raises RuntimeError at startup

**Retry Logic (implicit in tests):**
- Anthropic API 529 overload: 10-15 second backoff, max 3 attempts
- No explicit retry in test files, but scheduler handles it

## Logging in Tests

**Output:**
- Print statements only: `print(f"[+] Found {len(leads)} leads")`
- No structured logging
- No log file verification

**Example logging pattern in tests:**
```python
print("[*] Starting test search...")
print(f"[+] Found {len(leads)} leads")
print(f"[-] Error: {e}")
print(f"[+] Saved to {leads_file}")
```

**Pattern prefix:**
- `[*]` — Informational step
- `[+]` — Success
- `[-]` — Error or skip

## Test Isolation

**State Management:**
- Tests modify live files (`st8hub/leads.json`)
- No teardown/cleanup
- No test database isolation
- Side effects: Git commits are real

**Concerns:**
- Tests run against production data
- Git history modified by tests
- No test environment separation

## Configuration for Testing

**Environment Variables Used:**
- `ANTHROPIC_API_KEY` — Required for Claude API
- `TAVILY_API_KEY` — Required for lead search
- `JARVIS_BOT_TOKEN` — Required for Telegram notifications
- `GITHUB_TOKEN` — Required for git operations

**Test Isolation:**
- No test-specific config
- .env file shared with production

## Debugging Aids

**Available in test files:**
- Print statements for step tracking
- Exception messages printed with context
- Try/except blocks capture and display errors
- Lead data pretty-printed for visual inspection

**Example (test_search_now.py):**
```python
print("\n=== FOUND LEADS ===")
for i, lead in enumerate(leads, 1):
    print(f"\n{i}. {lead['company_name']}")
    print(f"   LPR: {lead['lpr']}")
    print(f"   Email: {lead['email'] or 'not found'}")
    print(f"   Phone: {lead['phone'] or 'not found'}")
    print(f"   Segment: {lead['segment']}")
```

## Continuous Testing

**Implicit CI (observed):**
- Scheduler runs continuously in background
- Daily tasks trigger automatically at set times
- No webhook-based testing
- Git commits from test files push to `st8hub` repository

## Known Testing Gaps

**Untested Areas:**
- API error handling: No tests for network failures, timeouts, rate limiting
- Data validation: No tests for malformed JSON, invalid company names
- Claude model fallback logic: `ST8ModelRouter` cascade (Haiku→Sonnet) not explicitly tested
- Agent routing: No tests for keyword detection and agent selection
- Memory operations: No tests for JSON load/save corruption scenarios
- Telegram delivery: No tests for message parsing or markdown formatting

**Test Coverage Priority:**
- HIGH: `extract_lead_data()` JSON parsing (currently relies on Claude + regex fallback)
- HIGH: `search_leads()` filtering logic (many conditions, easy to break)
- MEDIUM: Agent keyword matching logic
- MEDIUM: File I/O with missing/corrupt files
- LOW: Weather API parsing (external service, not critical)

## Test Execution Strategy

**Current Approach:**
- Manual execution: `python test_search.py`
- Real API calls: No mocking, live Tavily/Claude/Telegram
- Output inspection: Read stdout and check results

**Recommended Approach:**
- Add pytest with mocking for unit tests
- Mock external APIs (Tavily, Claude, Telegram)
- Create test fixtures for common data patterns
- Add integration tests with test-specific Telegram channel
- Track API costs in test output

---

*Testing analysis: 2026-04-15*
