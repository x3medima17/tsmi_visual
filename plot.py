
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
import matplotlib as mpl

from pylab import rcParams
rcParams['figure.figsize'] = 15, 10


mpl.use('Agg')


client = pymongo.MongoClient("128.199.148.157")

db = client.tsmi

res = db.authenticate('tsmi', '157359')
fs = gridfs.GridFS(db)

class StatsBuilder(object):
	def __init__(self, id):
		self.id = id
		self.oid = ObjectId(id)
		self.item = db.runs.find_one({"_id" : self.oid})
		if not self.item:
			print("Fetch failed")

		self.figures = dict()

	def plot_main(self):	

		deltas = self.item["data"]["delta"]

		fig = plt.figure()
		fig.canvas.set_window_title("Main")

		ax = plt.subplot(121)
		ax.plot(range(1,len(deltas)+1), deltas)
		
		ax.set_xlabel("Iteration")
		ax.set_ylabel("Value")
		ax.set_yscale('linear')
		ax.set_title('Delta')
		ax.grid(True)


		ax = plt.subplot(122)

		ax.hist(deltas, 50)# bins=np.arange(min(deltas), max(deltas), 0.1))
		ax.set_title('Delta hist')

		ax.set_xlabel("Value")
		ax.set_ylabel("Occurence")
		ax.grid(True)

		self.figures["main"] = [fig]
		# plt.savefig("{}/main.png".format(path))       

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
		
		for key, value in formations.iteritems():
			fig = plt.figure()
			ax = plt.subplot(111)
			x = item["data"]["positions"][value["k_perm"]]
			y = item["data"]["positions"][value["p_i_red"]]
			ax.plot(x, y, "ro")# bins=np.arange(min(deltas), max(deltas), 0.1))
			ax.set_title('Formation {} path'.format(key))
			fig.canvas.set_window_title('Formation {} path'.format(key))
			ax.grid(True)

			ax.set_xlabel('k_perm')
			ax.set_ylabel('p_i_red')


			figs.append(fig)
    
		self.figures["paths"] = figs


	def plot_positions(self):
		figs = []
		item = self.item
		N = len(item["data"]["positions"])
		assert N%2 == 0
		qq = 0
		for i in range(N/2):
			qq += 1
			x = item["data"]["positions"][2*i]
			y = item["data"]["positions"][2*i+1]

			fig = plt.figure()
			plt.subplot(121)
			plt.plot(range(1,len(x)+1), x)
			plt.title('Param {}'.format((qq-1)*2 +1))
			plt.grid(True)

			plt.subplot(122)
			plt.plot(range(1,len(y)+1), y)
			plt.title('Param {}'.format((qq-1)*2 +2))
			plt.grid(True)
			  
			figs.append(fig)

			# plt.savefig("{}/positions{}.png".format(path,qq))       
		self.figures["positions"] = figs


	def plot_freq(self, bins=10):	

		formations = self.get_formation_dict()

		figs = []
		item = self.item
		
		for key, value in formations.iteritems():
			fig = plt.figure()
			ax = plt.subplot(111)
			x = item["data"]["positions"][value["k_perm"]]
			y = item["data"]["positions"][value["p_i_red"]]

			plt.hist2d(x, y, bins=bins, norm=LogNorm())
			plt.colorbar()

			ax.set_title('Formation {} frequency'.format(key))
			fig.canvas.set_window_title('Formation {} frequency'.format(key))
			ax.grid(True)

			ax.set_xlabel('k_perm')
			ax.set_ylabel('p_i_red')

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
		for i in range(1, N+1):
			if i not in count_accepted.keys():
				count_accepted[i] = 0
			if i not in count_dropped.keys():
				count_dropped[i] = 0
				
		accepted = count_accepted.values()
		pprint(count_accepted)
		ind = np.arange(N)  # the x locations for the groups
		width = 0.35       # the width of the bars

		fig, ax = plt.subplots()
		
		rects1 = ax.bar(ind, accepted, width, color='y')

		dropped = count_dropped.values()
		rects2 = ax.bar(ind + width, dropped, width, color='r')

		# add some text for labels, title and axes ticks
		ax.set_ylabel('Points')
		ax.set_title('Accepted and dropped points by parameter')
		# ax.set_xticks(ind + width / 2)
		info = self.item["meta"]["param_info"]
		labels = []
		for item in info:
			labels.append("Frm {} {}".format(item[0], item[1]))
			labels.append("")
		ax.set_xticklabels(labels, ha='left')
		# fig.subplots_adjust(hspace=-0.5)

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

		self.figures["accepted_stats"] = [fig]
		# sys.exit() 
		# plt.savefig("{}/accepted.png".format(path))       

	@staticmethod
	def factorize2(n):
		sol = [1, n]
		for i in range(1,int(np.sqrt(n)+1)):
			if n%i == 0 and (i - n/i)**2 < (sol[0] - sol[1])**2:
				sol = [i, n/i]
		return sol 

	def plot_positions_hists(self):
		N = len(self.item["data"]["positions"])
		print(N)
		w,h = self.factorize2(N)

		fig = plt.figure()
		qq = 0
		for i in range(1, w+1):
			for j in range(1, h+1):
				vals = self.item["data"]["positions"][qq]
				info = self.item["meta"]["param_info"][qq]
				qq+=1
				plt.subplot(w*100 + h*10 + qq)
				plt.hist(vals, 50)# bins=np.arange(min(deltas), max(deltas), 0.1))
				plt.title('Formation {} {} hist'.format(info[0], info[1]))
				plt.grid(True)
		self.figures["positions_hists"] = fig

	def plot_field_line(self, field):
		fig = plt.figure()
		ax = plt.subplot(111)
		data = self.item["data"][field]
		plt.plot(range(1,len(data)+1), data)
		ax.set_xlabel("Iteration")
		ax.set_ylabel(field)

		ax.set_title(field)
		plt.grid(True)

	def plot_field_hist(self, field, bins=20):
		fig = plt.figure()
		plt.subplot(111)
		data = self.item["data"][field]
		plt.hist(data,bins)
		plt.title(field)
		plt.grid(True)


	def plot_all(self):
		self.plot_main()
		self.plot_paths()
		self.plot_positions()
		self.plot_freq()
		self.plot_accepted_stats()


	def show(self):
		plt.show();

	def insert(self):
		figs = self.figures

		self.path = "/tmp/tsmi/{}".format(self.id)
		oid = ObjectId(self.id)
		path = self.path
		try:
			shutil.rmtree(path)
		except:
			print(sys.exc_info()[0])
			pass

		os.makedirs(self.path)
		pprint(figs)
		for key, value in figs.iteritems():
			for i,item in enumerate(value):
				item.savefig("{}/{}{}.png".format(path,key,i))
				item.clf()
		# figs["main"].savefig("/tmp/main.png")       


		shutil.make_archive("/tmp/tsmi/out", 'zip', path)
		zip = open("/tmp/tsmi/out.zip", "rb").read()
		with fs.new_file(filename="{}.zip".format(oid)) as fb:
			fb.write(zip)

		plt.clf()
		shutil.rmtree(path)
		os.remove("/tmp/tsmi/out.zip")
	

def build_stats(oid):
	



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


	
	shutil.make_archive("/tmp/tsmi/out".format(path), 'zip', path)
	zip = open("/tmp/tsmi/out.zip", "rb").read()
	with fs.new_file(filename="{}.zip".format(oid)) as fb:
		fb.write(zip)

	plt.clf()
	shutil.rmtree(path)
	os.remove("/tmp/tsmi/out.zip")
	# plt.show()

	
if __name__ == "__main__":

	lst = list(db.runs.find())
	print len(lst)
	i = 0
	for item in lst:
		i+=1
		print(i)
		oid = str(item["_id"])
		try:
			obj = StatsBuilder("5894455af7478630fb2f04b9")
			obj.plot_all()
			obj.insert()
		except:
			print("Failed")
		
	# info = obj.item["meta"]["param_info"]

	# print(info)
	# obj.plot_main()
	# obj.plot_positions_hists()
	# obj.plot_paths()
	# obj.plot_freq()

	# obj.plot_accepted_stats()

	# obj.plot_field_line("delta")
	# obj.plot_field_hist("acceptance_probability")
	# obj.plot_field_hist("random_probability")
	# obj.show()

	sys.exit()
	# build_stats("5876b835f74786316bd909d9")
	