#!/usr/bin/env python3
import sys
import zmq
import json
import time
import signal
import pickle
import requests
import configparser
import numpy as np
from cv2 import imdecode
from base64 import b64encode, b64decode
from uuid import uuid4
from imutils import resize
from threading import Thread, Lock
from face_recognition import face_encodings
from lib.recognition.recognition import HandlerSearch
from lib.detectors.detector import MtcnnDetector, DlibDetector

class SIGINT_handler():
    def __init__(self):
        self.SIGINT = False
    
    def signal_handler(self, signal, frame):
        self.SIGINT = True

class DeepLearningWorker(object):

    def __init__(self, worker_url, stream_url, status_url, api_url, handler,
                resize_width=256, min_face_size=17, mode="queue", **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.mode = mode
        self.handler = handler
        self.api_url = api_url
        self.worker_url = worker_url
        self.stream_url = stream_url
        self.status_url = status_url
        self.resize_width = resize_width
        self._terminated = False
        self.processedQueue = []

        self.detector = MtcnnDetector(min_face_size=min_face_size)
        #self.handlerSearch = HandlerSearch()
        #self.handlerSearch.prepare_for_searches()
        if self.mode == "queue":
            self.senderThread = Thread(target=self.sender, args=())
            self.senderThread.start()

        ctx = zmq.Context()
        self.worker = ctx.socket(zmq.REQ)
        self.identity = str(uuid4()).replace('-', '')[: 8]
        self.worker.setsockopt_string(zmq.IDENTITY, self.identity)
        self.worker.connect(self.worker_url)

        self.streamfe = ctx.socket(zmq.PUB)
        self.streamfe.connect(self.stream_url)
        self.streamfe.hwm = 100
        self.streamfe.sndhwm = 100

        self.statebe = ctx.socket(zmq.PUSH)
        self.statebe.connect(self.status_url)
        self.ctx = ctx

        self.poller = zmq.Poller()
        self.poller.register(self.worker, zmq.POLLIN)

    @property
    def terminated(self):
        return self._terminated

    def _toOriginal(self, boxes, r):
        bboxes = []
        for (left, top, right, bottom) in boxes:
            left, top = int(left * r), int(top * r)
            right, bottom = int(right * r), int(bottom * r)
            bboxes.append([left, top, right, bottom])
        return bboxes

    def getFrame(self, data):
        if self.mode == "realtime":
            return pickle.loads(data), ""
        else:
            data = pickle.loads(data)
            image = b64decode(data['picture'])
            npimg = np.fromstring(image, dtype=np.uint8)
            frame = imdecode(npimg, 1)
            del data['picture']
            return frame, data

    def send_response(self, client_address, frame, response):
        if self.mode == "realtime":
            self.streamfe.send(client_address, zmq.SNDMORE)
            self.streamfe.send(pickle.dumps(frame), zmq.SNDMORE)
            self.streamfe.send_json(response)
        else:
            if not response["info"]["wait"]:
                self.worker.send_multipart([client_address, b"", b"OK"])
            else:
                self.worker.send(client_address, zmq.SNDMORE)
                self.worker.send(b"", zmq.SNDMORE)
                self.worker.send_json(response)
            
            ids, names = response['ids'], response['names']
            header = response['info']

            for i in range(len(ids)):
                resp = {
                    'person_id': ids[i],
                    'timestamp': header['timestamp'],
                    'name': names[i],
                    'mb_serial': header['mb_serial'],
                    'camera_url': header['camera_url'],
                    'pictures': [],
                    'event_type': 'detection',
                    'detection_type': 'person',
                }
                self.processedQueue.append(resp)

    def sender(self):
        while not self.terminated and not self.handler.SIGINT:
            try:
                response = self.processedQueue[0]
                resp = requests.post(
                    url=self.api_url,
                    json=response
                )
                print(response["timestamp"])
                resp = resp.json()
                if resp["status"] == 400:
                    del self.processedQueue[0]

            except IndexError:
                pass
            except requests.exceptions.ConnectionError:
                print("[ERRNO] Failed to establish connection with API {}".format(self.api_url))
                time.sleep(.5)

    def start_worker(self):
        print("[INFO] Worker {} is running...".format(self.identity))

        self.worker.send(b"0x1")
        frames = 0
        startTime = time.time()

        while not self.terminated and not self.handler.SIGINT:
            sockets = dict(self.poller.poll(1))

            if (self.worker in sockets and sockets[self.worker] == zmq.POLLIN):
                try:
                    client_address, _, data = self.worker.recv_multipart()
                    frame, info = self.getFrame(data)

                    resizedFrame = resize(frame, width=self.resize_width)
                    r = frame.shape[1] / float(resizedFrame.shape[1])

                    boxes = self.detector.getBoxes(resizedFrame)
                    boxes = self._toOriginal(boxes, r)
                    encodings = face_encodings(frame, boxes)
                    #ids, names = self.handlerSearch.search(encodings, matches=20, confidence=0.025)
                    ids = ["Unknown"]*len(boxes)
                    names = ids
                    frames += 1
                    elapsedTime = time.time() - startTime
                    fps = round(frames / elapsedTime, 2)
                    
                    reply = {'boxes': boxes, 'ids': ids, 
                            'names': names, 'fps': fps, 'info': info}
                    self.send_response(client_address, frame, reply)
                except zmq.ZMQError as e:
                    if e.strerror == "Context was terminated":
                        break
                    else:
                        self.statebe.send_multipart([self.identity.encode('utf-8'), b"KILLED"])
                        raise e
        
        self.worker.close()
        self.terminate()
        
    def terminate(self):
        if not self.terminated:
            self._terminated = True
            self.statebe.send_multipart([self.identity.encode('utf-8'), b"KILLED"])

def main():
    try:
        params = configparser.ConfigParser()
        params.read('config.ini')
        
        worker_url = 'tcp://{}:{}'.format(params.get("backend", "host"), params.get("backend", "port"))
        status_url = "tcp://{}:{}".format(params.get("statefe", "host"), params.get("statefe", "port"))
        stream_url = "tcp://{}:{}".format(params.get("streaming", "host"), params.get("streaming", "port"))
        api_url = "http://{}:{}/event".format(params.get("api", "host"), params.get("api", "port"))
        handler = SIGINT_handler()
        
        worker = DeepLearningWorker(
            worker_url=worker_url, 
            stream_url=stream_url,
            status_url=status_url,
            api_url=api_url,
            handler=handler)
        signal.signal(signal.SIGINT, handler.signal_handler)
        signal.signal(signal.SIGHUP, handler.signal_handler)
        signal.signal(signal.SIGINT, handler.signal_handler)
        signal.signal(signal.SIGQUIT, handler.signal_handler)
        signal.signal(signal.SIGILL, handler.signal_handler)
        signal.signal(signal.SIGTRAP, handler.signal_handler)
        signal.signal(signal.SIGABRT, handler.signal_handler)
        signal.signal(signal.SIGBUS, handler.signal_handler)
        signal.signal(signal.SIGFPE, handler.signal_handler)
        #signal.signal(signal.SIGKILL, receiveSignal)
        signal.signal(signal.SIGUSR1, handler.signal_handler)
        signal.signal(signal.SIGSEGV, handler.signal_handler)
        signal.signal(signal.SIGUSR2, handler.signal_handler)
        signal.signal(signal.SIGPIPE, handler.signal_handler)
        signal.signal(signal.SIGALRM, handler.signal_handler)
        signal.signal(signal.SIGTERM, handler.signal_handler)
        worker.start_worker()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        worker.terminate()

if __name__ == '__main__':
    main()