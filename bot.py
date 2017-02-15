from telegram.ext import CommandHandler
from telegram.ext import Updater
import telegram

from pprint import pprint
import pymongo
import logging
import threading
import time
import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


token = '361872774:AAG-d1Q9jlw70Djvg6oOLvCuoykzxN2OYCw'
updater = Updater(token=token)
dispatcher = updater.dispatcher
BOT = telegram.Bot(token=token)

client = pymongo.MongoClient() 
db = client.tsmi


def get_credentials(update):
	uid = update.message.chat.id
	alias = update.message.chat.username
	return uid, alias

def start(bot, update):
	text = """ Hello you can use the following commands
/subscribe
/unsubscribe"""
	uid = update.message.chat.id
	bot.sendMessage(chat_id=uid, text=text)

def subscribe(bot, update):
	uid, alias = get_credentials(update)
	try:
		db.subscribers.insert({"uid":uid, "alias": alias})
		bot.sendMessage(chat_id=uid, text="Done")
	except:
		bot.sendMessage(chat_id=uid, text="You are already subscribed")

def unsubscribe(bot, update):
	uid, alias = get_credentials(update)
	db.subscribers.remove({"uid" : uid})
	bot.sendMessage(chat_id=uid, text="Done")


class UpdaterThread(threading.Thread):
	def __init__(self, updater):
		threading.Thread.__init__(self)
		self.updater = updater

	def run(self):
		updater.start_polling()
		

class WatcherThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.running = False
	def run(self):
		self.running = True
		while(self.running):
			ok = True
			try:
				r = requests.get("http://localhost:8080")
			except:
				subs = db.subscribers.find()
				for sub in subs:
					BOT.sendMessage(chat_id=sub["uid"], text="Server is down!")
			time.sleep(3)

start_handler = CommandHandler('start', start)
subscribe_handler = CommandHandler('subscribe', subscribe)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(subscribe_handler)
dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe))


updater_thread = UpdaterThread(updater)
updater_thread.start()
watcher_thread = WatcherThread()
watcher_thread.start()


watcher_thread.join()
updater_thread.join()


