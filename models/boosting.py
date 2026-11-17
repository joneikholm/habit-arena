"""Boosting. Paste your functions from the LNN platform between the two lines
below. Paste ALL of them: boost_predict calls the others.

Until you paste, the model uses reference/boosting.py if your teacher gave you
one, and otherwise waits for your code."""
from models.base import Model, load_code

# ---- PASTE YOUR FUNCTIONS FROM THE LNN PLATFORM BELOW ----


# ---- END ----

NEEDED = ["boost_predict"]
f, SOURCE = load_code(__name__, globals(), NEEDED)

N_TREES = 20
LR = 0.3
DEPTH = 2


class BoostingModel(Model):
    name = "Boosting"
    min_days = 28
    ready = f is not None
    source = SOURCE

    def fit(self, X, y):
        self.X = self.matrix(X)
        self.y = list(y)

    def predict(self, X):
        return [f.boost_predict(self.X, self.y, x, N_TREES, LR, DEPTH) for x in self.matrix(X)]
