# Brevix Evals

Three-arm A/B harness measuring real Claude output tokens with and without Brevix.

## Arms

| Arm | System prompt |
|-----|---------------|
| baseline | (empty) |
| control | "Be terse. Avoid filler." |
| brevix | Brevix full-mode rules |

The `control` arm is critical — without it, savings could just reflect "asked the model to be brief," not Brevix's actual contribution.

## Run

```bash
pip install anthropic tiktoken
export ANTHROPIC_API_KEY=...

python evals/llm_run.py --prompts evals/prompts/en.txt \
  --model claude-sonnet-4-6 --out evals/snapshots/latest.json

python evals/measure.py evals/snapshots/latest.json
```

`llm_run.py` calls the API; `measure.py` is offline and works on any committed snapshot.

## Output

```
arm       n   median  mean   stdev  total  vs baseline  vs control
baseline  10  221     247.3  88.4   2473   —            —
control   10  178     191.6  61.7   1916   22.5%        —
brevix    10  119     128.4  43.1   1284   48.1%        33.0%
```

Brevix's score vs control is the honest metric — it's the savings *beyond* "just be brief."
