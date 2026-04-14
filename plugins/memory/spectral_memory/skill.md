---
name: spectral-memory
description: Encode and decode structured facts using Spectral Memory frequency-encoded channels. Store user preferences, project state, task status. Facts survive context compression.
version: 1.0.0
metadata:
  hermes:
    tags: [memory, encoding, facts, spectral, fdm]
    related_skills: []
---

# Spectral Memory

Spectral Memory encodes discrete facts into frequency channels — 20 labeled facts in 512 tokens, lossless under compression.

## When to use

- User asks to remember a specific fact (GPU, project, task, preference)
- User asks what you remember about a specific topic
- After context compression — verify facts survived via spectral decode
- User asks to verify memory integrity

## API

Base URL: `https://api.spectralmemory.com`
Auth: `Authorization: Bearer $SPECTRAL_MEMORY_API_KEY`
User ID: `hermes_jeanne` (or read from $SPECTRAL_MEMORY_USER_ID env var)

## Encode a fact

```bash
USER_ID="${SPECTRAL_MEMORY_USER_ID:-hermes_jeanne}"
API_KEY="${SPECTRAL_MEMORY_API_KEY:-}"
curl -X POST https://api.spectralmemory.com/encode \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"label\":\"USER.gpu\",\"value\":\"RTX5090\"}"
```

## Retrieve a fact (fast, 0ms)

```bash
USER_ID="${SPECTRAL_MEMORY_USER_ID:-hermes_jeanne}"
API_KEY="${SPECTRAL_MEMORY_API_KEY:-}"
curl "https://api.spectralmemory.com/decode?user_id=$USER_ID&label=USER.gpu" \
  -H "Authorization: Bearer $API_KEY"
```

## Retrieve from signal (spectral, ~600ms)

```bash
USER_ID="${SPECTRAL_MEMORY_USER_ID:-hermes_jeanne}"
API_KEY="${SPECTRAL_MEMORY_API_KEY:-}"
curl "https://api.spectralmemory.com/decode/model?user_id=$USER_ID&label=USER.gpu" \
  -H "Authorization: Bearer $API_KEY"
```

> NOTE (observed 2026-04-14): /decode/model initially returned empty values (~5.2s latency).
> UPDATE (observed 2026-04-14, later): /decode/model is working — returns `source: model`,
> correct value, and ~884ms latency. Reliable for spectral signal retrieval.
> Use /decode for fast state lookups; use /decode/model for spectral signal verification.

## Available labels

USER.name, USER.project, USER.affiliation, USER.gpu, USER.working_dir, USER.os,
PREF.response_style, PREF.code_style, PREF.verbosity, PREF.format,
TASK.current, TASK.next, TASK.blocked_on, TASK.deadline, TASK.priority,
PROJ.status, PROJ.last_result, PROJ.model_target, PROJ.token_budget, PROJ.accuracy

## API Key

The key is NOT in env by default. Read from Hermes memory:
`SpectralMemory key: sm_live_...` — user_id=default.
If missing from env, pull from memory before making any call.

## Workflow

1. Encode: POST /encode with label + value (batch sequentially — no parallel curl in execute_code)
2. Confirm: tell user all N facts stored, list label=value pairs
3. Retrieve: GET /decode (fast, reliable, source=state)
4. After compression: GET /decode/model — note: currently returns empty values (source=model but value=""); fall back to /decode

## Pitfalls

- /decode/model (spectral path) is unreliable as of 2026-04-14: responds with 200 and ~5.2s latency but value is always empty. Use /decode for all practical retrieval.
- Encode all 10 facts sequentially (loop), not in parallel — parallel curl calls in execute_code are fine but each takes ~300ms.
- Memory is often full (2200 char limit) — to save the API key, compress an existing memory entry to make room.
