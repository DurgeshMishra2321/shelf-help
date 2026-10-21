"""Logs go to stderr and logs/run.jsonl, never to stdout (stdout is only JSON output)."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "run.jsonl"


def log(event: str, **fields) -> None:
    record = {"time": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
    line = json.dumps(record, ensure_ascii=False, default=str)
    print(line, file=sys.stderr)
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass   # a log file problem must never break a request
