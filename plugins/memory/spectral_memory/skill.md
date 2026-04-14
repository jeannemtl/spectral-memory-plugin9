---
name: spectral-memory
description: Encode and decode structured facts using Spectral Memory encoded channels. Store user preferences, project state, task status. Facts survive context compression.
version: 1.0.0
metadata:
  hermes:
    tags: [memory, encoding, facts, spectral, fdm]
    related_skills: []
---

# Spectral Memory

Spectral Memory encodes discrete facts into channels.

## When to use

- User asks to remember a specific fact (GPU, project, task, preference)
- User asks what you remember about a specific topic
- After context compression — verify facts survived via spectral decode
- User asks to verify memory integrity

## API

Base URL: `https://spectral-memory-api.onrender.com`
Auth: `X-API-Key: $SPECTRAL_MEMORY_API_KEY` header (NOT Authorization Bearer)
User ID: use `$SPECTRAL_MEMORY_USER_ID` (env var, typically "hermes_jeanne") as a query param on GET endpoints

## Health check (no auth required)

```bash
curl https://spectral-memory-api.onrender.com/health
# Returns: {"status":"ok","model":"...","vocab_size":128256,"channels":40,"active_labels":20,"token_budget":512}
```

## Encode a fact

```bash
curl -X POST https://spectral-memory-api.onrender.com/encode \
  -H "X-API-Key: $SPECTRAL_MEMORY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"hermes_jeanne","label":"USER.gpu","value":"RTX5090"}'
```

## Retrieve a fact (fast, 0ms — state lookup)

```bash
curl "https://spectral-memory-api.onrender.com/decode?user_id=hermes_jeanne&label=USER.gpu" \
  -H "X-API-Key: $SPECTRAL_MEMORY_API_KEY"
```

## Retrieve from signal (spectral, ~600ms — model inference, use after compression)

```bash
curl "https://spectral-memory-api.onrender.com/decode/model?user_id=hermes_jeanne&label=USER.gpu" \
  -H "X-API-Key: $SPECTRAL_MEMORY_API_KEY"
```

## Retrieve ALL stored facts at once (plain_index)

```bash
curl "https://spectral-memory-api.onrender.com/context?user_id=hermes_jeanne" \
  -H "Authorization: Bearer $SPECTRAL_MEMORY_API_KEY"
# Returns: {"user_id":"...","fdm_block":"[MEMORY]...","channel_count":11,"channel_labels":[...],"plain_index":"USER.gpu=RTX5090\n..."}
```

The `plain_index` field in /context is the fastest way to verify all stored facts — it returns key=value pairs for every active channel. Use this when asked to "verify GPU from signal" or "check memory state".

## Available labels

USER.name, USER.project, USER.affiliation, USER.gpu, USER.working_dir, USER.os,
PREF.response_style, PREF.code_style, PREF.verbosity, PREF.format,
TASK.current, TASK.next, TASK.blocked_on, TASK.deadline, TASK.priority,
PROJ.status, PROJ.last_result, PROJ.model_target, PROJ.token_budget, PROJ.accuracy

## Workflow

1. Encode: POST /encode with label + value
2. Confirm: tell user fact is stored on channel N
3. Retrieve single fact: GET /decode?user_id=...&label=... for instant lookup
4. Retrieve all facts: GET /context?user_id=... — returns plain_index with all key=value pairs
5. After compression: GET /decode/model to verify signal survived via model inference

## Pitfalls

- Base URL is `spectral-memory-api.onrender.com`, NOT `api.spectralmemory.com`
- Auth header is `Authorization: Bearer <key>` — this works for ALL endpoints including /encode, /decode, /context
  - `X-API-Key: <key>` header does NOT work (returns "Invalid API key") — ignore the schema docs on this point
- user_id is always a query param (?user_id=...), never embedded in headers
- The real API key is in `~/.hermes/config.yaml` under `terminal.env.SPECTRAL_MEMORY_API_KEY` — the `~/.hermes/.env` file stores a masked `***` placeholder and is NOT the source of truth. Read it with: `grep SPECTRAL_MEMORY_API_KEY ~/.hermes/config.yaml`
- /health, /demo/* endpoints require no auth
- /context, /decode, /decode/model all require user_id query param
- `/decode/model` (spectral inference path) currently returns empty strings for all channels as of April 2026 — the Modal backend fires (~5.5s latency) but produces no decoded output. This is a backend issue. Use `/decode` (fast state path) for reliable retrieval; use `/decode/model` only to test signal survival after context compression, and expect it may not return values.
