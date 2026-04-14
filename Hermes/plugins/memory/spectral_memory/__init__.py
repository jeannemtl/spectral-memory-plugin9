from __future__ import annotations
import json
import logging
import os
import threading
import httpx
from typing import Any, Dict, List
from agent.memory_provider import MemoryProvider
from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

def _tool_error(msg: str) -> str:
    return json.dumps({"error": msg})

ENCODE_SCHEMA = {
    "name": "fdm_encode",
    "description": (
        "Store a structured fact into Spectral Memory. "
        "Use for discrete, stable, labeled facts: user preferences, "
        "project state, task status, environment facts."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "label": {
                "type": "string",
                "description": "Channel label e.g. USER.gpu, TASK.current, PROJ.accuracy",
                "enum": [
                    "USER.name", "USER.project", "USER.affiliation",
                    "USER.gpu", "USER.working_dir", "USER.os",
                    "PREF.response_style", "PREF.code_style",
                    "PREF.verbosity", "PREF.format",
                    "TASK.current", "TASK.next", "TASK.blocked_on",
                    "TASK.deadline", "TASK.priority",
                    "PROJ.status", "PROJ.last_result", "PROJ.model_target",
                    "PROJ.token_budget", "PROJ.accuracy",
                ]
            },
            "value": {"type": "string", "description": "The value to store"},
        },
        "required": ["label", "value"],
    },
}

DECODE_SCHEMA = {
    "name": "fdm_decode",
    "description": (
        "Retrieve a structured fact from Spectral Memory by channel label. "
        "Fast path — reads from persistent state in 0ms. "
        "Use this for routine fact retrieval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "label": {"type": "string", "description": "Channel label to retrieve"},
        },
        "required": ["label"],
    },
}

DECODE_SPECTRAL_SCHEMA = {
    "name": "fdm_decode_spectral",
    "description": (
        "Retrieve a structured fact by reading the FDM signal directly via model inference (~600ms). "
        "Use after context compression to verify facts survived, or when state may have been lost. "
        "Slower than fdm_decode but reads spectrally from the encoded signal."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "label": {"type": "string", "description": "Channel label to retrieve spectrally"},
        },
        "required": ["label"],
    },
}

def _load_config() -> dict:
    from pathlib import Path
    profile_path = get_hermes_home() / "spectral_memory" / "config.json"
    if profile_path.exists():
        try:
            return json.loads(profile_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "api_key": os.environ.get("SPECTRAL_MEMORY_API_KEY", ""),
        "api_url": os.environ.get("SPECTRAL_MEMORY_API_URL", "https://api.spectralmemory.com"),
        "user_id": os.environ.get("SPECTRAL_MEMORY_USER_ID", "default"),
    }


class SpectralMemoryProvider(MemoryProvider):
    """Spectral Memory — frequency-encoded structured memory.
    20 facts. Same token budget. Lossless under compression.
    """

    def __init__(self):
        self._config = None
        self._api_key = ""
        self._api_url = "https://api.spectralmemory.com"
        self._user_id = "default"
        self._client = None
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()
        self._prefetch_thread = None

    @property
    def name(self) -> str:
        return "spectral_memory"

    def is_available(self) -> bool:
        try:
            cfg = _load_config()
            return bool(cfg.get("api_key") or os.environ.get("SPECTRAL_MEMORY_API_KEY", ""))
        except Exception:
            return False

    def save_config(self, values: dict, hermes_home: str):
        from pathlib import Path
        config_dir = Path(hermes_home) / "spectral_memory"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.json"
        existing = {}
        if config_path.exists():
            try:
                existing = json.loads(config_path.read_text())
            except Exception:
                pass
        existing.update(values)
        config_path.write_text(json.dumps(existing, indent=2))

    def get_config_schema(self):
        return [
            {"key": "api_key", "description": "Spectral Memory API key", "secret": True, "env_var": "SPECTRAL_MEMORY_API_KEY", "url": "https://spectralmemory.com"},
            {"key": "user_id", "description": "User identifier for this agent", "default": "default"},
            {"key": "api_url", "description": "API endpoint", "default": "https://api.spectralmemory.com"},
        ]

    def initialize(self, session_id: str, **kwargs) -> None:
        self._config = _load_config()
        self._api_key = self._config.get("api_key") or os.environ.get("SPECTRAL_MEMORY_API_KEY", "")
        self._api_url = self._config.get("api_url", "https://api.spectralmemory.com").rstrip("/")
        self._user_id = self._config.get("user_id", "default")
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=30.0,
        )

    def _get(self, path: str, timeout: float = 30.0, **params) -> dict:
        try:
            r = self._client.get(
                f"{self._api_url}{path}",
                params={"user_id": self._user_id, **params},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("Spectral Memory GET %s failed: %s", path, e)
            return {}

    def _post(self, path: str, body: dict) -> dict:
        try:
            r = self._client.post(
                f"{self._api_url}{path}",
                json={"user_id": self._user_id, **body},
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("Spectral Memory POST %s failed: %s", path, e)
            return {}

    def system_prompt_block(self) -> str:
        return (
            "# Spectral Memory\n"
            "Active. Structured facts are frequency-encoded across 20 channels.\n"
            "Use fdm_encode to store discrete facts.\n"
            "Use fdm_decode to retrieve specific values instantly (0ms, from state).\n"
            "Use fdm_decode_spectral to read directly from the signal (~600ms) — "
            "use after compression to verify facts survived.\n"
            "The [MEMORY] block in context is the encoded signal — do not edit it directly."
        )

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        def _run():
            try:
                result = self._get("/context")
                fdm_block = result.get("fdm_block", "")
                plain_index = result.get("plain_index", "")
                if fdm_block:
                    with self._prefetch_lock:
                        self._prefetch_result = (
                            f"{fdm_block}\n\n"
                            f"<!-- Spectral Memory channel index -->\n{plain_index}"
                        )
            except Exception as e:
                logger.warning("Spectral Memory prefetch failed: %s", e)
        self._prefetch_thread = threading.Thread(
            target=_run, daemon=True, name="spectral-prefetch"
        )
        self._prefetch_thread.start()

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=5.0)
        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""
        return result

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        pass

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [ENCODE_SCHEMA, DECODE_SCHEMA, DECODE_SPECTRAL_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        if tool_name == "fdm_encode":
            label = args.get("label", "")
            value = args.get("value", "")
            if not label or not value:
                return _tool_error("fdm_encode requires label and value")
            result = self._post("/encode", {"label": label, "value": value})
            if not result:
                return _tool_error("fdm_encode failed — check API key and connection")
            return json.dumps({
                "result": (
                    f"Encoded {label}={value!r} on channel {result.get('channel', '?')}. "
                    f"{result.get('channel_count', '?')} facts total."
                )
            })

        elif tool_name == "fdm_decode":
            label = args.get("label", "")
            if not label:
                return _tool_error("fdm_decode requires label")
            result = self._get("/decode", label=label)
            if not result:
                return _tool_error(f"fdm_decode failed for {label}")
            return json.dumps({
                "result": f"{label} = {result.get('value', 'not found')}",
                "source": result.get("source", "state"),
                "latency_ms": result.get("latency_ms", 0),
            })

        elif tool_name == "fdm_decode_spectral":
            label = args.get("label", "")
            if not label:
                return _tool_error("fdm_decode_spectral requires label")
            result = self._get("/decode/model", timeout=120.0, label=label)
            if not result:
                return _tool_error(f"fdm_decode_spectral failed for {label}")
            return json.dumps({
                "result": f"{label} = {result.get('value', 'not found')}",
                "source": "model",
                "latency_ms": result.get("latency_ms", 0),
            })

        return _tool_error(f"Unknown tool: {tool_name}")

    def shutdown(self) -> None:
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=5.0)
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None


def register(ctx) -> None:
    ctx.register_memory_provider(SpectralMemoryProvider())