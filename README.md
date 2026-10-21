# Shelf Help

Turns a shop retailer's free-text drinks request into a valid order.

**Ground rule:** the LLM only *interprets text*. Code decides everything that touches
the catalogue: SKUs, prices, stock, quantities, totals and status.

## Setup

Windows (PowerShell):
```powershell
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then put your API key in .env
```

macOS / Linux:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your API key in .env
```

`LLM_PROVIDER` in `.env` picks the provider: `anthropic` (default), `openai`, `groq`, `gemini`
or `ollama`. Set the matching key (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY` or
`GEMINI_API_KEY`). `LLM_MODEL` optionally overrides the default model.

### No API key: run a local model with Ollama

1. Install Ollama from https://ollama.com and run `ollama pull llama3.2:3b`.
2. Put one line in `.env`: `LLM_PROVIDER=ollama`
3. That's it. The first call loads the model (can take ~2 minutes); after that each request
   takes a few seconds. All evals pass 5/5 with this setup.

## The one command

```bash
python run.py requests.json > responses.json
```

`requests.json` is a list of `{"id": ..., "text": ...}`. stdout is only the JSON results,
in input order. Logs go to stderr and `logs/run.jsonl`. Try it with
`python run.py evals/sample_requests.json`.

## Tests and evals

```bash
python -m pytest -q                  # unit tests, no API key needed
python evals/run_evals.py 2>nul      # each eval case 5 times (needs a key); use 2>/dev/null on macOS/Linux
```

The eval runner exits with code 1 if any case is below 5/5.

## How it works

```
text -> extract.py (LLM -> Intent, validated, 3 retries, regex budget cross-check)
     -> decide.py  (clarification / cannot_fulfil / solve)
     -> solver.py  (try all 385 orders, keep those passing every rule in rules.py, pick the best)
     -> message.py (template, numbers from code)
     -> validate.py (check the final response against all rules; on any failure -> safe fallback)
```

## Adding a shop rule

Write one function in `shelfhelp/rules.py`, add it to `RULES`, add one eval case to
`evals/cases.json`, and rerun the evals. If the rule depends on something the customer
says, it also needs an `Intent` field and a line in the prompt in `extract.py`.

## Clean-machine check

```powershell
powershell -ExecutionPolicy Bypass -File scripts\clean_check.ps1     # Windows
```
```bash
python -m venv /tmp/clean && source /tmp/clean/bin/activate         # macOS / Linux
pip install -r requirements.txt
python run.py evals/sample_requests.json > /tmp/out.json && python -m json.tool /tmp/out.json
```

## Live demo

```bash
python demo.py
```
Type a retailer request as plain text and press Enter; see the JSON response immediately.
Type `quit` to stop. This is for demos only — the real interface is the batch command above.
