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


def factory(field:str, min:float , max:float, context:tuple = None):
    #context: <formation, param>
    def fil(item):
        s = set()

        enum = item["data"][field]
        if context:
            info = plot.StatsBuilder.get_formation_dict(item)
            enum = enum[info[context[0]][context[1]]]

        for i, item in enumerate(enum):
            if item >= min and  item <= max:
                s |= {i}
        return s

    return fil


if len(sys.argv) == 2:
    plot.StatsBuilder.update(sys.argv[1], [
        # factory("iters", 0, 500),
        factory("positions",0,0.002, (0,"k_perm"))
    ])
else:
    plot.StatsBuilder.update()
