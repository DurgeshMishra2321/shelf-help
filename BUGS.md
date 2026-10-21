# Bugs scratch log

Every request that broke while building. Each one becomes an eval before it is fixed.

| # | What broke | How it was caught | Eval | Fix commit |
|---|---|---|---|---|
| 1 | `evals/cases.json` was first created with PowerShell `Set-Content -Encoding utf8`, which adds a byte-order mark; `json.loads` then refused the file and the eval runner crashed. | First dry run of `evals/run_evals.py` | – (tooling, not a request) | `test: eval runner + required cases` (reads with `utf-8-sig`; `run.py` does the same for `requests.json`) |
| 2 | **AI wrote a retired model name.** The AI tool set the default Gemini model to `gemini-2.5-flash` from memory. Google has retired it for new users, so every request failed with `404 NOT_FOUND` and every response became the safe fallback. | First real run of `python run.py evals/sample_requests.json`: the stderr log showed `fallback_reason: unexpected error: NotFoundError ... gemini-2.5-flash is no longer available`. | – (configuration, not a request; unit tests use a fake LLM so they could not catch it) | `998d981 fix: update default Gemini model (2.5-flash is retired)` |

## Operational finding (not a code bug)

- **Google 503 "high demand" and 20 s timeouts** on `gemini-3.8-flash`. Two of six sample requests (r2, r4) used all 3 attempts and returned the safe fallback. The retry loop and fallback worked as designed; nothing was changed. Mitigations: lighter model via `LLM_MODEL`, paid tier, or rerun later.

## Still to add

- `own1` / `own2`: real request-level failures from eval runs, each added to `evals/cases.json` red before the fix.
