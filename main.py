import os

import tornado.ioloop
import tornado.web
import tornado.httpserver
import pymongo
import numpy as np
from bson.objectid import ObjectId
import json

client = pymongo.MongoClient()
db = client.tsmi


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/run", RunHandler)
        ]

        settings = dict(
            debug=True,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            cookie_secret="Settings.COOKIE_SECRET",
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        runs = list(db.runs.find())
        self.render("index.html", runs=runs)

    def post(self):
        raw = self.get_argument("data", None)
        time = self.get_argument("time", None)

        meta = raw.split("\r\n")[:5]

        data = "".join(raw.split("\r\n")[8:])
        M = np.fromstring(data, sep="\t").reshape(-1, 13)

        # Metropolis results
        out = dict(
            zone=[map(float, x.replace("(", "").replace(")", "").split(';')) for x in meta[1].split(" ")],
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
        db.runs.insert(out)
        self.write("hello")


class RunHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("run.html")

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

        out = dict(
            deltas=deltas,
            histogram=dict(
                data=hist[0].tolist(),
                max=max(tmp),
                step=step
            )
        )
        self.write(json.dumps(out))


if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8080)
    tornado.ioloop.IOLoop.current().start()
