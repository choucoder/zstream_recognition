#!/usr/bin/env python3
import sys
import zmq
import time
from threading import Thread
from cv2 import VideoCapture
from client import StreamClient
from imutils.video import VideoStream
from helpers import online, url_format

class StreamHandler(object):
    def __init__(self, broker_url, cameras, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.broker_url = broker_url
        self.cameras = cameras
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
            #cameras = ['rtsp://localhost-video.mp4', 'rtsp://localhost-video2.mp4']
            for camera in self.cameras:
                camera_url = url_format(camera)
                if not self.is_streaming(camera_url) and online(camera):
                    self.stream_clients[camera_url] = StreamClient(self, self.broker_url, camera_url)
                    self.stream_clients[camera_url].start()
                    print("[INFO] StreamClient[{}] has been started.".format(camera_url))
                elif self.is_streaming(camera_url):
                    print("[INFO] Camera {} is already streaming".format(url_format(camera)))
                else:
                    print("[INFO] Camera {} is not online for streaming".format(url_format(camera)))

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
        help_message = '''
        USAGE: ./sender.py [<cam-url-1>,..., <cam-url-n>]
        '''
        cameras = sys.argv[1: ] if len(sys.argv) > 1 else []
        if cameras:
            print("[INFO] Sending streaming from cameras: {}".format(cameras))
        else:
            print("[INFO] The cameras url are going to be taken from zeye-cloud.")
        broker_url = 'tcp://localhost:5550'
        handler = StreamHandler(broker_url, cameras)
        handler.start_main_process()
    except (KeyboardInterrupt, SystemExit):
        handler.terminate()
        sys.exit(0)