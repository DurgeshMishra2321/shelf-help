# Bugs scratch log

Every request that broke while building. Each one becomes an eval before it is fixed.

| # | What broke | How it was caught | Eval | Fix commit |
|---|---|---|---|---|
| 1 | `evals/cases.json` was first created with PowerShell `Set-Content -Encoding utf8`, which adds a byte-order mark; `json.loads` then refused the file and the eval runner crashed. | First dry run of `evals/run_evals.py` | – (tooling, not a request) | `test: eval runner + required cases` (reads with `utf-8-sig`; `run.py` does the same for `requests.json`) |
| 2 | **AI wrote a retired model name.** The AI tool set the default Gemini model to `gemini-2.5-flash` from memory. Google has retired it for new users, so every request failed with `404 NOT_FOUND` and every response became the safe fallback. | First real run of `python run.py evals/sample_requests.json`: the stderr log showed `fallback_reason: unexpected error: NotFoundError ... gemini-2.5-flash is no longer available`. | – (configuration, not a request; unit tests use a fake LLM so they could not catch it) | `998d981 fix: update default Gemini model (2.5-flash is retired)` |

## Operational finding (not a code bug)

- **Google 503 "high demand" and 20 s timeouts** on `gemini-3.8-flash`. Two of six sample requests (r2, r4) used all 3 attempts and returned the safe fallback. The retry loop and fallback worked as designed. Fix: switched the default to the `gemini-flash-lite-latest` alias (`1229dd5`); after that all six sample requests were correct with zero LLM errors.
- **Free-tier quota exhausted (429).** The first full eval run (11 cases x 5 runs, up to 3 attempts each) used up the key's free-tier request quota; every later call failed with `429 ... generate_content_free_tier_requests` or timed out, and every response was the safe fallback. Not fixable in code. Mitigations: wait for the quota to reset, enable billing on the key, run a few cases at a time, and `EVAL_PAUSE_SECONDS` in `evals/run_evals.py` for per-minute limits.

- **Local model cold start.** With Ollama, the first call loads `llama3.2:3b` into the GPU (~2 minutes on this laptop), longer than the 20 s timeout, so the whole first run fell back. Fix: 180 s timeout for the ollama provider (`27ecd7d`). Warm calls take under a second.

## Request bugs that became evals (found with Ollama `llama3.2:3b`)

| Eval | What broke | Red commit | Fix commit | Result |
|---|---|---|---|---|
| `own1` | The model sends `"exact_qty": null` instead of `{}` for "nothing said". `Intent` rejected it 3 times, so a clear request ("Mango and lime please, budget Rs 900") always got the "Sorry" fallback. `e1` failed the same way. | `ed29002` (0/5) | `ec77797` null → empty for list/dict fields | 5/5 |
| `own2` | For "Only cola, Rs 700." the model returns `only: [LIME, MANGO]`, inventing drinks the customer never named, so we recommended them instead of refusing. `s4` failed the same way. | `c62c960` (0/5) | `68152f1` code drops SKUs the text never mentions | 5/5 |

Full eval suite after both fixes: **65/65 runs (100%)** on the local model.
