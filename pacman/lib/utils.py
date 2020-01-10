from base64 import b64encode
from cv2 import imread, imencode

def encodeImg(file):

	frame = imread(file, 1)
	_, raw = imencode('.jpg', frame)
	string = b64encode(raw).decode('utf-8')

	return string