"""JSON-lines event logging. Path comes from CONCIERGE_LOG (default logs/agent.log)."""
import json
import os
import time
from pathlib import Path


def log_event(event: str, **fields) -> None:
    """Append one structured event. Logging must never break the app."""
    try:
        path = Path(os.environ.get("CONCIERGE_LOG", "logs/agent.log"))
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts": round(time.time(), 3), "event": event, **fields}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except OSError:
        pass
