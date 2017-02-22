import plot
import sys

if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1])
else:
    plot.StatsBuilder.update()
