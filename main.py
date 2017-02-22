import os

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.options

import pymongo
import numpy as np
from bson.objectid import ObjectId
import json
import time as timee
import gridfs
import plot
import multiprocessing as mp
from subprocess import Popen

client = pymongo.MongoClient()
db = client.tsmi
fs = gridfs.GridFS(db)

tornado.options.parse_command_line()


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/run", RunHandler),
            (r"/plot", PlotHandler),
            (r"/get_fields", GetFieldsHander),

            (r"/deltas", DeltasHandler),
            (r"/histogram", HistogramHandler),
            (r"/paths", PathsHandler),
            (r"/download/json", DownloadHandler.JSONDownloadHandler),
            (r"/download/tab", DownloadHandler.TabDownloadHandler),
            (r"/download/zip", DownloadHandler.ZipDownloadHandler),

            (r"/hook", HookHandler),
        ]

        settings = dict(
            debug=True,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="Settings.COOKIE_SECRET",
            compress_response=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class HookHandler(tornado.web.RequestHandler):
    def post(self):
        print(self.request.body)
        Popen("cd /root/tsmi_visual && git pull origin master", shell=True)


class DownloadHandler(tornado.web.RequestHandler):
    class JSONDownloadHandler(tornado.web.RequestHandler):
        def get(self):
            id = self.get_argument("id", None)
            mid = ObjectId(id)
            item = db.runs.find_one({"_id": mid}, {"_id": 0})
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename=%s.json' % item["meta"]["time"])
            self.write(json.dumps(item))

    class ZipDownloadHandler(tornado.web.RequestHandler):
        def get(self):
            id = self.get_argument("id", None)
            zip = fs.get_last_version('{}.zip'.format(id)).read()
            mid = ObjectId(id)
            item = db.runs.find_one({"_id": mid}, {"_id": 0})
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename=%s.zip' % item["meta"]["time"])
            self.write(zip)

    class TabDownloadHandler(tornado.web.RequestHandler):
        def get(self):
            id = self.get_argument("id", None)
            mid = ObjectId(id)
            item = db.runs.find_one({"_id": mid}, {"_id": 0})
            doc = item
            header = ["iters", "param_index", "param_name", "Ha", "S0", "new_value", "acceptance_probability",
                      "random_probability", "accepted", "positions", "delta"]
            out = ""
            data = item["data"]
            meta = item["meta"]

            m = len(data["delta"])
            for key in data.keys():
                if not key in header:
                    header.append(key)
            out += "\t".join(header) + "\n"
            for i in range(m):
                for key in header:
                    if key == "param_name":
                        curr = meta["param_info"][data["param_index"][i]]
                        out += "{1}{0}\t".format(curr[0] + 1, curr[1][0])
                        continue
                    if key == "positions":
                        out += "[ "
                        for item in data[key]:
                            out += str(item[i]) + " "
                        out += "]\t"
                    else:
                        out += str(data[key][i]) + "\t"
                out += "\n"

            print("aaaaaaaaaaaaaaa\n\n\naaaaaaaaaaa")
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename=%s.tab' % doc["meta"]["time"])
            self.write(out)


class GetFieldsHander(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument("id")
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})
        self.write(json.dumps(item["data"].keys()))


class PlotHandler(tornado.web.RequestHandler):
    def get(self):
        field = self.get_argument("field")
        id = self.get_argument("id")
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})
        self.write(json.dumps(item["data"][field]))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        runs = list(db.runs.find())
        self.render("index.html", runs=runs)

    def post(self):
        # print(self.request.body)
        req = json.loads(self.request.body)
        data = req["data"]
        meta = req["meta"]

        required = ["iters", "param_index", "Ha", "S0", "new_value", "acceptance_probability", "random_probability",
                    "accepted", "positions", "delta"]
        for item in required:
            if not item in data.keys():
                raise Exception("%s missing" % item)
        m = len(data["S0"])
        for key, value in data.items():
            if key == "positions":
                for item in value:
                    if len(item) != m:
                        raise Exception("Wrong size in positions %s vs %s" % (m, len(item)))
            else:
                if len(value) != m:
                    raise Exception("Wrong size in %s, %s vs %s" % (key, m, len(value)))
        f = open("/var/www/html/tsmi/%s.tab" % meta["time"], "w")
        header = required
        for key in data.keys():
            if not key in header:
                header.append(key)
        f.write("\t".join(header) + "\n")
        for i in range(m):
            for key in header:
                if key == "positions":
                    f.write("[ ")
                    for item in data[key]:
                        f.write(str(item[i]) + " ")
                    f.write("]\t")
                else:
                    f.write(str(data[key][i]) + "\t")
            f.write("\n")
        req["meta"]["min_delta"] = min(data["delta"])
        oid = db.runs.insert(req)

        def worker(oid):
            obj = plot.StatsBuilder(oid)
            obj.plot_all()
            obj.insert()

        p = mp.Process(target=worker, args=(oid,))
        p.start()
        p.join()
        print("OK!!")


class DeltasHandler(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument("id", None)
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})
        deltas = item["delta"]
        self.write(json.dumps(deltas))


class HistogramHandler(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument("id", None)
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})

        deltas = item["data"]["delta"]
        hist = np.histogram(deltas, 300)
        tmp = hist[1].tolist()
        step = 0
        if len(tmp) > 1:
            step = tmp[1] - tmp[0]

        out = dict(
            data=hist[0].tolist(),
            max=max(tmp),
            step=step
        )

        self.write(json.dumps(out))


class PathsHandler(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument("id", None)
        if not id:
            self.write("no id")
            return
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})

        x1 = item["data"]["positions"][0]
        y1 = item["data"]["positions"][1]

        x2 = item["data"]["positions"][2]
        y2 = item["data"]["positions"][3]

        out = [
            dict(
                data=np.array([x1, y1]).transpose().tolist(),  # [x1.tolist(), x2.tolist()],
                maxx=max(x1),
                maxy=max(y1),
                minx=min(x1),
                miny=min(y1)
            ),
            dict(
                data=np.array([x2, y2]).transpose().tolist(),  # [x1.tolist(), x2.tolist()],
                maxx=max(x2),
                maxy=max(y2),
                minx=min(x2),
                miny=min(y2)
            )
        ]
        self.write(json.dumps(out))


class RunHandler(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument("id", None)
        if not id:
            self.write("no id")
            return
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})

        out = dict(
            min_delta=item["meta"]["min_delta"],
            s0=item["meta"]["S0"],
            m=item["meta"]["m"],
            total_samples=len(item["data"]["delta"]),
            accepted=item["data"]["accepted"].count(True),
            health=0,
            time=item["meta"]["time"]
        )
        self.render("run.html", **out)

    def post(self):
        id = self.get_argument("id", None)
        if not id:
            self.write("no id")
            return
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})
        A = np.array(item["list_of_lists"])
        deltas = A[:, 12].tolist()
        hist = np.histogram(A[:, 12], 300)

        tmp = hist[1].tolist()
        step = 0
        if len(tmp) > 1:
            step = tmp[1] - tmp[0]

        x1 = A[:, 8]
        y1 = A[:, 9]

        x2 = A[:, 10]
        y2 = A[:, 11]

        paths = [A[:, 8:10].tolist(), A[:, 10:12].tolist()]
        out = dict(

        )
        self.write(json.dumps(out))


if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8080)
    tornado.ioloop.IOLoop.current().start()
