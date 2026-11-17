"""Synthetic data for a fake student, with a KNOWN hidden rule.

The rule works through YESTERDAY's values, so the models can find it:
  evening mood today = 5
      + 0.6 per hour of yesterday's sleep above 6, up to 8 hours (then flat)
      - 0.8 per cup of yesterday's coffee above 3
      + 0.7 if yesterday you exercised
      - 1.0 if yesterday's bedtime was crazy_late
      + 0.3 * (yesterday's evening mood - 5)       (carry-over)
      + random noise
  rounded to a whole number and kept within 1..10.

Run:  python -m app.seed --days 60
"""
import argparse
import random
from datetime import date as Date, timedelta

from . import db
from .config import SEED_CONFIG

HIDDEN_RULE = __doc__.split("Run:")[0].strip()
STUDENT = SEED_CONFIG["student"]


def generate(days, seed=1):
    rng = random.Random(seed)
    start = Date.today() - timedelta(days=days)
    rows = []
    prev = None
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        sleep = round(min(14, max(3, rng.gauss(7, 1.3))) * 2) / 2
        coffee = max(0, min(10, round(rng.gauss(2.5, 1.6))))
        exercised = 1 if rng.random() < 0.4 else 0
        bedtime = rng.choices([0, 1, 2], weights=[5, 4, 1])[0]
        if prev is None:
            mood = rng.randint(4, 7)
        else:
            m = 5.0
            m += 0.6 * (min(prev["sleep"], 8) - 6)
            m -= 0.8 * max(0, prev["coffee"] - 3)
            m += 0.7 * prev["exercised"]
            m -= 1.0 * (prev["bedtime"] == 2)
            m += 0.3 * (prev["mood"] - 5)
            m += rng.gauss(0, 0.7)
            mood = max(1, min(10, round(m)))
        ts = f"{d}T21:00:00"
        # coffee is logged cup by cup, so the sum rollup has something to do
        rows.append({"timestamp": f"{d}T07:30:00", "date": d, "field": "sleep_hours", "value": sleep})
        for c in range(coffee):
            rows.append({"timestamp": f"{d}T{8 + 2 * c:02d}:00:00", "date": d,
                         "field": "coffee_cups", "value": 1})
        rows.append({"timestamp": ts, "date": d, "field": "exercised", "value": exercised})
        rows.append({"timestamp": ts, "date": d, "field": "bedtime", "value": bedtime})
        rows.append({"timestamp": ts, "date": d, "field": "mood_evening", "value": mood})
        prev = {"sleep": sleep, "coffee": coffee, "exercised": exercised,
                "bedtime": bedtime, "mood": mood}
    return rows


def seed(days, seed=1):
    db.replace_student(STUDENT, generate(days, seed))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--seed", type=int, default=1)
    a = p.parse_args()
    seed(a.days, a.seed)
    print(f"Synthetic student: {a.days} days written to {db.DB_PATH}")
