"""Reference solution: the single neuron, platform steps 11-18.
Linear output; the bias is the last weight w[n], with input 1."""


def scale(value, lo, hi):
    return (value - lo) / (hi - lo)


def output(x, w):
    total = 0
    for i in range(len(x)):
        total = total + x[i] * w[i]
    return total + 1 * w[len(x)]


def error(target, out):
    return target - out


def update(x, w, lr, err):
    new_w = []
    for i in range(len(x)):
        new_w.append(w[i] + lr * err * x[i])
    new_w.append(w[len(x)] + lr * err * 1)
    return new_w


def epoch(X, Y, w, lr):
    for r in range(len(X)):
        err = error(Y[r], output(X[r], w))
        w = update(X[r], w, lr, err)
    return w


def train(X, Y, lr, epochs):
    w = []
    for i in range(len(X[0]) + 1):
        w.append(0)
    for e in range(epochs):
        w = epoch(X, Y, w, lr)
    return w


def velocity(x, v, lr, err, momentum):
    new_v = []
    for i in range(len(x)):
        new_v.append(momentum * v[i] + lr * err * x[i])
    new_v.append(momentum * v[len(x)] + lr * err * 1)
    return new_v


def train_momentum(X, Y, lr, epochs, momentum):
    w = []
    v = []
    for i in range(len(X[0]) + 1):
        w.append(0)
        v.append(0)
    for e in range(epochs):
        for r in range(len(X)):
            err = error(Y[r], output(X[r], w))
            v = velocity(X[r], v, lr, err, momentum)
            new_w = []
            for i in range(len(w)):
                new_w.append(w[i] + v[i])
            w = new_w
    return w
