"""Loads a config (config.yaml for your own data, the built-in seed config for
synthetic data) and describes the model columns each field turns into."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yaml"

TYPES = {"number", "scale", "yesno", "choice"}
ROLLUPS = {"sum", "mean", "max", "min", "last", "count"}
NAME = re.compile(r"^[a-z][a-z0-9_]*$")   # names become column names

# The fake student's fields. The hidden rule that uses them lives in seed.py.
SEED_CONFIG = {
    "student": "synthetic",
    "target": "mood_evening",
    "fields": [
        {"name": "sleep_hours", "type": "number", "min": 0, "max": 14, "rollup": "sum"},
        {"name": "coffee_cups", "type": "number", "min": 0, "max": 10, "rollup": "sum"},
        {"name": "exercised", "type": "yesno", "rollup": "max"},
        {"name": "bedtime", "type": "choice", "options": ["early", "late", "crazy_late"],
         "ordered": True, "rollup": "last"},
        {"name": "mood_evening", "type": "scale", "min": 1, "max": 10, "rollup": "mean"},
    ],
}


class ConfigError(ValueError):
    pass


def validate(cfg):
    if not isinstance(cfg, dict):
        raise ConfigError("config must be a mapping")
    for key in ("student", "target", "fields"):
        if key not in cfg:
            raise ConfigError(f"config is missing '{key}'")
    names = set()
    for f in cfg["fields"]:
        name = f.get("name")
        if not name or name in names:
            raise ConfigError(f"field name missing or used twice: {name!r}")
        if not NAME.match(name):
            raise ConfigError(f"{name!r}: use small letters, digits and _ only, starting with a letter")
        names.add(name)
        t = f.get("type")
        if t not in TYPES:
            raise ConfigError(f"{name}: type must be one of {sorted(TYPES)}")
        if t in ("number", "scale"):
            if "min" not in f or "max" not in f or f["min"] >= f["max"]:
                raise ConfigError(f"{name}: needs min < max")
            if t == "scale" and (f["min"] != int(f["min"]) or f["max"] != int(f["max"])):
                raise ConfigError(f"{name}: a scale needs whole numbers for min and max")
        if t == "choice":
            opts = f.get("options")
            if not isinstance(opts, list) or len(opts) < 2 or len(set(opts)) != len(opts):
                raise ConfigError(f"{name}: a choice needs at least 2 different options")
            for o in opts:
                if not isinstance(o, str) or not NAME.match(o):
                    raise ConfigError(f"{name}: option {o!r}: use small letters, digits and _ only")
            if "ordered" not in f:
                raise ConfigError(f"{name}: say ordered: true or ordered: false")
        rollup = f.get("rollup", "last" if t == "choice" else None)
        if rollup not in ROLLUPS:
            raise ConfigError(f"{name}: rollup must be one of {sorted(ROLLUPS)}")
        if t == "choice" and rollup not in ("last", "min", "max"):
            raise ConfigError(f"{name}: a choice can only use rollup last, min or max")
        if t == "choice" and not f["ordered"] and rollup != "last":
            raise ConfigError(f"{name}: an unordered choice can only use rollup last")
        f["rollup"] = rollup
    if cfg["target"] not in names:
        raise ConfigError(f"target '{cfg['target']}' is not one of the fields")
    target = field(cfg, cfg["target"])
    if target["type"] not in ("number", "scale"):
        raise ConfigError("the target must be a number or a scale")
    return cfg


def load(dataset="own"):
    if dataset == "synthetic":
        import copy
        return validate(copy.deepcopy(SEED_CONFIG))
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        return validate(yaml.safe_load(fh))


KEYS = {"number": ["name", "type", "min", "max", "rollup"],
        "scale": ["name", "type", "min", "max", "rollup"],
        "yesno": ["name", "type", "rollup"],
        "choice": ["name", "type", "options", "ordered", "rollup"]}


def save(cfg):
    """Validate, then write config.yaml (only the keys each type uses)."""
    cfg = validate(cfg)
    clean = {"student": cfg["student"], "target": cfg["target"],
             "fields": [{k: f[k] for k in KEYS[f["type"]]} for f in cfg["fields"]]}
    text = ("# Edited in the Fields tab of the app. You can also edit it by hand;\n"
            "# see README.md for the field types and rules.\n")
    text += yaml.safe_dump(clean, sort_keys=False, allow_unicode=True)
    CONFIG_PATH.write_text(text, encoding="utf-8")
    return clean


def field(cfg, name):
    for f in cfg["fields"]:
        if f["name"] == name:
            return f
    raise KeyError(name)


def columns(cfg):
    """Every model column, in a fixed order: (column name, field name, lo, hi).
    An unordered choice gives one column per option (one-hot); everything else
    gives one column. lo/hi are the range a column's values live in."""
    cols = []
    for f in cfg["fields"]:
        base = "prev_" + f["name"]
        if f["type"] in ("number", "scale"):
            cols.append((base, f["name"], f["min"], f["max"]))
        elif f["type"] == "yesno" or (f["type"] == "choice" and f["ordered"]):
            cols.append((base, f["name"], 0, 1))
        else:
            for opt in f["options"]:
                cols.append((f"{base}_{opt}", f["name"], 0, 1))
    return cols
