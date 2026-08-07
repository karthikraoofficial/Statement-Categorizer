import json

from rules import load, score

with open("rulebook.json") as f:
    rules = json.load(f)

train_accuracy, _ = score(rules)
holdout = load("data/holdout.csv")
holdout_accuracy, misses = score(rules, holdout)

print(f"train:   {train_accuracy:.0%}")
print(f"holdout: {holdout_accuracy:.0%}")
for m in misses:
    print(f"  {m['issue']}")