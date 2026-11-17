"""Decision tree. Paste your functions from the LNN platform between the two lines
below. Paste ALL of them: tree_predict calls the others.

Until you paste, the model uses reference/tree.py if your teacher gave you
one, and otherwise waits for your code."""
from models.base import Model, load_code

# ---- PASTE YOUR FUNCTIONS FROM THE LNN PLATFORM BELOW ----


# ---- END ----

NEEDED = ["tree_predict"]
f, SOURCE = load_code(__name__, globals(), NEEDED)

DEPTH = 3


class TreeModel(Model):
    name = "Decision tree"
    min_days = 14
    ready = f is not None
    source = SOURCE

    def fit(self, X, y):
        self.X = self.matrix(X)
        self.y = list(y)

    def predict(self, X):
        return [f.tree_predict(self.X, self.y, x, DEPTH) for x in self.matrix(X)]
