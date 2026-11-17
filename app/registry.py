"""Finds every Model subclass in models/. Adding a model = adding one file."""
import importlib
import inspect
import pkgutil
import sys

from .config import ROOT

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models  # noqa: E402
from models.base import Model  # noqa: E402

SKIP = {"base"}


def discover():
    """[(model class, load error)]; a file that fails to import is reported, not hidden."""
    found = []
    errors = []
    for info in sorted(pkgutil.iter_modules(models.__path__), key=lambda m: m.name):
        if info.name in SKIP or info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"models.{info.name}")
        except Exception as e:  # a broken paste must not take the whole app down
            errors.append({"file": f"models/{info.name}.py", "error": repr(e)})
            continue
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, Model) and obj is not Model and obj.__module__ == mod.__name__:
                found.append(obj)
    found.sort(key=lambda c: (c.min_days, c.name))
    return found, errors
