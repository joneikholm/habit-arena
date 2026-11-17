"""Single neuron: one weight per prev_ column plus the bias (the last weight,
with input 1). Inputs are scaled to 0..1; the target stays on its own scale.
Paste your functions from the LNN platform (neuron exercises 11-18) between the
two lines below. Paste ALL of them: the ones in NEEDED call the others.

Until you paste, the model uses reference/neuron.py if your teacher gave you
one, and otherwise waits for your code."""
from models.base import Model, load_code

# ---- PASTE YOUR FUNCTIONS FROM THE LNN PLATFORM BELOW ----


# ---- END ----

NEEDED = ["scale", "output", "train_momentum"]
f, SOURCE = load_code(__name__, globals(), NEEDED)

LR = 0.01
EPOCHS = 500
MOMENTUM = 0.9


class NeuronModel(Model):
    name = "Single neuron"
    min_days = 10
    ready = f is not None
    source = SOURCE

    def _scaled(self, X):
        out = []
        for row in self.matrix(X):
            out.append([f.scale(v, *self.ranges[c]) for v, c in zip(row, self.columns)])
        return out

    def fit(self, X, y):
        # weights and momentum start at 0 on every fit (inside train_momentum)
        self.w = f.train_momentum(self._scaled(X), list(y), LR, EPOCHS, MOMENTUM)

    def predict(self, X):
        return [f.output(x, self.w) for x in self._scaled(X)]

    def weights(self):
        """For the bonus exercise: which column pushes the target up or down."""
        return dict(zip(self.columns + ["bias"], self.w))
