#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from datetime import datetime


def parse_amount(value):
    """Amounts arrive as numbers or as strings with thousands separators, e.g. "4,804.15"."""
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return float(value)


def parse_ts(value):
    """Timestamps are ISO 8601 in UTC, e.g. 2026-09-21T15:30:26Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# Keep only the latest attempt for each txn_id.
# The file is not in time order, so compare timestamps instead of trusting line order.
latest = {}

with open("payments.jsonl", encoding="utf-8") as f:
    for line in f:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue  # unreadable line: ignore, per the README

        if not isinstance(event, dict) or not event.get("txn_id"):
            continue  # no txn_id: ignore, per the README

        txn_id = event["txn_id"]
        ts = parse_ts(event["ts"])
        if txn_id not in latest or ts > latest[txn_id][0]:
            latest[txn_id] = (ts, event)

# A payment is collected only if its latest attempt succeeded.
total = 0.0
count = 0
for _, event in latest.values():
    if event["status"] == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")