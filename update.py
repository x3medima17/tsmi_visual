import plot
import sys

def filt(item):
    item = filter(lambda x: item["data"]["iters"] > 50, item)
    return item

if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [filt])
else:
    plot.StatsBuilder.update()
