#!/usr/bin/env bash
# Query the Perplexity API from the command line.
# Usage:
#   scripts/perplexity.sh "your question"
#   scripts/perplexity.sh -m sonar-pro "deep question"
#   echo "question" | scripts/perplexity.sh
#
# Key is read from $PERPLEXITY_API_KEY or ~/.config/perplexity/key
# Models: sonar (cheap), sonar-pro (better), sonar-reasoning, sonar-deep-research

set -uo pipefail

MODEL="sonar"
if [[ "${1:-}" == "-m" ]]; then
  MODEL="$2"; shift 2
fi

KEY="${PERPLEXITY_API_KEY:-}"
if [[ -z "$KEY" && -f "$HOME/.config/perplexity/key" ]]; then
  KEY="$(cat "$HOME/.config/perplexity/key")"
fi
if [[ -z "$KEY" ]]; then
  echo "No Perplexity API key found (set PERPLEXITY_API_KEY or ~/.config/perplexity/key)" >&2
  exit 1
fi

if [[ $# -gt 0 ]]; then
  PROMPT="$*"
else
  PROMPT="$(cat)"
fi

BODY="$(PROMPT="$PROMPT" MODEL="$MODEL" python3 -c 'import json,os; print(json.dumps({"model":os.environ["MODEL"],"messages":[{"role":"user","content":os.environ["PROMPT"]}]}))')"

RESP="$(curl -s https://api.perplexity.ai/chat/completions \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")"

RESP="$RESP" python3 -c '
import json, os, sys
raw = os.environ.get("RESP", "")
if not raw.strip():
    print("Empty response from Perplexity API", file=sys.stderr); sys.exit(1)
d = json.loads(raw)
if "choices" not in d:
    print(json.dumps(d, indent=2)); sys.exit(1)
print(d["choices"][0]["message"]["content"])
cites = d.get("citations") or []
if cites:
    print("\nSources:")
    for i, c in enumerate(cites, 1):
        print(f"  [{i}] {c}")
cost = (d.get("usage", {}).get("cost") or {}).get("total_cost")
if cost is not None:
    print(f"\n(cost: ${cost:.4f})")
'
