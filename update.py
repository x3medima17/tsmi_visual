import plot
import sys

def filt(item):
    return filter(lambda x: item["data"]["iters"] > 50, item).next()


if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [filt])
else:
    plot.StatsBuilder.update()
