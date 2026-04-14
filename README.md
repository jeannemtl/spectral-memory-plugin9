# Spectral Memory — OpenClaw Skill

Encode facts into frequency channels. Survive context compression. Decode by model inference.

## Install

```bash
mkdir -p ~/.openclaw/skills/spectral-memory
curl -o ~/.openclaw/skills/spectral-memory/SKILL.md \
  https://raw.githubusercontent.com/jeannemtl/spectral-memory-plugin9/main/SKILL.md
```

Then add to `~/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "spectral-memory": {
        "env": {
          "SPECTRAL_MEMORY_API_KEY": "your_key_here",
          "SPECTRAL_MEMORY_USER_ID": "your_user_id"
        }
      }
    }
  }
}
```

Restart: `openclaw gateway restart`

Get a key at [spectralmemory.com](https://spectralmemory.com)

## Usage

```
use spectral-memory to encode my GPU as RTX5090
use spectral-memory to decode my GPU from the signal
```

## For Hermes Agent

```bash
hermes plugins install jeannemtl/spectral-memory-plugin9
hermes config set terminal.env.SPECTRAL_MEMORY_API_KEY your_key_here
hermes gateway restart
```
