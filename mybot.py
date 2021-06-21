#!/usr/bin/env python
# --coding:utf-8--

import vk_api
import time
import configparser
import pymongo
from fuzzywuzzy import process
import sys

# лучше создать класс бота...
user_name = sys.argv[1]

config = configparser.ConfigParser()
config.read("settings.ini")

client = pymongo.MongoClient(config["database"]["host"], int(config["database"]["port"]))
db = client[config["database"]["db"]]

user_profile = db['users'].find({'username': user_name})[0]

vk = vk_api.VkApi(token=user_profile["vk_token"])
id_group = int(user_profile["id_group"])
vk._auth_token()

answers_collection = db[user_name]
categories = answers_collection.distinct("categories")

while True:
	try:
		messages = vk.method("messages.getConversations", {"offset": 0, "count": 20, "filter": "unanswered"})
		if messages["count"] >= 1:
			for i in range(messages["count"]):
				id = messages["items"][i]["last_message"]["from_id"]
				body = messages["items"][i]["last_message"]["text"]
				profiles = vk.method('users.get', {'user_ids' : id })
				res_find_categories = process.extractOne(body, categories)
				ctg = ""
				if res_find_categories[1] > 45:
					ctg = res_find_categories[0]
				find_ans = []
				for s in answers_collection.find({"categories": ctg}):
					find_ans += s["keyword"]
				res_find_answers = process.extractOne(body, find_ans)
				if res_find_answers[1] > 45:
					for answer in answers_collection.find({"categories": ctg}):
						if res_find_answers[0] in answer["keyword"]:
							vk.method("messages.send", {"peer_id": id, "random_id": 0, "message": answer["text"].replace("{user name}", profiles[0]['first_name'])})
				else:
					vk.method("messages.markAsAnsweredConversation", {"peer_id": id, "answered": 1, "group_id": id_group})
	except vk_api.exceptions.ApiError:
		sys.exit()
	except Exception as E:
		print(E)
		time.sleep(1)
