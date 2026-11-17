"""Reference solution: Pearson's r, the same functions as the LNN platform's
Habit Arena steps 1-10. Population formulas (divide by n)."""


def mean(xs):
    total = 0
    for x in xs:
        total = total + x
    return total / len(xs)

def deviations(xs):
    m = mean(xs)
    result = []
    for x in xs:
        result.append(x - m)
    return result

def covariance(xs, ys):
    dx = deviations(xs)
    dy = deviations(ys)
    products = []
    for i in range(len(xs)):
        products.append(dx[i] * dy[i])
    return mean(products)

def std(xs):
    return covariance(xs, xs) ** 0.5

def pearson(xs, ys):
    return covariance(xs, ys) / (std(xs) * std(ys))

def strength(xs, ys):
    return abs(pearson(xs, ys))

def safe_strength(xs, ys):
    if std(xs) == 0:
        return -1
    if std(ys) == 0:
        return -1
    return strength(xs, ys)

def best_column(columns, ys):
    best = -1
    best_strength = -1
    for c in range(len(columns)):
        s = safe_strength(columns[c], ys)
        if s > best_strength:
            best = c
            best_strength = s
    return best

def slope(xs, ys):
    return pearson(xs, ys) * std(ys) / std(xs)

def line_predict(x, xs, ys):
    return mean(ys) + slope(xs, ys) * (x - mean(xs))
