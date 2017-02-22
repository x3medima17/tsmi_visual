from functools import reduce

import matplotlib as mpl
mpl.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
from bson.objectid import ObjectId
from pprint import pprint
import sys
import pymongo
from matplotlib.colors import LogNorm
import matplotlib.animation as animation
from collections import Counter
import os
import shutil
import gridfs
import fractions
import gc
import tqdm

import multiprocessing as mp
from pylab import rcParams

import operator

WIDTH = 53
HEIGHT = 20
rcParams['figure.figsize'] = WIDTH, HEIGHT
rcParams.update({'font.size': 26})


def connect():
    client = pymongo.MongoClient()
    db = client.tsmi
    fs = gridfs.GridFS(db)
    return db, fs


class StatsBuilder(object):
    def __init__(self, id, filters=[]):

        """
        filters [ (function) ]
        """
        self.db, self.fs = connect()
        self.id = id
        self.oid = ObjectId(id)
        self.item = self.db.runs.find_one({"_id": self.oid})
        if not self.item:
            print("Fetch failed")

        self.figures = dict()

        # applying filters
        accepted = [ set(range(len(self.item["data"]["iters"]))) ]
        for fil in filters:
            accepted.append(fil(self.item))

        accepted = reduce(lambda x,y : x & y, accepted)
        print(accepted)
        for key, value in self.item["data"].items():
            if key == "positions":
                value = list(map(list, zip(*value)))

            zipped = [(i,x) for i,x in enumerate(value) if i in accepted]
            out = zip(*zipped)
            # print(key,"--------------------",zipped)
            try:
                if key == "positions":
                    out = list(map(list, zip(*out)))
                _, self.item["data"][key] = out
            except ValueError:
                print(value)
                print(zipped)
                print(key)
                print([(i,x) for i,x in enumerate(value)])
                # raise ValueError
            print(key)
            # print(self.item)
            # print(self.item["data"]["iters"])


    def plot_main(self):

        deltas = self.item["data"]["delta"]

        fig = plt.figure()
        fig.canvas.set_window_title("Main")

        ax = plt.subplot(121)
        iters = self.item["data"]["iters"]
        ax.plot(iters, deltas)

        ax.set_xlabel("Iteration")
        ax.set_ylabel("Value")
        ax.set_yscale('linear')
        ax.set_title('Delta')
        ax.grid(True)

        ax = plt.subplot(122)

        ax.hist(deltas, 50)  # bins=np.arange(min(deltas), max(deltas), 0.1))
        ax.set_title('Delta hist')

        ax.set_xlabel("Value")
        ax.set_ylabel("Occurence")
        ax.grid(True)
        plt.tight_layout()

        self.figures["main"] = [fig]

    # plt.savefig("{}/main.png".format(path))

    def get_param_dict(self):
        """
            Example
            {
                'k_perm' : {
                        '<formation>' : <index>,
                    },
                'p_i_red' : {
                        '<formation>' : <index>,
                    }
            }
        """
        params = {}
        info = self.item["meta"]["param_info"]
        for i, item in enumerate(info):
            if not item[1] in params.keys():
                params[item[1]] = {}
            params[item[1]][item[0]] = i
        return params

    def get_formation_dict(self):
        """
            Example
            {
                '1' : {
                        'k_perm' : <index>,
                        'p_i_red': <index>
                      },
            }
        """
        formations = {}
        info = self.item["meta"]["param_info"]

        for i, item in enumerate(info):
            if not item[0] in formations.keys():
                formations[item[0]] = dict()
            formations[item[0]][item[1]] = i
        return formations

    def plot_paths(self):
        formations = self.get_formation_dict()

        figs = []
        item = self.item
        nRows, nCols = self.factorize2(len(formations.keys()))
        fig = plt.figure(figsize=(WIDTH, HEIGHT / 2))
        i = 0
        for key, value in formations.items():
            i += 1
            ax = fig.add_subplot(nRows, nCols, i)
            x = item["data"]["positions"][value["k_perm"]]
            y = item["data"]["positions"][value["p_i_red"]]
            ax.plot(x, y, "ro")  # bins=np.arange(min(deltas), max(deltas), 0.1))
            ax.set_title('f{}'.format(key + 1))
            ax.grid(True)

            ax.set_xlabel("{}{}".format(list(value.keys())[0][0], key + 1))
            ax.set_ylabel("{}{}".format(list(value.keys())[1][0], key + 1))
            plt.xticks(rotation=70)
            plt.yticks(rotation=70)
        # plt.set_fontsize(20)
        plt.tight_layout()
        figs.append(fig)

        self.figures["paths"] = figs

    def plot_positions(self):
        figs = []
        item = self.item
        params = self.get_param_dict()
        nRows = len(params.keys())
        nCols = max([len(x) for x in params.values()])
        fig = plt.figure()
        i = 1
        for param, value in params.items():
            for form_index, index in value.items():
                ax = plt.subplot(nRows, nCols, i)
                ax.ticklabel_format(style='sci', axis='y')

                x = self.item["data"]["iters"]

                y = item["data"]["positions"][index]
                ax.plot(x, y)
                ax.set_title("{}{}".format(param[0], form_index + 1))

                ax.grid(True)
                ax.set_xlabel("Iteration")
                # ax.set_ylabel("{}{}".format(param[0], form_index+1))


                plt.yticks(rotation=50)
                i += 1

        plt.tight_layout()
        figs.append(fig)

        self.figures["positions"] = figs
        figh = plt.figure()
        i = 1
        for param, value in params.items():
            for form_index, index in value.items():
                ax = plt.subplot(nRows, nCols, i)
                # ax.ticklabel_format(st)
                vals = item["data"]["positions"][index]

                ax.hist(vals, 50)  # bins=np.arange(min(deltas), max(deltas), 0.1))
                ax.set_title("{}{} hist".format(param[0], form_index + 1))

                ax.set_xlabel("Value")
                ax.set_ylabel("Occurence")
                ax.grid(True)
                plt.yticks(rotation=50)
                plt.xticks(rotation=50)
                i += 1

        plt.tight_layout()
        self.figures["positions_hists"] = [figh]

    def plot_freq(self, bins=10):

        formations = self.get_formation_dict()

        figs = []
        item = self.item
        nRows, nCols = self.factorize2(len(list(formations.keys())))
        fig = plt.figure(figsize=(WIDTH, HEIGHT / 2))
        i = 1
        for key, value in formations.items():
            ax = fig.add_subplot(nRows, nCols, i)
            x = item["data"]["positions"][value[list(value.keys())[0]]]
            y = item["data"]["positions"][value[list(value.keys())[1]]]

            plt.hist2d(x, y, bins=bins, norm=LogNorm())
            plt.colorbar()

            ax.set_title('f{}'.format(key + 1))
            # fig.canvas.set_window_title('Formation {} frequency'.format(key+1))
            ax.grid(True)

            ax.set_xlabel("{}{}".format(list(value.keys())[0][0], key + 1))
            ax.set_ylabel("{}{}".format(list(value.keys())[1][0], key + 1))

            ax = self.set_fontsize(ax, 18)
            plt.xticks(rotation=50)
            plt.yticks(rotation=50)
            i += 1

        plt.tight_layout()
        figs.append(fig)

        self.figures["frequ"] = figs

    def plot_accepted_stats(self):
        item = self.item
        N = len(item["data"]["positions"])

        accepted = np.array(item["data"]["accepted"])
        param_indexes = np.array(item["data"]["param_index"]) + 1

        accepted_only = filter(lambda x: x != 0, param_indexes * accepted)
        dropped_only = filter(lambda x: x != 0, param_indexes * ((accepted - 1) * -1))

        count_accepted = dict(Counter(accepted_only))
        count_dropped = dict(Counter(dropped_only))
        for i in range(1, N + 1):
            if i not in count_accepted.keys():
                count_accepted[i] = 0
            if i not in count_dropped.keys():
                count_dropped[i] = 0

        accepted = count_accepted.values()

        ind = np.arange(N)  # the x locations for the groups
        width = 0.35  # the width of the bars

        fig, ax = plt.subplots()

        rects1 = ax.bar(ind, accepted, width, color='y')

        dropped = count_dropped.values()
        rects2 = ax.bar(ind + width, dropped, width, color='r')

        # add some text for labels, title and axes ticks
        ax.set_ylabel('Points')
        ax.set_title('Accepted and dropped points by parameter')
        info = self.item["meta"]["param_info"]
        ax.set_xticks(ind + width / 2)
        labels = []
        for item in info:
            labels.append("{}{}".format(item[1][:1], item[0] + 1))
        # labels.append("")
        ax.set_xticklabels(labels, ha='left')
        # fig.subplots_adjust(hspace=-0.5)

        ax.legend((rects1[0], rects2[0]), ('Accepted', 'Dropped'))

        def autolabel(rects):
            """
            Attach a text label above each bar displaying its height
            """
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width() / 2., 1.00 * height,
                        '%d' % int(height),
                        ha='center', va='bottom')

        autolabel(rects1)
        autolabel(rects2)

        self.figures["accepted_stats"] = [fig]

    # sys.exit()
    # plt.savefig("{}/accepted.png".format(path))

    @staticmethod
    def set_fontsize(ax, size):
        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
            label.set_fontsize(size)  # Size here overrides font_prop
        return ax

    @staticmethod
    def factorize2(n):
        sol = [1, n]
        for i in range(1, int(np.sqrt(n) + 1)):
            if n % i == 0 and (i - n / i) ** 2 < (sol[0] - sol[1]) ** 2:
                sol = [i, n / i]
        return sol

    def plot_positions_hists(self):
        N = len(self.item["data"]["positions"])
        w, h = self.factorize2(N)

        fig = plt.figure()
        qq = 0
        for i in range(1, w + 1):
            for j in range(1, h + 1):
                vals = self.item["data"]["positions"][qq]
                info = self.item["meta"]["param_info"][qq]
                qq += 1
                ax = plt.subplot(w * 100 + h * 10 + qq)
                ax.hist(vals, 50)  # bins=np.arange(min(deltas), max(deltas), 0.1))
                ax.title('Formation {} {} hist'.format(info[0], info[1]))
                ax.grid(True)
                ax = StatsBuilder.set_fontsize(ax, 18)
        self.figures["positions_hists"] = fig

    def plot_field_line(self, field):
        fig = plt.figure()
        ax = plt.subplot(111)
        data = self.item["data"][field]
        plt.plot(self.item["data"]["iters"], data)
        ax.set_xlabel("Iteration")
        ax.set_ylabel(field)

        ax.set_title(field)
        plt.grid(True)

    def plot_field_hist(self, field, bins=20):
        fig = plt.figure()
        plt.subplot(111)
        data = self.item["data"][field]
        plt.hist(data, bins)
        plt.title(field)
        plt.grid(True)

    def plot_all(self):
        self.plot_main()
        self.plot_paths()
        self.plot_positions()
        self.plot_freq()
        self.plot_accepted_stats()

    def show(self):
        plt.show()

    def insert(self):
        figs = self.figures

        self.path = "/tmp/tsmi/{}".format(self.id)
        oid = ObjectId(self.id)
        path = self.path
        try:
            shutil.rmtree(path)
        except:
            pass

        os.makedirs(self.path)

        dtime = self.item["meta"]["time"]
        for key, value in figs.items():
            for i, item in enumerate(value):
                if len(value) > 1:
                    fname = "{}/{}{}_{}.png".format(path, key, i, dtime)
                else:
                    fname = "{}/{}_{}.png".format(path, key, dtime)
                fname = fname.replace(":", "-")
                item.savefig(fname)
                item.clf()
                hx = ":".join("{:02x}".format(ord(c)) for c in fname)
                # print(hx)
        # figs["main"].savefig("/tmp/main.png")


        shutil.make_archive("/tmp/tsmi/out{}".format(self.id), 'zip', path)
        zip = open("/tmp/tsmi/out{}.zip".format(self.id), "rb").read()
        with self.fs.new_file(filename="{}.zip".format(oid)) as fb:
            fb.write(zip)

        plt.clf()
        shutil.rmtree(path)
        os.remove("/tmp/tsmi/out{}.zip".format(self.id))

    @staticmethod
    def reset():
        # fs.chunks.remove({})
        # fs.files.remove({})
        db, fs = connect()
        db['fs.chunks'].remove({})
        db['fs.files'].remove({})

    @staticmethod
    def update(oid = None, filters=[]):
        StatsBuilder.reset()
        db, fs = connect()
        if oid:
            lst = list(db.runs.find({"_id" : ObjectId(oid)}))
        else:
            lst = list(db.runs.find({}, {"_id": 1}))

        for item in tqdm.tqdm(lst):
            p = mp.Process(target=StatsBuilder.worker, args=(item["_id"], filters,))
            p.start()
            p.join()

    @staticmethod
    def worker(oid, filters):
        db, fs = connect()
        obj = StatsBuilder(oid, filters)
        obj.plot_all()
        obj.insert()

    def __del__(self):
        plt.close()
        gc.collect()


if __name__ == "__main__":

    db, fs = connect()
    lst = list(db.runs.find())
    i = 0
    for item in tqdm.tqdm(lst):
        i += 1
        oid = str(item["_id"])
        try:
            obj = StatsBuilder("5894455af7478630fb2f04b9")
            obj.plot_all()
            obj.insert()
        except:
            print("Failed")
