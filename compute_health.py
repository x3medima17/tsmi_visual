
import pymongo
import numpy as np
from bson.objectid import ObjectId
import json

client = pymongo.MongoClient()
db = client.tsmi

gamma = 1

cursor = db.runs.find()
for item in cursor:
	M = np.array(item["list_of_lists"])
	deltas = M[:,12]
	dmax = max(deltas)
	dmin = min(deltas)
	alpha = item["accepted"]*1.0/ item["total_samples"]
	stdev = np.std(deltas)

	a = 1 - dmin
	b = (1-alpha**2)
	c = 1 - np.mean(deltas)
	print(a,b,c)
	health = a + b + c
	health /= 3
	item["health"] = health
	db.runs.save(item)