"""Pearson's r: picks the one prev_ column with the largest |r| and predicts
with its straight line. Paste your functions from the LNN platform (Pearson
exercises 1-10) between the two lines below. Paste ALL of them: the ones listed
in NEEDED call the others.

Until you paste, the model uses reference/pearson.py if your teacher gave you
one, and otherwise waits for your code."""
from models.base import Model, load_code

# ---- PASTE YOUR FUNCTIONS FROM THE LNN PLATFORM BELOW ----


# ---- END ----

NEEDED = ["mean", "best_column", "line_predict"]
f, SOURCE = load_code(__name__, globals(), NEEDED)


class PearsonModel(Model):
    name = "Pearson's r"
    min_days = 7
    ready = f is not None
    source = SOURCE

    def fit(self, X, y):
        rows = self.matrix(X)
        cols = [[row[c] for row in rows] for c in range(len(self.columns))]
        self.ys = list(y)
        self.best = f.best_column(cols, self.ys)
        self.xs = cols[self.best] if self.best >= 0 else None
        self.chosen = self.columns[self.best] if self.best >= 0 else None

    def predict(self, X):
        if self.best < 0:
            return [f.mean(self.ys) for _ in X]
        return [f.line_predict(row[self.best], self.xs, self.ys) for row in self.matrix(X)]
