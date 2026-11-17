"""FastAPI routes. Run: uvicorn app.main:app --reload"""
from datetime import date as Date

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, db, evaluate, rollup, seed

app = FastAPI(title="Habit Arena")
STATIC = config.ROOT / "static"


def load(dataset):
    if dataset not in ("own", "synthetic"):
        raise HTTPException(400, "dataset must be own or synthetic")
    try:
        return config.load(dataset)
    except (config.ConfigError, OSError) as e:
        raise HTTPException(400, f"config.yaml: {e}")


@app.get("/")
def index():
    # VERSION counts deploys. It is shown on the Results page and added to the
    # app.js / style.css addresses, so a phone fetches the new files at once.
    version = (config.ROOT / "VERSION").read_text().strip()
    html = (STATIC / "index.html").read_text().replace("%VERSION%", version)
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


@app.get("/api/config")
def get_config(dataset: str = "own"):
    cfg = load(dataset)
    out = {"student": cfg["student"], "target": cfg["target"], "fields": cfg["fields"],
           "today": Date.today().isoformat()}
    if dataset == "synthetic":
        out["hidden_rule"] = seed.HIDDEN_RULE
    else:
        out["entry_counts"] = db.entry_counts(cfg["student"])
    return out


class ConfigIn(BaseModel):
    student: str
    target: str
    fields: list[dict]


def locked_changes(old, new, counts):
    """A field with entries keeps its name, type and options (its meaning).
    The pseudonym is locked once there is data, because entries are stored under it."""
    problems = []
    if counts and new["student"] != old["student"]:
        problems.append("The pseudonym can't change once you have logged data.")
    new_by_name = {f.get("name"): f for f in new["fields"]}
    old_names = {f["name"] for f in old["fields"]}
    for name in new_by_name:
        if name not in old_names and counts.get(name):
            problems.append(f"'{name}' was used before by a deleted field and still has its old "
                            "entries. Pick another name.")
    for f in old["fields"]:
        if not counts.get(f["name"]):
            continue
        g = new_by_name.get(f["name"])
        if g is None:
            continue  # deleting is allowed; the entries stay and come back if re-added
        if g.get("type") != f["type"]:
            problems.append(f"{f['name']} has logged entries, so its type is locked.")
        elif f["type"] == "choice" and g.get("options") != f["options"]:
            problems.append(f"{f['name']} has logged entries, so its options are locked.")
    return problems


@app.put("/api/config")
def put_config(c: ConfigIn):
    old = load("own")
    new = c.model_dump()
    problems = locked_changes(old, new, db.entry_counts(old["student"]))
    if problems:
        raise HTTPException(400, " ".join(problems))
    try:
        return config.save(new)
    except config.ConfigError as e:
        raise HTTPException(400, str(e))


class Entry(BaseModel):
    date: str
    field: str
    value: float


@app.post("/api/entries")
def add_entry(e: Entry):
    cfg = load("own")
    try:
        d = Date.fromisoformat(e.date)
    except ValueError:
        raise HTTPException(400, "date must be YYYY-MM-DD")
    if d > Date.today():
        raise HTTPException(400, "You can't log a day that hasn't happened yet.")
    try:
        f = config.field(cfg, e.field)
    except KeyError:
        raise HTTPException(400, f"unknown field {e.field}")
    v = e.value
    if f["type"] in ("number", "scale") and not f["min"] <= v <= f["max"]:
        raise HTTPException(400, f"{f['name']} must be between {f['min']} and {f['max']}")
    if f["type"] == "yesno" and v not in (0, 1):
        raise HTTPException(400, "yes/no must be 1 or 0")
    if f["type"] == "choice" and (v != int(v) or not 0 <= v < len(f["options"])):
        raise HTTPException(400, "not one of the options")
    return {"id": db.add_entry(cfg["student"], e.date, e.field, v, replace=f["rollup"] == "last")}


@app.get("/api/entries")
def list_entries(date: str):
    return db.entries(load("own")["student"], date)


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int):
    db.delete_entry(load("own")["student"], entry_id)
    return {"ok": True}


@app.get("/api/days")
def days(dataset: str = "own"):
    cfg = load(dataset)
    return rollup.daily(db.entries(cfg["student"]), cfg)


@app.post("/api/predict")
def predict():
    load("own")
    return evaluate.predict_tomorrow()


def _scored(result, exclude):
    ex = set(filter(None, exclude.split(",")))
    result["leaderboard"] = evaluate.leaderboard(result["records"], ex)
    result["rolling"] = evaluate.rolling(result["records"])
    return result


@app.get("/api/live")
def live(exclude: str = ""):
    load("own")
    return _scored(evaluate.live(), exclude)


@app.get("/api/backtest")
def backtest(dataset: str = "own", exclude: str = ""):
    load(dataset)
    return _scored(evaluate.backtest(dataset), exclude)


class Seed(BaseModel):
    days: int


@app.post("/api/seed")
def make_seed(s: Seed):
    if not 2 <= s.days <= 730:
        raise HTTPException(400, "days must be between 2 and 730")
    seed.seed(s.days)
    return {"ok": True}


app.mount("/static", StaticFiles(directory=STATIC), name="static")
