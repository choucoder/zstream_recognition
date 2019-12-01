#!/usr/bin/env python3
import zmq
import pickle
from uuid import uuid4
from imutils import resize
from face_recognition import face_encodings
from lib.detectors.detector import MtcnnDetector, DlibDetector
from lib.recognition.recognition import HandlerSearch

class DeepLearningWorker(object):

    def __init__(self, worker_url, stream_url, status_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.worker_url = worker_url
        self.stream_url = stream_url
        self.status_url = status_url
        self._terminated = False

        self.detector = DlibDetector()
        self.handlerSearch = HandlerSearch()
        self.handlerSearch.prepare_for_searches()
    
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
                reply = b"READY"
                # Facial recognition work
                frame = pickle.loads(data)
                frame = resize(frame, width=640, height=480)
                bboxes = self.detector.getBoxes(frame)

                # bboxes = self.detector.getBoxes(frame, confidence=0.8)
                encodings = face_encodings(frame, bboxes)
                ids, names = self.handlerSearch.search(encodings, matches=200, confidence=0.025)

                worker.send_multipart([client_address, b"", reply])
                # Send frame and json response to streaming server
                reply = {'boxes': bboxes, 'ids': ids, 'names': names}
                streamfe.send(client_address, zmq.SNDMORE)
                streamfe.send(pickle.dumps(frame), zmq.SNDMORE)
                streamfe.send_json(reply)
                #streamfe.send_multipart([client_address, frame, bytes(reply, 'utf-8').decode('utf-8')])
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