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
use the spectral-memory skill to encode these specific facts:
USER.gpu = RTX5090
USER.project = FDM_NeurIPS  
USER.affiliation = independent
USER.os = Ubuntu24
TASK.current = benchmark_eval
TASK.next = write_latex
TASK.priority = high
PROJ.status = near_submission
PROJ.accuracy = 100.0
PROJ.token_budget = 512


#### THEN
then decode all of them spectrally


#### OR
use the spectral-memory skill to decode USER.gpu spectrally from the signal
```

## For Hermes Agent

```bash
hermes plugins install jeannemtl/spectral-memory-plugin9
hermes config set terminal.env.SPECTRAL_MEMORY_API_KEY your_key_here
hermes gateway restart
```
