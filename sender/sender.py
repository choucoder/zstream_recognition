# A script to send streaming from ip camera over tcp
import sys
import zmq
import time
from threading import Thread
from cv2 import VideoCapture
from client import StreamClient
from imutils.video import VideoStream
from helpers import online, url_format

class StreamHandler(object):
    def __init__(self, broker_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.broker_url = broker_url
        self.stream_clients = {}
        self._terminated = False

    @property
    def terminated(self):
        return self._terminated

    def is_streaming(self, url_camera):
        for streamClient in self.stream_clients.values():
            if streamClient.camera_url == url_camera:
                return True
        return False

    def start_main_process(self):
        print("[INFO] Starting StreamHandler...")
        while not self.terminated:
            time.sleep(2.5)
            cameras = ['rtsp://localhost-video.mp4']
            for camera in cameras:
                if not self.is_streaming(camera) and online(camera):
                    camera_url = url_format(camera)
                    self.stream_clients[camera_url] = StreamClient(self, self.broker_url, camera_url)
                    self.stream_clients[camera_url].start()
                    print("[INFO] StreamClient[{}] has been started.".format(camera))
                else:
                    print("[INFO] Camera {} sucks".format(url_format(camera)))

    def terminate(self):
        self._terminated = True
        keys = list(self.stream_clients.keys())
        for sc in keys:
            try:
                self.stream_clients[sc].terminate()
            except:
                pass
        print("[INFO] Streaming sender has been terminated.")
    
if __name__ == '__main__':
    try:
        cameras = sys.argv[1: ]
        broker_url = 'tcp://localhost:5550'
        handler = StreamHandler(broker_url)
        handler.start_main_process()
    except (KeyboardInterrupt, SystemExit):
        handler.terminate()
        sys.exit(0)