import csv


def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))


ROWS = load("data/train.csv")


def apply_rules(rules, narration):
    """First matching keyword wins — so order matters."""
    text = narration.upper()
    for rule in rules:
        if rule.get("keyword", "").upper() in text:
            return rule.get("category", "Uncategorised")
    return "Uncategorised"


def find_shadowed(rules):
    """A rule is unreachable if an earlier rule's keyword is inside its own.
    'SWIGGY' above 'SWIGGY INSTAMART' means the second can never fire."""
    problems = []
    for i, rule in enumerate(rules):
        keyword = rule.get("keyword", "").upper()
        if not keyword:
            continue
        for earlier in rules[:i]:
            earlier_keyword = earlier.get("keyword", "").upper()
            if earlier_keyword and earlier_keyword in keyword:
                problems.append({
                    "narration": f"rule {keyword!r}",
                    "predicted": "never reached",
                    "correct": f"listed above {earlier_keyword!r}",
                    "issue": (f"rule {keyword!r} can never fire because "
                              f"{earlier_keyword!r} is listed above it — move it above"),
                })
                break
    return problems


def score(rules, rows=None):
    """The verifier. Deterministic, external, costs nothing."""
    rows = ROWS if rows is None else rows
    wrong = []
    for row in rows:
        predicted = apply_rules(rules, row["narration"])
        if predicted != row["category"]:
            wrong.append({
                "narration": row["narration"],
                "predicted": predicted,
                "correct": row["category"],
                "issue": (f"{row['narration']!r} → you said {predicted}, "
                          f"should be {row['category']}"),
            })

    accuracy = (len(rows) - len(wrong)) / len(rows)
    wrong += find_shadowed(rules)
    return accuracy, wrong