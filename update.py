import plot
import sys

def filt(item):
    item["data"]["iters"] = list(filter(lambda x: item["data"]["iters"] > 50, item["data"]["iters"]))
    return item

if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [filt])
else:
    plot.StatsBuilder.update()
