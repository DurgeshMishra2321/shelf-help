"""Interactive demo: type a retailer request, see the response. For live demos only;
the real interface is `python run.py requests.json` (see README).

    python demo.py
"""

import json
import sys

from run import respond
from shelfhelp import llm

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    llm.check_config()
    print("Type a retailer request (or 'quit').\n")
    while True:
        text = input("> ").strip()
        if not text or text.lower() in ("quit", "exit"):
            break
        response = respond(text)
        print(json.dumps(response, ensure_ascii=False, indent=2), "\n")
