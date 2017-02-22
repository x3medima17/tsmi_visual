import plot
import sys

def filt(item):
    s = set(item["data"]["iters"])
    for i, item in item["data"]["iters"]:
        if not (item>50):
            s -= {item}
    return s

if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [filt])
else:
    plot.StatsBuilder.update()
