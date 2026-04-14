---
name: spectral-memory
description: Encode and decode structured facts using Spectral Memory frequency channels. Facts survive context compression — retrieval is model inference from the signal.
metadata: {"openclaw": {"primaryEnv": "SPECTRAL_MEMORY_API_KEY", "requires": {"env": ["SPECTRAL_MEMORY_API_KEY"]}}}
---

# Spectral Memory

Encodes discrete facts into frequency channels — 20 labeled facts in 512 tokens, lossless under compression. After compression, a fine-tuned model reads facts back directly from the signal.

## API

Base URL: `https://api.spectralmemory.com`
Auth: `Authorization: Bearer $SPECTRAL_MEMORY_API_KEY`
User ID: `${SPECTRAL_MEMORY_USER_ID:-default}`

## Encode a fact

```bash
USER_ID="${SPECTRAL_MEMORY_USER_ID:-default}"
API_KEY="${SPECTRAL_MEMORY_API_KEY:-}"
curl -s -X POST https://api.spectralmemory.com/encode \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"label\":\"USER.gpu\",\"value\":\"RTX5090\"}"
```

## Retrieve a fact — fast path (0ms)

```bash
USER_ID="${SPECTRAL_MEMORY_USER_ID:-default}"
API_KEY="${SPECTRAL_MEMORY_API_KEY:-}"
curl -s "https://api.spectralmemory.com/decode?user_id=$USER_ID&label=USER.gpu" \
  -H "Authorization: Bearer $API_KEY"
```

## Retrieve from signal — spectral path (~600ms, use after compression)

```bash
USER_ID="${SPECTRAL_MEMORY_USER_ID:-default}"
API_KEY="${SPECTRAL_MEMORY_API_KEY:-}"
curl -s "https://api.spectralmemory.com/decode/model?user_id=$USER_ID&label=USER.gpu" \
  -H "Authorization: Bearer $API_KEY"
```

## Available labels

USER.name, USER.project, USER.affiliation, USER.gpu, USER.working_dir, USER.os,
PREF.response_style, PREF.code_style, PREF.verbosity, PREF.format,
TASK.current, TASK.next, TASK.blocked_on, TASK.deadline, TASK.priority,
PROJ.status, PROJ.last_result, PROJ.model_target, PROJ.token_budget, PROJ.accuracy

## Workflow

1. Encode facts with label + value
2. Fast decode for instant lookup
3. After context compression — spectral decode to verify facts survived
