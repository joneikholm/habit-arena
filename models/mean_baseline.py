"""Mean baseline: predicts the average target so far. The floor every model must
beat. Paste your `mean` function from the LNN platform (exercise 1) between the
two lines below.

Until you paste, the model uses reference/mean_baseline.py if your teacher gave you
one, and otherwise waits for your code."""
from models.base import Model, load_code

# ---- PASTE YOUR FUNCTIONS FROM THE LNN PLATFORM BELOW ----


# ---- END ----

NEEDED = ["mean"]
f, SOURCE = load_code(__name__, globals(), NEEDED)


class MeanBaseline(Model):
    name = "Mean baseline"
    min_days = 1
    ready = f is not None
    source = SOURCE

    def fit(self, X, y):
        self.avg = f.mean(y)

    def predict(self, X):
        return [self.avg for _ in X]
