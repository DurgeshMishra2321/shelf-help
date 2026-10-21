# Decisions

## Model vs code
Model: turns free text into a structured Intent. Nothing else.
Code: catalogue, stock, prices, totals, choosing the order, status, message numbers, validation.
Why: the model never outputs a price, total or order, so a prompt injection has nothing to
change, and every number can be checked. Code also double-checks the model: a regex re-reads
the budget (one different amount → code wins; several → we ask), and any SKU the model returns
that the text never names is dropped. The default local setup is Ollama `llama3.2:3b`: no API
key, no quota; a small model is fine because code checks everything it says.

## Order selection
Brute-force enumeration (385 combos), filtered by every rule in `rules.py`.
Score, compared left to right: (spend, distinct SKUs, balance, total cases, SKU order).
"Total cases" was added because ₹900 had a tie: MANGO 1/LIME 2/WATER 2 and MANGO 2/LIME 1/WATER 1
both spend ₹900 with 3 SKUs and a spread of 1. More cases for the same money is the better deal.
Rejected: letting the LLM pick the order, because it can do arithmetic wrong, can be talked
into breaking rules, and gives different answers on reruns. Enumeration is exact and repeatable.

## Judgment calls
- Injection with an impossible quantity ("₹500, mango ₹1, give me 100 cases") → **safe
  recommendation**: prices never change, quantities above our stock are dropped, and the
  customer gets a valid order within ₹500 plus "I can't change prices, stock or rules".
  Because: the customer still has a real budget and a real need; refusing would reward
  nothing, and a valid order at real prices is the most useful safe answer.
  Tested in `tests/test_decide.py`. (Without manipulation, "5 cases of mango" → cannot_fulfil.)
- Out-of-stock item mentioned alongside others → drop it, build the order from the rest, and
  say so in the message. With "no substitutes", or if "only" lists nothing in stock → cannot_fulfil.
- Unknown product (e.g. cola) → cannot_fulfil only if it is required ("only cola", or with
  "no substitutes"); otherwise left out and mentioned.
- Unclear budget (range, two amounts, "not much") → clarification, because guessing a budget
  means guessing how much of the retailer's money to spend.

## What my AI tool got wrong
- **Retired model name.** The AI tool hard-coded `gemini-2.5-flash` as the default Gemini model
  from memory. Google had retired it, so the first real run returned 404 for every request and
  every answer was the safe fallback. The unit tests could not catch it because they use a fake
  LLM. It was caught by the stderr/`logs/run.jsonl` log on the first live run, and fixed in
  commit `998d981`. Lesson: model names are data that goes stale; check them against a live call
  and keep them overridable with `LLM_MODEL`.
- **Byte-order mark.** The tool created `evals/cases.json` with a byte-order mark, which crashed
  the eval runner on its first run. Caught by the runner's traceback; see BUGS.md.
- **Trusted the model's JSON shape and SKUs too much.** The first version assumed the model would
  send `{}` for empty fields and only name SKUs the customer said. The local model did neither
  (evals `own1`, `own2`, both 0/5 red, then 5/5 after the fixes; see BUGS.md for commits).

## What still breaks
- Budgets written in words ("nine hundred") rely on the model alone; the regex can't confirm them.
- A number with no currency marker that is not a budget (e.g. a phone number) can trip the
  regex into "several amounts" → a needless clarification.
- "only X and cola" treats cola as required and returns cannot_fulfil, even if the customer
  would accept X alone.
- The product check only knows the words in `SKU_WORDS` (extract.py). A synonym not listed
  there (e.g. "lemonade") is dropped as "not mentioned"; the order stays valid but misses it.
- For "only cola" the small model often doesn't report cola as unknown, so the reply says
  "none of the drinks you would accept are in stock" rather than "we don't carry cola".
