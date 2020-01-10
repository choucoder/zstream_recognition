#!/usr/bin/env python3

from os import system, walk
from time import sleep
from requests import post

from lib.utils import *

url = '0.0.0.0:8443'

def login():

	response = post(
				url = 'http://{}/login'.format(url),
				json = {
			"email": "troconisbaltar@gmail.com",
			"password": "18138899"
		}
	)

	data = response.json()
	print(data)
	if data['status'] != 200:
		return [ None ]
	return [ data['token'] ]

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

if __name__ == '__main__':
	key = ["morty"]

	while True:
		sleep(1)
		try:
			if not key:
				print('Not key yet')
				key = login()
			if key[0]:

				for (_, _, files) in walk('queue'):
					for name in files:
						print('Processing: {}'.format(name))
						raw = encodeImg('queue/{}'.format(name))
						response = post(
							url = 'http://{}/person-query'.format(url),
							json = {
								'picture': raw,
								'filename': name,
								'key': key[0]
							},
						)
						response = response.json()
						if response['status'] == 200:
							system('rm -f "queue/{}"'.format(str(name)))
		except Exception as e:
			print(e)
			