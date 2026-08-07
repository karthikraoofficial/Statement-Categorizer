import json
import os

import anthropic
from rules import ROWS, score

MODEL = "claude-haiku-4-5-20251001"
MAX_STEPS = 8
MAX_TOKENS = 4000

CATEGORIES = ["Food", "Groceries", "Transport", "Shopping", "Bills",
              "Entertainment", "Travel", "Fuel", "Health", "Fees"]

SYSTEM = (
    "You write keyword rules for classifying bank transaction narrations. "
    'Output only a JSON array: [{"keyword": "SWIGGY INSTAMART", "category": "Groceries"}]. '
    "Rules are matched in order, first hit wins, so put specific keywords before "
    "general ones. No prose, no code fences."
)

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def build_prompt(rules, wrong):
    """Fresh every step — but the model must see what it is editing."""
    if wrong is None:
        samples = [row["narration"] for row in ROWS[:6]]
        return (f"Categories: {', '.join(CATEGORIES)}\n"
                f"Example narrations: {samples}\n"
                "Write a rulebook of 40 or more rules covering Indian card statement "
                "narrations — food delivery, quick commerce, cabs, e-commerce, utilities, "
                "streaming, travel, fuel, pharmacy and card fees. Use short brand keywords "
                "like 'ZOMATO' rather than full narration strings.")

    lines = [f"- {w['issue']}" for w in wrong[:15]]
    return ("Here is your current rulebook:\n" + json.dumps(rules) +
            "\n\nIt has these problems:\n" + "\n".join(lines) +
            "\n\nReturn the COMPLETE rulebook with these problems fixed. "
            "Keep every existing rule that is not causing a problem — do not shorten "
            "the rulebook. Rules match in order and the first hit wins, so move "
            "specific keywords above general ones.")


def finish(outcome, rules, trace, total_in, total_out):
    if rules:
        with open("rulebook.json", "w") as f:
            json.dump(rules, f, indent=2)
    else:
        print("no rules produced — keeping the previous rulebook.json")
    print(f"\n{outcome} — {total_in} in, {total_out} out")
    return {"outcome": outcome, "rules": rules, "trace": trace,
            "tokens_in": total_in, "tokens_out": total_out}


def run():
    rules, wrong, seen, trace = [], None, set(), []
    best_rules, best_accuracy = [], -1.0
    total_in = total_out = 0

    for step in range(1, MAX_STEPS + 1):
        response = client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM,
            messages=[{"role": "user", "content": build_prompt(rules, wrong)}],
        )
        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens

        raw = response.content[0].text.strip()
        try:
            rules = json.loads(raw[raw.index("["):raw.rindex("]") + 1])
        except (ValueError, json.JSONDecodeError):
            print(f"{step:02d}  unparseable ({response.stop_reason}), "
                  f"{len(raw)} chars, retrying")
            trace.append({
                "step": step,
                "error": f"model did not return valid JSON ({response.stop_reason})",
                "tokens_in": response.usage.input_tokens,
                "tokens_out": response.usage.output_tokens,
            })
            continue

        accuracy, wrong = score(rules)

        # Never end worse than the best attempt so far.
        if accuracy > best_accuracy:
            best_accuracy, best_rules = accuracy, rules

        trace.append({
            "step": step,
            "accuracy": round(accuracy, 3),
            "rule_count": len(rules),
            "wrong": wrong[:6],
            "tokens_in": response.usage.input_tokens,
            "tokens_out": response.usage.output_tokens,
        })

        print(f"{step:02d}  {accuracy:.0%}  ({len(rules)} rules, "
              f"{response.usage.input_tokens}+{response.usage.output_tokens} tokens)")
        for w in wrong[:6]:
            print(f"      {w['issue']}")

        if not wrong:
            return finish("verified", rules, trace, total_in, total_out)

        fingerprint = json.dumps(rules, sort_keys=True)
        if fingerprint in seen:
            return finish("no_progress", best_rules, trace, total_in, total_out)
        seen.add(fingerprint)

    return finish("step_cap", best_rules, trace, total_in, total_out)


if __name__ == "__main__":
    run()