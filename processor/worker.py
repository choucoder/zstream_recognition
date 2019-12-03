#!/usr/bin/env python3
import zmq
import pickle
from uuid import uuid4
from imutils import resize
from threading import Thread, Lock
from face_recognition import face_encodings
from lib.recognition.recognition import HandlerSearch
from lib.detectors.detector import MtcnnDetector, DlibDetector

class DeepLearningWorker(object):

    def __init__(self, worker_url, stream_url, status_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.worker_url = worker_url
        self.stream_url = stream_url
        self.status_url = status_url
        self._terminated = False

        self.detector = MtcnnDetector()
        self.handlerSearch = HandlerSearch()
        self.handlerSearch.prepare_for_searches()
        self.current_msg = (None, None)
        self.boxes = {}
        self.ids, self.names = {}, {}
        self.rThread = Thread(target=self.recognition_thread, daemon=True)
        self.rThread.start()
    
    @property
    def terminated(self):
        return self._terminated

    def start_worker(self):
        ctx = zmq.Context()
        worker = ctx.socket(zmq.REQ)
        self.identity = str(uuid4()).replace('-', '')[: 8]
        worker.setsockopt_string(zmq.IDENTITY, self.identity)
        worker.connect(self.worker_url)

        streamfe = ctx.socket(zmq.PUB)
        streamfe.connect(self.stream_url)

        self.statebe = ctx.socket(zmq.PUSH)
        self.statebe.connect(self.status_url)

        print("[INFO] Worker {} is running...".format(self.identity))

        worker.send(b"0x1")

        while not self.terminated:
            try:
                client_address, _, data = worker.recv_multipart()
                self.frame = pickle.loads(data)
                self.current_msg = (client_address, self.frame.copy())

                if client_address not in self.boxes:
                    self.ids[client_address] = []
                    self.names[client_address] = []
                    self.boxes[client_address] = []

                if (len(self.boxes[client_address]) > 0):
                    reply = {'ids': self.ids[client_address].pop(0), 
                            'names': self.names[client_address].pop(0),
                            'boxes': self.boxes[client_address].pop(0)}
                else:
                    reply = {'boxes': [], 'ids': [], 'names': []}
        
                worker.send_multipart([client_address, b"", b"OK"])

                streamfe.send(client_address, zmq.SNDMORE)
                streamfe.send(pickle.dumps(self.frame), zmq.SNDMORE)
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

    def recognition_thread(self):
        while not self.terminated:
            if self.current_msg[1] is not None:
                client, frame = self.current_msg
                boxes = self.detector.getBoxes(frame, confidence=0.8)
                encodings = face_encodings(frame, boxes)
                ids, names = self.handlerSearch.search(encodings, matches=30, confidence=0.025)
                self.ids[client].append(ids)
                self.names[client].append(names)
                self.boxes[client].append(boxes)

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