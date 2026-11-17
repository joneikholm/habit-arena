"""The Model base class every model extends (given; students don't edit it)."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "reference"


class Model:
    name = "Model"
    min_days = 1          # don't predict before this many training rows
    ready = True          # a paste-block model sets this: True once it has code (pasted or reference)
    source = "your code"  # "your code", "reference", "reference (missing: ...)", "missing: ...", "no code yet"

    # Set by the harness before fit, so every model sees the same columns:
    columns = []          # prev_ column names, in a fixed order
    ranges = {}           # column -> (lo, hi), for scaling

    def fit(self, X, y):  # X: list of dicts (one per day), y: list of floats
        raise NotImplementedError

    def predict(self, X):  # returns list of floats
        raise NotImplementedError

    def matrix(self, X):
        """List of dicts -> list of lists, in self.columns order."""
        return [[row[c] for c in self.columns] for row in X]


def load_code(model_module, namespace, needed):
    """Where a model gets its functions, in this order:
    1. the student's pasted code, once ALL `needed` names are pasted;
    2. reference/<model>.py, if the teacher handed one out;
    3. nothing: the model waits for code.
    Returns (functions or None, source text for the leaderboard)."""
    missing = [n for n in needed if not callable(namespace.get(n))]
    if not missing:
        return SimpleNamespace(**{n: namespace[n] for n in needed}), "your code"
    ref = REFERENCE_DIR / (model_module.rsplit(".", 1)[-1] + ".py")
    partial = len(missing) < len(needed)
    if ref.exists():
        spec = importlib.util.spec_from_file_location(f"reference_{ref.stem}", ref)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, "reference (missing: " + ", ".join(missing) + ")" if partial else "reference"
    if partial:
        return None, "missing: " + ", ".join(missing)
    return None, "no code yet"
