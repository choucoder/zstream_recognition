import zmq
import time
from imutils import resize
from cv2 import VideoCapture
from threading import Thread

class StreamClient(Thread):
    def __init__(self, parent, broker_url, camera_url, **kwargs):
        Thread.__init__(self, daemon=True, name=camera_url)
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.parent = parent
        self.broker_url = broker_url
        self.camera_url = camera_url
        self._terminated = False
    
    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        self._terminated = True
        try:
            del self.parent.stream_clients[self.camera_url]
        except:
            pass

    def run(self):
        # Network configurations
        context = zmq.Context(io_threads=1)
        client = context.socket(zmq.REQ)
        identity = "Client-{}".format(self.camera_url)
        client.setsockopt_string(zmq.IDENTITY, identity)
        client.connect(self.broker_url)
        # VideoStreaming configuration
        streamer = VideoCapture(self.camera_url)

        frames = 0
        startTime = time.time()

        while not self.terminated and not self.parent.terminated:
            try:
                ret, frame = streamer.read()
                if not ret:
                    break
                frame = resize(frame, width=720, height=640)
                client.send_pyobj(frame)
                reply = client.recv()
                frames += 1
                diffTime = time.time() - startTime
                fps = round(frames / diffTime, 2)
                #print(fps)
            except zmq.ZMQError as e:
                if e.strerror == "Context was terminated":
                    break
                else:
                    raise e

        client.close()
        context.term()
        self.terminate()
        print("[INFO] {} has been terminated".format(self.camera_url))