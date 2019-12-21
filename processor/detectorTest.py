#!/usr/bin/env python3
import cv2
import sys
import zmq
import time
import pickle
from imutils import resize
from threading import Thread
from lib.utils.draw import drawFaces, drawCorners
from lib.detectors.detector import MtcnnDetector
from face_recognition import face_encodings
from lib.recognition.recognition import HandlerSearch

class InferenceWorker(object):
    def __init__(self, camera_url, 
                stream_url='tcp://localhost:5552', 
                processing_type='async', 
                resize_width=256, 
                min_face_size=17, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.resize_width = resize_width
        self.camera_url = camera_url
        self.processing_type = processing_type
        
        self.stream_reader = cv2.VideoCapture(camera_url)
        self.ctx = zmq.Context(io_threads=1)
        self.streamfe = self.ctx.socket(zmq.PUB)
        self.topic_identity = "Client-" + camera_url
        self.streamfe.connect(stream_url)
   
        # Face recognition objects
        self.detector = MtcnnDetector(min_face_size=min_face_size)
        self.searchController = HandlerSearch()
        self.searchController.prepare_for_searches()

        # Shared object for async processing
        self.frame = None
        self.resizedFrame = None
        self.ids   = []
        self.boxes = []
        self.names = []
        
        self._terminated = False
        self.fps = 0

        if self.processing_type == 'async':
            self.rThread = Thread(target=self.recognition_worker)
            self.rThread.start()

    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        self._terminated = True
        self.stream_reader.release()
        self.streamfe.close()
        self.ctx.term()
        cv2.destroyAllWindows()

    def recognition_worker(self):
        self.frames = 0
        self.startTime = time.time()

        while not self.terminated:
            if self.frame is not None and self.resizedFrame is not None:
                r = self.frame.shape[1] / float(self.resizedFrame.shape[1])
                self.frames += 1
                elapsedTime = time.time() - self.startTime
                self.fps = round(self.frames / elapsedTime, 2)

                bboxes = self.detector.getBoxes(self.resizedFrame)
                bboxes = [[int(left*r), int(top*r), int(right*r), int(bottom*r)] for (left, top, right, bottom) in bboxes]
                encodings = face_encodings(self.frame, bboxes)
                ids, names = self.searchController.search(encodings, matches=15, confidence=0.025)
                self.boxes, self.ids, self.names = bboxes, ids, names

    def start_process(self):
        
        if self.processing_type == 'sync':
            self.frames = 0
            self.startTime = time.time()

        while not self.terminated:
            try:
                ret, self.frame = self.stream_reader.read()

                while not ret:
                    self.stream_reader = cv2.VideoCapture(self.camera_url)
                    ret, self.frame = self.stream_reader.read()

                self.resizedFrame = resize(self.frame, width=self.resize_width)
                r = self.frame.shape[1] / float(self.resizedFrame.shape[1])

                if self.processing_type == 'sync':
                    self.boxes = self.detector.getBoxes(self.resizedFrame)
                    self.boxes = [[int(left*r), int(top*r), int(right*r), int(bottom*r)] for (left, top, right, bottom) in self.boxes]
                    encodings = face_encodings(self.frame, self.boxes)
                    self.ids, self.names = self.searchController.search(encodings, matches=15, confidence=0.025)

                # Computing fps rate
                if self.processing_type == 'sync':
                    self.frames += 1
                    elapsedTime = time.time() - self.startTime
                    self.fps = round(self.frames / elapsedTime, 2)

                # Sending to streaming server
                reply = {'boxes': self.boxes, 'ids': self.ids, 'names': self.names, 'fps': self.fps}
                self.streamfe.send(bytes(self.topic_identity, 'utf-8'), zmq.SNDMORE)
                self.streamfe.send(pickle.dumps(self.frame), zmq.SNDMORE)
                self.streamfe.send_json(reply)

            except zmq.ZMQError as e:
                if e.strerror == "Context was terminated":
                    break
                else:
                    raise e
            except Exception as e:
                break

        self.terminate()

if __name__ == '__main__':
    try:
        help_message = '''
        USAGE: python3 detectorTest.py [camera_url]
        '''
        camera_url = sys.argv[1] if len(sys.argv) > 1 else ""
        if not camera_url:
            print(help_message)
            raise SystemExit
        iworker = InferenceWorker(processing_type='sync', camera_url=camera_url)
        iworker.start_process()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        try:
            iworker.terminate()
        except:
            pass