#!/usr/bin/env python3

from os import system, walk
from time import sleep, time
from datetime import datetime
from requests import post
from threading import Thread
from lib.utils import *

class QueueProcess(Thread):
	def __init__(self, parent, **kwargs):
		Thread.__init__(self)
		if kwargs:
			raise TypeError("Unrecognized keyword argument {}".format(kwargs))
		self.url = '0.0.0.0:8444'
		self.parent = parent
		self.daemon = True

	def login(self):
		response = post(
			url='http://{}/login'.format(self.url),
			json={
				"email": "troconisbaltar@gmail.com",
				"password": "18138899"
			}
		)
		data = response.json()
		if data["status"] != 200:
			return [None]
		return [data["token"]]

	def run(self):
		print("[INFO] QueueProcess has been started.")
		key = ["morty"]
		while not self.parent.terminated:
			sleep(1)
			try:
				if not key:
					print('Not key yet')
					key = self.login()
				if key[0]:
					for (_, _, files) in walk('queue'):
						for name in files:
							print('Processing: {}'.format(name))
							raw = encodeImg('queue/{}'.format(name))
							response = post(
								url = 'http://{}/person-query'.format(self.url),
								json = {
									'picture': raw,
									'filename': name,
									'key': key[0],
									'wait': True,
									"mode": "queue",
									"camera_url": self.parent.camera_url,
									"mb_serial": self.parent.mb_serial,
									"event_type": "detection",
									"detection_type": "person",
									"timestamp": str(datetime.now())
								},
							)
							response = response.json()
							if response['status'] == 200:
								system('rm -f "queue/{}"'.format(str(name)))
			except Exception as e:
				print(e)

def register_event(data):

	req = {}
	req['person_id'] 		= data['id']
	req['timestamp'] 		= data['timestamp']
	req['mb_serial'] 		= '1ejqhdakshdkjashdkjashdkjashdjs' # Change to real id 
	req['camera_url']		= 'rtsp://sdfdsafsdfsdfsdf' # change to real url
	req['pictures'] 		= [data['face'], data['video_file'][:-4] + '.mp4']
	req['event_type']		= 'detection'
	req['detection_type']	= 'person'

	response = post('http://localhost:8001/event', json=req)
			