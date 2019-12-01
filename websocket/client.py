import zmq
import time
import base64
import imutils
from json import dumps
from threading import Thread
from utils.draw import drawFaces
from cv2 import imencode, IMWRITE_JPEG_QUALITY, putText, FONT_HERSHEY_DUPLEX

class WebSocketClient(Thread):

    def __init__(self, key, parent, sserver_addr, topic_filter, **kwargs):
        Thread.__init__(self, daemon=True)
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        
        self.key = key
        self.parent = parent
        self.sserver_addr = sserver_addr
        self.topic_filter = topic_filter
        self._terminated = False

        self.ctx = zmq.Context()
        self.streambe = self.ctx.socket(zmq.SUB)
        self.streambe.connect(self.sserver_addr)
        self.streambe.setsockopt_string(zmq.SUBSCRIBE, self.topic_filter)

    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        #self.streambe.close()
        #self.ctx.term()
        self._terminated = True

        try:
            del self.parent.subscriptors[self.key]
        except (KeyError):
            pass

    def run(self):

        frames = 0
        startTime = time.time()
        while not self.terminated and not self.parent.terminated:
            try:
                client_address = self.streambe.recv()
                frame = self.streambe.recv_pyobj()
                reply = self.streambe.recv_json()
                
                frames += 1
                elapsedTime = time.time() - startTime
                fps = round(frames/elapsedTime, 2)

                try:
                    frame = imutils.resize(frame, width=640, height=480)
                    ids = reply['ids']
                    names = reply['names']
                    frame = drawFaces(frame, reply['boxes'], ids, names)
                    putText(frame, 'fps: ' + str(fps), (int(10), int(20)),
                        FONT_HERSHEY_DUPLEX, 0.50, (205, 155, 55), 1)
                    _, image = imencode('.jpg', frame)
                    data = base64.b64encode(image).decode('utf-8')
                    response = dumps({
                        'fps': fps,
                        'type': 0,
                        'data': data,
                        'online': 1,
                        'status': 201
                    }).encode('utf-8')

                    self.parent.sendMessage(response)
                except Exception as e:
                    print("Exception en : {}".format(e))
                    break
            except zmq.ZMQError as e:
                if e.strerror == "Context was terminated":
                    break
                else:
                    raise e

            except Exception as e:
                print("e: {}".format(e))

        if not self._terminated:
            self.terminate()