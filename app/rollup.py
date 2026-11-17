"""Raw entries -> one value per field per day -> the lag table the models see.

Row for day d = yesterday's (d-1) value of every field as prev_ columns, plus
day d's target. Same-day values never reach a model.
"""
from datetime import date as Date, timedelta

from .config import columns


def _rollup(rule, values):
    if rule == "sum":
        return sum(values)
    if rule == "mean":
        return sum(values) / len(values)
    if rule == "max":
        return max(values)
    if rule == "min":
        return min(values)
    if rule == "count":
        return len(values)
    return values[-1]  # last


def daily(entries, cfg):
    """{date: {field: value}} using each field's rollup rule. Entries must be
    in logging order (db.entries sorts them)."""
    rules = {f["name"]: f["rollup"] for f in cfg["fields"]}
    grouped = {}
    for e in entries:
        if e["field"] in rules:
            grouped.setdefault(e["date"], {}).setdefault(e["field"], []).append(e["value"])
    return {d: {name: _rollup(rules[name], vals) for name, vals in fields.items()}
            for d, fields in sorted(grouped.items())}


def encode(cfg, day_values):
    """One day's rolled values -> {column: value} for the columns that day has.
    A field the day lacks gives no column (filled later)."""
    out = {}
    for f in cfg["fields"]:
        v = day_values.get(f["name"])
        if v is None:
            continue
        base = "prev_" + f["name"]
        if f["type"] == "choice" and f["ordered"]:
            out[base] = int(v) / (len(f["options"]) - 1)
        elif f["type"] == "choice":
            for i, opt in enumerate(f["options"]):
                out[f"{base}_{opt}"] = 1.0 if int(v) == i else 0.0
        else:
            out[base] = float(v)
    return out


def _days(first, last):
    d = Date.fromisoformat(first)
    end = Date.fromisoformat(last)
    while d <= end:
        yield d.isoformat()
        d += timedelta(days=1)


def _prev_row(cfg, cols, enc, known):
    """Fill a day's encoded values; a missing column gets its mean so far
    (`known` holds only earlier days). One-hot columns of a missing choice are 0."""
    onehot = {c for c, fname, _, _ in cols
              if any(f["name"] == fname and f["type"] == "choice" and not f["ordered"]
                     for f in cfg["fields"])}
    row = {}
    for c, _, lo, hi in cols:
        if c in enc:
            row[c] = enc[c]
        elif c in onehot:
            row[c] = 0.0
        elif known.get(c):
            row[c] = sum(known[c]) / len(known[c])
        else:
            row[c] = 0.0 if hi == 1 and lo == 0 else (lo + hi) / 2
    return row


def lag_table(days, cfg, until=None):
    """All model rows in date order: [{'date', 'x': {prev_...}, 'y'}].
    Only days whose target is present are rows; the first calendar day is never
    a row. If `until` is given, also returns the x row for the day after it
    (built from `until`'s values) as the second result."""
    if not days:
        return [], None
    cols = columns(cfg)
    target = cfg["target"]
    first = min(days)
    last = max(max(days), until) if until else max(days)
    known = {}          # column -> encoded values of the days seen so far
    rows = []
    prev_x = None
    for d in _days(first, last):
        if prev_x is not None:
            y = days.get(d, {}).get(target)
            if y is not None:
                rows.append({"date": d, "x": prev_x, "y": float(y)})
        enc = encode(cfg, days.get(d, {}))
        prev_x = _prev_row(cfg, cols, enc, known)
        for c, v in enc.items():
            known.setdefault(c, []).append(v)
    return rows, (prev_x if until else None)
