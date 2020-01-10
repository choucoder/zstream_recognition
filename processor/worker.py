#!/usr/bin/env python3
import zmq
import time
import pickle
from uuid import uuid4
from imutils import resize
from threading import Thread, Lock
from face_recognition import face_encodings
from lib.recognition.recognition import HandlerSearch
from lib.detectors.detector import MtcnnDetector, DlibDetector

class DeepLearningWorker(object):

    def __init__(self, worker_url, stream_url, status_url,
                resize_width=256, min_face_size=17, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.worker_url = worker_url
        self.stream_url = stream_url
        self.status_url = status_url
        self.resize_width = resize_width
        self._terminated = False

        self.detector = MtcnnDetector(min_face_size=min_face_size)
        self.handlerSearch = HandlerSearch()
        self.handlerSearch.prepare_for_searches()
    
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

    def start_worker(self):
        ctx = zmq.Context()
        worker = ctx.socket(zmq.REQ)
        self.identity = str(uuid4()).replace('-', '')[: 8]
        worker.setsockopt_string(zmq.IDENTITY, self.identity)
        worker.connect(self.worker_url)

        streamfe = ctx.socket(zmq.PUB)
        streamfe.connect(self.stream_url)
        streamfe.hwm = 100
        streamfe.sndhwm = 100

        self.statebe = ctx.socket(zmq.PUSH)
        self.statebe.connect(self.status_url)

        print("[INFO] Worker {} is running...".format(self.identity))

        worker.send(b"0x1")
        frames = 0
        startTime = time.time()

        while not self.terminated:
            try:
                client_address, _, data = worker.recv_multipart()
                frame = pickle.loads(data)
                resizedFrame = resize(frame, width=self.resize_width)
                r = frame.shape[1] / float(resizedFrame.shape[1])

                boxes = self.detector.getBoxes(resizedFrame)
                boxes = self._toOriginal(boxes, r)
                encodings = face_encodings(frame, boxes)
                ids, names = self.handlerSearch.search(encodings, matches=20, confidence=0.025)

                frames += 1
                elapsedTime = time.time() - startTime
                fps = round(frames / elapsedTime, 2)

                reply = {'boxes': boxes, 'ids': ids, 
                        'names': names, 'fps': fps}
        
                worker.send_multipart([client_address, b"", b"OK"])

                streamfe.send(client_address, zmq.SNDMORE)
                streamfe.send(pickle.dumps(frame), zmq.SNDMORE)
                streamfe.send_json(reply)

            except zmq.ZMQError as e:
                if e.strerror == "Context was terminated":
                    break
                else:
                    raise e
        
        worker.close()
        ctx.term()
        self.terminate()
        
    def terminate(self):
        if not self.terminated:
            self._terminated = True
            self.statebe.send_multipart([self.identity.encode('utf-8'), b"0x2"])

def main():
    try:
        worker = DeepLearningWorker(
            worker_url='tcp://localhost:5551', 
            stream_url='tcp://localhost:5552',
            status_url='tcp://localhost:5555')
        worker.start_worker()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        worker.terminate()

if __name__ == '__main__':
    main()