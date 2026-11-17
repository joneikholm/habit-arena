"""Reference solution: boosting.

A tree is grown fresh inside each call, so the function takes the training
data plus one new row and returns one number.
- leaf answer: the mean of its targets
- a question: "is column c <= threshold?"; thresholds are midpoints between
  neighbouring different values
- question score: squared error of the yes-group plus the no-group (lower is better)
"""
def _mean(ys):
    return sum(ys) / len(ys)


def _squared_error(ys):
    m = _mean(ys)
    return sum((y - m) ** 2 for y in ys)


def _best_question(X, y, cols):
    best = None   # (score, col, threshold)
    for c in cols:
        values = sorted(set(row[c] for row in X))
        for a, b in zip(values, values[1:]):
            t = (a + b) / 2
            yes = [y[i] for i in range(len(X)) if X[i][c] <= t]
            no = [y[i] for i in range(len(X)) if X[i][c] > t]
            score = _squared_error(yes) + _squared_error(no)
            if best is None or score < best[0]:
                best = (score, c, t)
    return best


def _grow(X, y, depth, pick_cols):
    if depth == 0 or len(y) < 4:
        return _mean(y)
    q = _best_question(X, y, pick_cols(len(X[0])))
    if q is None or q[0] >= _squared_error(y):
        return _mean(y)
    _, c, t = q
    yes = [i for i in range(len(X)) if X[i][c] <= t]
    no = [i for i in range(len(X)) if X[i][c] > t]
    return (c, t,
            _grow([X[i] for i in yes], [y[i] for i in yes], depth - 1, pick_cols),
            _grow([X[i] for i in no], [y[i] for i in no], depth - 1, pick_cols))


def _answer(node, x):
    while isinstance(node, tuple):
        c, t, yes, no = node
        node = yes if x[c] <= t else no
    return node


def _all_cols(n):
    return range(n)


def boost_predict(X, y, x, n_trees, lr, depth):
    """Start guess = mean of y. Each tree is fitted on the current errors, and
    lr of its answer is added to every prediction."""
    start = _mean(y)
    preds = [start] * len(y)
    answer = start
    for _ in range(n_trees):
        errors = [y[i] - preds[i] for i in range(len(y))]
        tree = _grow(X, errors, depth, _all_cols)
        preds = [preds[i] + lr * _answer(tree, X[i]) for i in range(len(y))]
        answer += lr * _answer(tree, x)
    return answer
