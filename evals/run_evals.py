"""Run every eval case 5 times through the real pipeline and print a pass table.

    python evals/run_evals.py            # all cases
    python evals/run_evals.py e4 own1    # only these cases

Exit code 0 only if every case passes 5/5.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evals.checks import run_check  # noqa: E402
from run import respond             # noqa: E402  (the same function run.py uses)
from shelfhelp import llm           # noqa: E402

RUNS = 5


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    llm.check_config()
    cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8-sig"))
    if len(sys.argv) > 1:
        cases = [case for case in cases if case["id"] in sys.argv[1:]]

    rows, all_green = [], True
    for case in cases:
        passes, failed = 0, set()
        for _ in range(RUNS):
            response = respond(case["text"], case["id"])
            failing = [name for name in case["checks"] if not run_check(name, response, case)]
            if failing:
                failed.update(failing)
            else:
                passes += 1
        all_green &= passes == RUNS
        rows.append((case["id"], passes, ", ".join(sorted(failed))))

    print(f"\n{'case':<8}{'passes':<10}failing checks")
    print("-" * 50)
    for case_id, passes, failed in rows:
        print(f"{case_id:<8}{passes}/{RUNS:<8}{failed or '-'}")
    total_passes = sum(passes for _, passes, _ in rows)
    print("-" * 50)
    print(f"overall: {total_passes}/{len(rows) * RUNS} runs passed "
          f"({100 * total_passes / max(1, len(rows) * RUNS):.0f}%) -> "
          f"{'GREEN' if all_green else 'RED'}")
    return 0 if all_green else 1


if __name__ == "__main__":
    sys.exit(main())
