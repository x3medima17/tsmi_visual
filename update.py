import plot
import sys

def filt(item):
    return list(filter(lambda x: item["data"]["iters"] > 50, item))[0]


if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [filt])
else:
    plot.StatsBuilder.update()
