from cv2 import VideoCapture
from imutils.video import VideoStream

def online(url):
    try:
        if 'rtsp://localhost-' in url:
            vs = VideoCapture(url_format(url))
            ret, frame = vs.read()
            vs.release()
            if not ret and not frame:
                return False
            return True
        else:
            vs = VideoStream(src=url)
            frame = vs.read()
            vs.stop()
            try:
                if not frame:
                    return False
            except:
                pass
            return True
    except:
        return False

def url_format(url):
    if 'localhost' in url:
        opencv_url = url.split("-")[1]
        try:
            return int(opencv_url)
        except ValueError:
            return opencv_url
    return url