#!/usr/bin/env python3

import os
import sys
import cv2
from imutils import resize
from face_recognition import face_locations
from threading import Thread as thread
from time import sleep, time
from uuid import uuid4
from queueProcess import QueueProcess
from lib.get_serial import get_hashed_mbserial

class MainThread(object):
	frames = []
	terminated = False

	def __init__(self, source):
		self.camera_url = source
		self.mb_serial = get_hashed_mbserial()
		self.checkFolder()
		thread(target=self.captureThread, args=(source,)).start()
		while not self.frames:
			sleep(0.3)
		thread(target=self.promptThread).start()
		self.queueThread = QueueProcess(self)
		self.queueThread.start()

	def terminate(self):
		self.terminated = True

	def checkFolder(self):
		folder = 'queue'
		if not os.path.exists(folder):
			os.mkdir(folder)

	def captureThread(self, source):
		try:
			source = int(source)
		except:
			pass
		cap = cv2.VideoCapture(source)
		while not self.terminated:
			try:
				ret, frame = cap.read()
				self.frames = [frame, resize(frame, width=180)]
			except AttributeError:
				cap = cv2.VideoCapture(source)

	def promptThread(self):
		frames = 0
		start = time()
		persons = 0

		while True:
			try:
				frames += 1
				total = time() - start
				fps = round(frames / total, 2)

				originalFrame, frame = self.frames.copy()
				r = originalFrame.shape[1] / float(frame.shape[1])
				boxes = face_locations(frame, model='hog')

				if len(boxes) != persons:
					if boxes:
						filename = "{}-{}".format(str(time()).replace('.', ''), str(uuid4())[0: 4])
						cv2.imwrite('queue/{}.jpg'.format(filename), originalFrame)
					persons = len(boxes)

				for (top, right, bottom, left) in boxes:
					top = int(top * r)
					right = int(right * r)
					bottom = int(bottom * r)
					left = int(left * r)

					cv2.rectangle(originalFrame, (left, top), (right, bottom), (255, 255, 255), 1, cv2.LINE_AA)
				#cv2.imshow('Test', originalFrame)
				if cv2.waitKey(1) & 0xFF == ord('q'):
					break

			except KeyboardInterrupt:
				self.terminated = True
				break

if __name__ == '__main__':
	try:
		source = sys.argv[1]
	except:
		source = 0
	try:
		main = MainThread(source)
	except (KeyboardInterrupt, SystemExit):
		main.terminate()