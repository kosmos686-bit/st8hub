---
phase: 01-smart-routing-core
plan: "02"
subsystem: model-routing
tags: [routing, cost-optimization, haiku, sonnet, decorator, process_with_agent]
dependency_graph:
  requires: [_pick_model, smart_route, ROUTING_env_vars]
  provides: [smart_route_active_on_process_with_agent]
  affects: [jarvis.py]
tech_stack:
  added: []
  patterns: [post-definition-wrapping, proactive-model-selection]
key_files:
  created: []
  modified:
    - jarvis.py
decisions:
  - "Post-definition wrapping (process_with_agent = smart_route(process_with_agent)) used instead of @decorator syntax to avoid NameError from forward reference"
  - "Inserted single line after # end Smart Route comment at line 911 — no other modifications"
metrics:
  duration_minutes: 15
  completed_date: "2026-04-15T08:35:00Z"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 1
---

# Phase 01 Plan 02: Smart Routing Core — Wire smart_route onto process_with_agent Summary

One-liner: Single-line post-definition wrapping wires smart_route onto process_with_agent, making Haiku/Sonnet/fallback routing live for every interactive Telegram message.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Apply smart_route wrapper to process_with_agent | 37133ecb | jarvis.py |
| 2 | Verify routing logic with AST and structure checks | 37133ecb | jarvis.py (read-only) |
| 3 | Manual verification — bot starts and routes correctly | human-approved | jarvis_live.log |

## What Was Built

### jarvis.py — line 911

One line inserted after `# ── end Smart Route ──` comment:

```python
process_with_agent = smart_route(process_with_agent)
```

This is the complete change. It is placed after `def smart_route(func)` (line 882) which was inserted by Plan 01, and before the global variable section that begins at line 915. The post-definition wrapping pattern avoids a forward-reference `NameError` that would occur if `@smart_route` were placed at the `def process_with_agent` line (line 621, which precedes smart_route's definition by ~260 lines).

### Routing paths now active

Every call to `process_with_agent(user_text, history, claude_client, CLAUDE_MODEL)` at line 2043 now passes through the `smart_route` wrapper, which:

1. Calls `_pick_model(user_text)` to determine the model
2. If Haiku: replaces the `model` positional arg (args[2]) with `claude-haiku-4-5-20251001`
3. If Sonnet: replaces with `claude-sonnet-4-6`
4. If None (ambiguous): leaves the original `CLAUDE_MODEL` unchanged (falls through to Sonnet as default)

## Verification Results

```
python -m py_compile jarvis.py             -> SYNTAX_OK
AST parse                                  -> all 5 routing functions found
process_with_agent wrapping confirmed      -> PASS
smart_route defined before wrapping line   -> PASS
_pick_model('hello')                       -> claude-haiku-4-5-20251001   PASS
_pick_model('```python...```')             -> claude-sonnet-4-6            PASS
_pick_model('a ' * 1500)                  -> claude-sonnet-4-6            PASS
_pick_model(104-token medium message)      -> None (fallback)              PASS
No file deletions in commit                -> OK
```

Note: The plan's test example `'Tell me about the project status and the next steps we should take'` (67 chars ~16 tokens) routes to Haiku because it is below the 100-token threshold — this is correct behavior. The ambiguous/None path was confirmed with a properly-sized message (104 tokens, no complexity signals).

## Deviations from Plan

None — plan executed exactly as written. Single line inserted, syntax verified, AST verified, functional tests passed.

## Known Stubs

None — `process_with_agent` is fully wired. All three routing paths are functional. The bot will route messages proactively on next start.

## Manual Verification (Task 3 — Checkpoint) — APPROVED

Human verification completed and approved. All three routing paths confirmed working in production:

| Path | Log entry | Status |
|------|-----------|--------|
| Short message | `smart_route decision=haiku` | VERIFIED |
| Complex/code message | `smart_route decision=sonnet` | VERIFIED |
| Medium/ambiguous message | `smart_route decision=fallback` | VERIFIED |

Bot started without errors. All acceptance criteria met. Approved signal: "approved".

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. The single inserted line calls only already-existing functions from Plan 01. No new threat surface.

## Self-Check: PASSED

- `jarvis.py` contains `process_with_agent = smart_route(process_with_agent)` at line 911: FOUND
- Commit 37133ecb exists in git log: FOUND
- `python -m py_compile jarvis.py`: SYNTAX_OK
- AST verification: ALL_CHECKS_PASS
- Functional routing tests: PASSED (all 4 paths)
