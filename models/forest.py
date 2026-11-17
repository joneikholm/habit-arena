"""Random forest. Paste your functions from the LNN platform between the two lines
below. Paste ALL of them: forest_predict calls the others.

Until you paste, the model uses reference/forest.py if your teacher gave you
one, and otherwise waits for your code."""
from models.base import Model, load_code

# ---- PASTE YOUR FUNCTIONS FROM THE LNN PLATFORM BELOW ----


# ---- END ----

NEEDED = ["forest_predict"]
f, SOURCE = load_code(__name__, globals(), NEEDED)

N_TREES = 30
DEPTH = 3
SEED = 7


class ForestModel(Model):
    name = "Random forest"
    min_days = 21
    ready = f is not None
    source = SOURCE

    def fit(self, X, y):
        self.X = self.matrix(X)
        self.y = list(y)

    def predict(self, X):
        return [f.forest_predict(self.X, self.y, x, N_TREES, DEPTH, SEED) for x in self.matrix(X)]
