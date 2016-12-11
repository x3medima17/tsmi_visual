import os

import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.options


import pymongo
import numpy as np
from bson.objectid import ObjectId
import json

client = pymongo.MongoClient()
db = client.tsmi


tornado.options.parse_command_line()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/run", RunHandler),
            (r"/deltas", DeltasHandler),
            (r"/histogram", HistogramHandler),
            (r"/paths",PathsHandler)
        ]

        settings = dict(
            debug=True,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="Settings.COOKIE_SECRET",
            compress_response=True
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        runs = list(db.runs.find())
        self.render("index.html", runs=runs)

    def post(self):
        print(self.request.body)
    	req = json.loads(self.request.body)
    	raw = req["data"]
        time = req["time"]

        meta = raw.split("\n")[:5]

        data = "".join(raw.split("\n")[8:])
        M = np.fromstring(data, sep="\t").reshape(-1, 13)
        deltas = M[:,12]
        
        # Metropolis results
        out = dict(
            zone=[map(float, x.replace("(", "").replace(")", "").split(';')) for x in meta[1].strip().split(" ")],
            m=float(meta[2].split(":")[1]),
            s0=float(meta[3].split(":")[1]),
            max_iters=int(meta[4].split(":")[1]),
            min_delta=min(M[:, 12]),
            accepted=int(sum(M[:, 7])),
            total_samples=M.shape[0],
            list_of_lists=M.tolist(),
            raw=raw,
            time=time,
        )
        dmax = max(deltas)
        dmin = min(deltas)
        alpha = out["accepted"]*1.0/ out["total_samples"]
        stdev = np.std(deltas)
        a = 1 - dmin
        b = (1-alpha**2)
        c = 1 - np.mean(deltas)
        health = a + b + c
        health /= 3

        out["health"] = health
        db.runs.insert(out)
        self.write("hello")


class DeltasHandler(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument("id", None)
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})
        A = np.array(item["list_of_lists"])
        deltas = A[:, 12].tolist()
        self.write(json.dumps(deltas))

class HistogramHandler(tornado.web.RequestHandler):
    def get(self):
        id = self.get_argument("id", None)
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})
        A = np.array(item["list_of_lists"])
        deltas = A[:, 12].tolist()
        hist = np.histogram(A[:, 12],300)
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
        A = np.array(item["list_of_lists"])
       
       
        x1 = A[:,8]
        y1 = A[:,9]
        
        x2 = A[:,10]
        y2 = A[:,11]

        paths = [A[:,8:10].tolist(), A[:,10:12].tolist()]
        out =  [
                    dict(
                        data = np.array([x1,y1]).transpose().tolist(),#[x1.tolist(), x2.tolist()],
                        maxx = max(x1),
                        maxy = max(y1),
                        minx = min(x1),
                        miny = min(y1)
                        ),
                    dict(
                        data = np.array([x2,y2]).transpose().tolist(),#[x1.tolist(), x2.tolist()],
                        maxx = max(x2),
                        maxy = max(y2),
                        minx = min(x2),
                        miny = min(y2)
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
                min_delta=item["min_delta"],
                s0=item["s0"],
                m=item["m"],
                total_samples=item["total_samples"],
                accepted=item["accepted"],
                health=item["health"],
                time=item["time"]
            )
        self.render("run.html",**out)

    def post(self):
        id = self.get_argument("id", None)
        if not id:
            self.write("no id")
            return
        mid = ObjectId(id)
        item = db.runs.find_one({"_id": mid})
        A = np.array(item["list_of_lists"])
        deltas = A[:, 12].tolist()
        hist = np.histogram(A[:, 12],300)

        tmp = hist[1].tolist()
        step = 0
        if len(tmp) > 1:
            step = tmp[1] - tmp[0]

        x1 = A[:,8]
        y1 = A[:,9]
        
        x2 = A[:,10]
        y2 = A[:,11]

        paths = [A[:,8:10].tolist(), A[:,10:12].tolist()]
        out = dict(
                      
        )
        self.write(json.dumps(out))


if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8080)
    tornado.ioloop.IOLoop.current().start()
