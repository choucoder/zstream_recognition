import zmq
import time
from imutils import resize
from cv2 import VideoCapture
from threading import Thread
from imutils.video import VideoStream

#25 fps with REQ
#29 fps with DEALER

class StreamClient(Thread):
    def __init__(self, parent, broker_url, camera_url, **kwargs):
        Thread.__init__(self, daemon=True, name=camera_url)
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.parent = parent
        self.broker_url = broker_url
        self.camera_url = camera_url
        self._terminated = False

        self.frame = None
        self._wasCloseReader = False

    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        self._terminated = True
        try:
            del self.parent.stream_clients[self.camera_url]
        except:
            pass

    def read_frame(self):
        if 'rtsp://' in self.camera_url:
            frame = self.streamer.read()
            try:
                if not frame:
                    return False, frame
            except:
                return True, frame
        else:
            return self.streamer.read()

    def stream_reader(self):
        frames = 0
        startTime = time.time()

        while not self.terminated and not self.parent.terminated:
            try:
                ret, self.frame = self.read_frame()
                if not ret:
                    break

                frames += 1
                diffTime = time.time() - startTime
                fps = round(frames / diffTime, 2)
                # print(fps)
            except:
                break
        self._wasCloseReader = True

    def run(self):
        # Network configurations
        context = zmq.Context(io_threads=1)
        client = context.socket(zmq.DEALER)
        identity = "Client-{}".format(self.camera_url)
        client.setsockopt_string(zmq.IDENTITY, identity)
        client.connect(self.broker_url)

        poller = zmq.Poller()
        poller.register(client, zmq.POLLIN)

        # VideoStreaming configuration
        if 'rtsp://' in self.camera_url:
            self.streamer = VideoStream(src=self.camera_url).start()
        else:
            self.streamer = VideoCapture(self.camera_url)
        Thread(target=self.stream_reader, args=(), daemon=True).start()

        while not self.terminated and not self.parent.terminated:
            try:
                if self.frame is not None:
                    client.send(b"", zmq.SNDMORE)
                    client.send_pyobj(self.frame)
                elif self._wasCloseReader:
                    break

            except zmq.ZMQError as e:
                if e.strerror == "Context was terminated":
                    break
                else:
                    raise e

        client.close()
        context.term()
        self.terminate()
        print("[INFO] {} has been terminated".format(self.camera_url))