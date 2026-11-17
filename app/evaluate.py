"""Training, the walk-forward backtest, the live prediction log and scoring."""
import time
from datetime import date as Date, timedelta

from . import config, db, rollup, registry

ROLLING = 7          # window for the error-over-time chart
BACKTEST_POINTS = 60  # at most this many evaluated days, so a long seed stays quick


def setup(model_cls, cfg):
    m = model_cls()
    cols = config.columns(cfg)
    m.columns = [c for c, _, _, _ in cols]
    m.ranges = {c: (lo, hi) for c, _, lo, hi in cols}
    return m


def train_and_predict(model_cls, cfg, train_rows, x_new):
    """One prediction, or (None, reason). Only ever sees `train_rows`."""
    if not model_cls.ready:
        return None, "waiting for your code"
    if len(train_rows) < model_cls.min_days:
        n = model_cls.min_days
        return None, f"needs {n} day" + ("" if n == 1 else "s")
    m = setup(model_cls, cfg)
    try:
        m.fit([r["x"] for r in train_rows], [r["y"] for r in train_rows])
        return float(m.predict([x_new])[0]), None
    except Exception as e:  # pasted code can fail; show it, don't crash
        return None, f"error: {e!r}"


def table(dataset):
    cfg = config.load(dataset)
    days = rollup.daily(db.entries(cfg["student"]), cfg)
    return cfg, days


def backtest(dataset):
    """For each model row t: train on rows before t, predict t, record the error.
    Never trains on day t or later."""
    cfg, days = table(dataset)
    rows, _ = rollup.lag_table(days, cfg)
    classes, load_errors = registry.discover()
    step = max(1, len(rows) // BACKTEST_POINTS)
    points = list(range(len(rows) - 1, 0, -step))[::-1]
    records, issues = [], {}
    for cls in classes:
        issues.setdefault(cls.name, None)
        if not cls.ready:
            continue
        started = time.time()
        for t in points:
            pred, why = train_and_predict(cls, cfg, rows[:t], rows[t]["x"])
            if pred is None:
                if why.startswith("error"):
                    issues[cls.name] = why
                    break
                continue
            records.append({"date": rows[t]["date"], "model": cls.name,
                            "predicted": pred, "actual": rows[t]["y"]})
        if time.time() - started > 20:
            issues[cls.name] = "slow: over 20 s for the backtest"
    return {"records": records, "rows": len(rows), "evaluated": len(points),
            "models": model_info(classes, issues), "load_errors": load_errors}


def model_info(classes, issues=None):
    issues = issues or {}
    return [{"name": c.name, "min_days": c.min_days, "source": c.source,
             "ready": c.ready, "issue": issues.get(c.name)} for c in classes]


def predict_tomorrow(today=None):
    """Train every eligible model on all rows so far and log its prediction for
    tomorrow, BEFORE tomorrow's target exists. Needs today's target."""
    today = today or Date.today().isoformat()
    cfg, days = table("own")
    if days.get(today, {}).get(cfg["target"]) is None:
        return {"ok": False, "message": f"Log today's {cfg['target'].replace('_', ' ')} first."}
    rows, x_tomorrow = rollup.lag_table(days, cfg, until=today)
    rows = [r for r in rows if r["date"] <= today]
    tomorrow = (Date.fromisoformat(today) + timedelta(days=1)).isoformat()
    classes, load_errors = registry.discover()
    made, skipped = [], []
    for cls in classes:
        pred, why = train_and_predict(cls, cfg, rows, x_tomorrow)
        if pred is None:
            skipped.append({"model": cls.name, "reason": why})
            continue
        db.save_prediction(cfg["student"], tomorrow, cls.name, pred)
        made.append({"model": cls.name, "predicted": pred})
    return {"ok": True, "target_date": tomorrow, "made": made, "skipped": skipped,
            "load_errors": load_errors}


def live():
    """Every logged prediction, scored against the day's CURRENT rolled target
    (a re-logged target re-scores; the prediction itself never changes)."""
    cfg, days = table("own")
    records = []
    for p in db.predictions(cfg["student"]):
        actual = days.get(p["target_date"], {}).get(cfg["target"])
        records.append({"date": p["target_date"], "model": p["model"],
                        "predicted": p["predicted"], "actual": actual})
    classes, load_errors = registry.discover()
    return {"records": records, "models": model_info(classes), "load_errors": load_errors}


def leaderboard(records, exclude=()):
    """MAE per model over the SHARED days only: days where every included model
    has a scored prediction. Different start days would otherwise make the
    numbers incomparable."""
    scored = [r for r in records if r["actual"] is not None and r["model"] not in exclude]
    models = sorted({r["model"] for r in scored})
    by_day = {}
    for r in scored:
        by_day.setdefault(r["date"], {})[r["model"]] = abs(r["predicted"] - r["actual"])
    shared = sorted(d for d, ms in by_day.items() if all(m in ms for m in models))
    board = []
    for m in models:
        errs = [by_day[d][m] for d in shared]
        board.append({"model": m, "mae": sum(errs) / len(errs) if errs else None,
                      "own_days": sum(1 for d in by_day if m in by_day[d])})
    board.sort(key=lambda b: (b["mae"] is None, b["mae"]))
    return {"shared_days": len(shared), "board": board}


def rolling(records):
    """Per model: [(date, mean absolute error of its last ROLLING scored days)]."""
    out = {}
    for r in sorted((r for r in records if r["actual"] is not None), key=lambda r: r["date"]):
        errs = out.setdefault(r["model"], {"errs": [], "points": []})
        errs["errs"].append(abs(r["predicted"] - r["actual"]))
        window = errs["errs"][-ROLLING:]
        errs["points"].append({"date": r["date"], "mae": sum(window) / len(window)})
    return {m: v["points"] for m, v in out.items()}
