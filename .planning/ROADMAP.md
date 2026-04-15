# Roadmap: Jarvis ST8-AI

## Overview

Milestone v1.0 adds proactive model selection on top of the existing reactive ST8ModelRouter.
Phase 1 delivers the @smart_route decorator and configurable routing rules so every request
picks the right model before hitting the API. Phase 2 layers per-call token metrics and a
/stats command so cost savings are observable and measurable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Smart Routing Core** - @smart_route decorator and ROUTING_RULES config wired into jarvis.py (completed 2026-04-15)
- [ ] **Phase 2: Token Metrics** - Per-call cost logging and /stats Telegram command

## Phase Details

### Phase 1: Smart Routing Core
**Goal**: Every Claude API call in jarvis.py has a model selected proactively based on request complexity before the API is called, with rules configurable in .env
**Depends on**: Nothing (first phase)
**Requirements**: ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04, ROUTE-05
**Success Criteria** (what must be TRUE):
  1. A short conversational message (< 100 tokens, no code/analysis) is routed to Haiku without ever touching ST8ModelRouter's cascade
  2. A message containing code blocks or exceeding 500 tokens is routed directly to Sonnet
  3. An ambiguous message (medium length, no clear complexity signal) falls through to the existing ST8ModelRouter quality cascade unchanged
  4. Changing ROUTING_RULES_HAIKU_MAX_TOKENS and ROUTING_RULES_SONNET_KEYWORDS in .env alters routing behavior without any code change
  5. jarvis.py passes a syntax check (python -m py_compile jarvis.py) and the bot starts cleanly after changes
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01-PLAN.md -- Routing config (.env) and _pick_model + smart_route functions in jarvis.py
- [x] 01-02-PLAN.md -- Wire smart_route onto process_with_agent and verify all routing paths

**UI hint**: no

### Phase 2: Token Metrics
**Goal**: Every model call writes token counts and cost to jarvis_live.log, and the founder can ask /stats in Telegram to see today's spend
**Depends on**: Phase 1
**Requirements**: METRIC-01, METRIC-02
**Success Criteria** (what must be TRUE):
  1. After any message that triggers a Claude API call, jarvis_live.log contains a line with model name, input tokens, output tokens, and estimated cost in USD
  2. Sending /stats to the Telegram bot returns a summary showing total calls, total tokens (input + output), and total cost for the current calendar day (MSK timezone)
  3. The /stats response correctly groups costs by model (Haiku vs Sonnet) so the routing savings are visible
**Plans:** 2 plans

Plans:
- [ ] 02-01-PLAN.md -- _log_token_usage helper and hook all client.messages.create call sites
- [ ] 02-02-PLAN.md -- /stats command: log parser, aggregator, Telegram handler

**UI hint**: no

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Smart Routing Core | 2/2 | Complete   | 2026-04-15 |
| 2. Token Metrics | 0/2 | Not started | - |
