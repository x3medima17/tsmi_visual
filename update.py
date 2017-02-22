import plot
import sys

def filt(item):
    s = set()
    for i, item in enumerate(item["data"]["iters"]):
        if  item > 50:
            s |= {i}
    return s

if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [filt])
else:
    plot.StatsBuilder.update()
