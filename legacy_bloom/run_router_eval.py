import json
import os
from collections import Counter, defaultdict

import requests

DATA_PATH = os.path.join("eval", "router_eval.jsonl")
API_URL = os.getenv("EVAL_API_URL", "http://localhost:8000/chat")

# Update these to match your actual backend response key(s)
ROUTE_KEYS = ["route", "category", "router_route"]

def extract_route(resp: dict) -> str:
    for k in ROUTE_KEYS:
        v = resp.get(k)
        if v:
            return str(v)
    # If your backend nests router output, add logic here.
    return ""

def main():
    # Load dataset
    rows = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    total = 0
    correct = 0
    confusion = Counter()
    per_expected = Counter()
    per_correct = Counter()
    confusions = []

    for r in rows:
        total += 1
        text = r["text"]
        expected = r["expected"]

        resp = requests.post(API_URL, json={"message": text}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        predicted = extract_route(data) or "UNKNOWN"

        per_expected[expected] += 1
        if predicted == expected:
            correct += 1
            per_correct[expected] += 1
        else:
            confusion[(expected, predicted)] += 1
            confusions.append({
                "id": r.get("id"),
                "text": text,
                "expected": expected,
                "predicted": predicted,
            })

    acc = correct / total if total else 0.0

    print("\n=== Router Eval Results ===")
    print(f"API_URL: {API_URL}")
    print(f"Total: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {acc:.2%}")

    print("\n=== Per-class accuracy ===")
    for label in sorted(per_expected.keys()):
        denom = per_expected[label]
        num = per_correct[label]
        print(f"{label:18} {num}/{denom} ({(num/denom):.2%})")

    print("\n=== Confusion cases (top) ===")
    for (exp, pred), n in confusion.most_common(10):
        print(f"{exp} -> {pred}: {n}")

    if confusions:
        print("\n=== Example misroutes (up to 8) ===")
        for c in confusions[:8]:
            print(f"- {c['id']} expected={c['expected']} predicted={c['predicted']} text={c['text']}")

if __name__ == "__main__":
    main()
