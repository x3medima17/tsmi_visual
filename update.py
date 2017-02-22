import plot
import sys


def filt_iter(item):
    s = set()
    for i, item in enumerate(item["data"]["iters"]):
        if item > 5:
            s |= {i}
    return s


def filt_delta(item):
    s = set()
    for i, item in enumerate(item["data"]["delta"]):
        if item <= 20.42923143809969:
            s |= {i}
    return s


def factory(field, min, max):
    def fil(item):
        s = set()
        for i, item in enumerate(item["data"][field]):
            if item >= min and item <= max:
                s |= {i}
        return s
    return fil


if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [factory("iters", 0,5)])
else:
    plot.StatsBuilder.update()
