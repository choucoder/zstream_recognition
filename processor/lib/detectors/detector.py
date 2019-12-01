

class MtcnnDetector(object):

	def __init__(
					self,
					min_face_size = 70,
					scale_factor = 0.709,
					device = '/device:GPU:0'
				):

		import numpy as np
		import tensorflow as tf
		from mtcnn.mtcnn import MTCNN

		with tf.device(device):
			self.detector = MTCNN(min_face_size=min_face_size, scale_factor=scale_factor)

	def getBoxes(self, frame, confidence=0.7, boxes_to_return='box'):
		bboxes = []
		results = self.detector.detect_faces(frame)

		for result in results:
			if result['confidence'] > confidence:
				x1, y1, width, height = result['box']
				x1, y1 = abs(x1), abs(y1)
				if boxes_to_return == 'box':
					x2, y2 = x1 + width, y1 + height
					bboxes.append([x1, y1, x2, y2])
				else:
					bboxes.append([x1, y1, width, height])
		return bboxes

class DlibDetector(object):

	def __init__(self):
		
		from face_recognition import face_locations

	def getBoxes(self, *args):

		return face_locations(args[0], model='cnn')

