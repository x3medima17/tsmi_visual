import plot
import sys

def filt_iter(item):
    s = set()
    for i, item in enumerate(item["data"]["iters"]):
        if  item > 5:
            s |= {i}
    return s

def filt_delta(item):
    s = set()
    for i, item in enumerate(item["data"]["delta"]):
        if item < 0.000035:
            s |= {i}
    return s

if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [filt_iter, filt_delta])
else:
    plot.StatsBuilder.update()
