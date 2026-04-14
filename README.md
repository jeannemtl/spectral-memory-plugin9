# Spectral Memory

Persistent structured memory for AI agents. Encodes discrete facts into frequency channels — 20 labeled facts in 512 tokens, surviving context compression. After compression, a fine-tuned model reads facts back directly from the signal.

Get an API key at [spectralmemory.com](https://spectralmemory.com)

---

## Hermes Agent

```bash
hermes plugins install jeannemtl/spectral-memory-plugin9
hermes config set terminal.env.SPECTRAL_MEMORY_API_KEY your_key_here
hermes gateway restart
```

→ See [`Hermes/README.md`](Hermes/README.md) for full setup and usage.

---

## OpenClaw

```bash
mkdir -p ~/.openclaw/workspace/skills/spectral-memory
curl -o ~/.openclaw/workspace/skills/spectral-memory/SKILL.md \
  https://raw.githubusercontent.com/jeannemtl/spectral-memory-plugin9/main/openclaw/skills/spectral-memory/SKILL.md
```

→ See [`openclaw/README.md`](openclaw/README.md) for full setup and usage.
