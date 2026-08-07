import json
import os

import anthropic
from rules import ROWS, score

SYSTEM = (
    "You write keyword rules for classifying bank transaction narrations. "
    'Output only a JSON array: [{"keyword": "SWIGGY INSTAMART", "category": "Groceries"}]. '
    "Rules are matched in order, first hit wins, so put specific keywords before "
    "general ones. No prose, no code fences."
)

CATEGORIES = ["Food", "Groceries", "Transport", "Shopping", "Bills",
              "Entertainment", "Travel", "Fuel", "Health", "Fees"]

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

samples = [row["narration"] for row in ROWS[:6]]
prompt = (
    f"Categories: {', '.join(CATEGORIES)}\n"
    f"Example narrations: {samples}\n"
    "Write a rulebook covering Indian card statement narrations."
)

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1500,
    system=SYSTEM,
    messages=[{"role": "user", "content": prompt}],
)

raw = response.content[0].text.strip()
print(repr(raw[-200:]))
print(response.stop_reason)
rules = json.loads(raw[raw.index("["):raw.rindex("]") + 1])

accuracy, wrong = score(rules)

print(f"{len(rules)} rules, accuracy {accuracy:.0%}")
for w in wrong:
    print(f"  {w['narration']} → {w['predicted']}, should be {w['correct']}")
print(f"tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")