
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
import matplotlib as mpl
mpl.use('Agg')


client = pymongo.MongoClient()
db = client.tsmi
fs = gridfs.GridFS(db)



def build_stats(oid):
	path = "/tmp/tsmi/{}".format(oid)

	try:
		shutil.rmtree(path)
	except:
		pass

	os.makedirs(path)
	id = ObjectId(oid)



	item = db.runs.find_one({"_id" : id})
	# pprint(item["data"].keys())	
	deltas = item["data"]["delta"]

	plt.figure()
	plt.subplot(121)
	plt.plot(range(1,len(deltas)+1), deltas)
	plt.yscale('linear')
	plt.title('Delta')
	plt.grid(True)



	plt.subplot(122)

	plt.hist(deltas, 50)# bins=np.arange(min(deltas), max(deltas), 0.1))
	plt.title('Delta hist')
	plt.grid(True)

	plt.savefig("{}/main.png".format(path))       


	N = len(item["data"]["positions"])
	assert N%2 == 0
	qq = 0
	for i in range(N/2):
		qq += 1
		plt.figure()
		plt.subplot(111)

		x = item["data"]["positions"][2*i]
		y = item["data"]["positions"][2*i+1]

		plt.plot(x, y, "ro")# bins=np.arange(min(deltas), max(deltas), 0.1))
		plt.title('Path '+ str(qq))
		plt.grid(True)
		plt.savefig("{}/path{}.png".format(path, qq))    
	       


		plt.figure()
		plt.subplot(121)
		plt.plot(range(1,len(x)+1), x)
		plt.title('Param {}'.format((qq-1)*2 +1))
		plt.grid(True)

		plt.subplot(122)
		plt.plot(range(1,len(y)+1), y)
		plt.title('Param {}'.format((qq-1)*2 +2))
		plt.grid(True)
	       

		plt.savefig("{}/positions{}.png".format(path,qq))       


		plt.figure()
		plt.subplot(111)
		plt.hist2d(x, y, bins=100, norm=LogNorm())
		plt.colorbar()

		plt.savefig("{}/shoot_freq{}.png".format(path,qq))       



	# plt.figure()
	# ax = fig.add_subplot(111)

	# fig, (ax1, ax2) = plt.subplots(1,2)

	# line1,  = ax1.plot(x1,y1, "ro")
	# line2,  = ax2.plot(x2,y2, "bo")
	# line = [line1, line2]

	# ax1.grid(True)
	# ax2.grid(True)

	# def animate(i):
	# 	x = x1[:i]
	# 	y = y1[:i]
	# 	line[0].set_data(x, y)
	# 	x = x2[:i]
	# 	y = y2[:i]
	# 	line[1].set_data(x, y)

	# 	return line

	# # Init only required for blitting to give a clean slate.
	# def init():
	# 	# print(len(x1))
	# 	line[0].set_data(np.ma.array([x1, y1], mask=True))
	# 	line[1].set_data(np.ma.array([x2, y2], mask=True))
	# 	return line

	# ani = animation.FuncAnimation(fig, animate, np.arange(0, len(y1)), init_func=init,
	#                               interval=10, blit=True, repeat=False)


	N = len(item["data"]["positions"])

	accepted = np.array(item["data"]["accepted"])
	param_indexes = np.array(item["data"]["param_index"]) + 1

	accepted_only = filter(lambda x: x != 0, param_indexes * accepted)
	dropped_only = filter(lambda x: x != 0, param_indexes * ((accepted - 1) * -1))

	count_accepted = dict(Counter(accepted_only))
	count_dropped = dict(Counter(dropped_only))
	for i in range(1, N+1):
		if i not in count_accepted.keys():
			count_accepted[i] = 0
		if i not in count_dropped.keys():
			count_dropped[i] = 0
			
	# print(dropped_only, accepted_only,accepted)

	# print(count_accepted, count_dropped)
	# print(len(item["data"]["accepted"]), sum(count_accepted.values()) + sum(count_dropped.values()))
	# N = len(count_accepted.keys())
	# N = 5
	accepted = count_accepted.values()
	pprint(count_accepted)
	ind = np.arange(N)  # the x locations for the groups
	width = 0.35       # the width of the bars

	fig, ax = plt.subplots()
	print(ind, accepted)
	rects1 = ax.bar(ind, accepted, width, color='r')

	dropped = count_dropped.values()
	print(ind+width, dropped, width)
	rects2 = ax.bar(ind + width, dropped, width, color='y')

	# add some text for labels, title and axes ticks
	ax.set_ylabel('Points')
	ax.set_title('Accepted and dropped points by parameter')
	ax.set_xticks(ind + width / 2)
	ax.set_xticklabels(["Param {}".format(x) for x in range(1,N+1)])

	ax.legend((rects1[0], rects2[0]), ('Accepted', 'Dropped'))


	def autolabel(rects):
	    """
	    Attach a text label above each bar displaying its height
	    """
	    for rect in rects:
	        height = rect.get_height()
	        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
	                '%d' % int(height),
	                ha='center', va='bottom')

	autolabel(rects1)
	autolabel(rects2)

	# sys.exit()
	plt.savefig("{}/accepted.png".format(path))       
	
	shutil.make_archive("/tmp/tsmi/out".format(path), 'zip', path)
	zip = open("/tmp/tsmi/out.zip", "rb").read()
	with fs.new_file(filename="{}.zip".format(oid)) as fb:
		fb.write(zip)

	plt.clf()
	shutil.rmtree(path)
	os.remove("/tmp/tsmi/out.zip")
	# plt.show()

if __name__ == "__main__":
	build_stats("5876b835f74786316bd909d9")
	sys.exit()
	lst = list(db.runs.find())
	print len(lst)
	i = 0
	for item in lst:
		i+=1
		print(i)
		oid = str(item["_id"])
		print(oid)
		build_stats(oid)