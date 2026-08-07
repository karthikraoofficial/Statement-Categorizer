# Statement categoriser — a loop-engineering project

The loop writes a keyword rulebook for categorising card statement narrations,
scores it against a labelled CSV, and keeps correcting itself until it hits 95%.

## Run it

Open the folder in VS Code, then in its terminal (Ctrl+`):

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install fastapi uvicorn anthropic
export ANTHROPIC_API_KEY=sk-ant-...  # Windows: set ANTHROPIC_API_KEY=sk-ant-...
uvicorn app:app --reload
```

Open http://127.0.0.1:8000 and press **Run the loop**.

`--reload` restarts the server whenever you save a file. No npm, no build step.

## Where each loop component lives

| Component | In the code |
|---|---|
| Goal + termination condition | `TARGET = 0.95` accuracy on the labelled CSV |
| Tool that touches the environment | `apply_rules()` — runs the rulebook on real rows |
| Verifier | `score()` — deterministic, external, zero tokens |
| Context management | `build_prompt()` rebuilds fresh; only errors are fed back |
| Termination | target hit, `MAX_STEPS`, identical-rulebook detection |
| Escalation | returns `no_progress` / `step_cap` to the UI |

## Why this is token-cheap

Scoring all 38 rows costs nothing, because it is Python, not a model call.
The model only ever sees six failing rows at a time. And the loop's output is
an artifact — once `rulebook.json` exists, categorising a transaction calls no
model at all. You pay tokens once to build it, then zero forever.

## Extensions, roughly in order of difficulty

1. Replace `data/transactions.csv` with 40 rows from your own statement.
   Fair warning: the loop will overfit if the file is small. Hold back ten
   rows it never sees and check accuracy against those separately.
2. Log every run to a JSONL file. That file is your trace store.
3. Add a `/traces` page. Reading your own traces is the start of a
   hill-climbing loop.
4. Add a fallback tier: rulebook first, model call only for narrations that
   come back `Uncategorised`. That is the cost curve most production
   classifiers actually run on.
5. Trigger it on an event — a file watcher on a statement drop folder —
   so runs start without you.
