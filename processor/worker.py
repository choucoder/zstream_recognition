import zmq
from uuid import uuid4

class DeepLearningWorker(object):

    def __init__(self, worker_url, stream_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.worker_url = worker_url
        self.stream_url = stream_url
        self._terminated = False
    
    @property
    def terminated(self):
        return self._terminated

    def start_worker(self):
        ctx = zmq.Context()
        worker = ctx.socket(zmq.REQ)
        identity = str(uuid4()).replace('-', '')[: 8]
        worker.setsockopt_string(zmq.IDENTITY, identity)
        worker.connect(self.worker_url)

        streamfe = ctx.socket(zmq.PUB)
        streamfe.connect(self.stream_url)

        worker.send(b"0x1")

        while not self.terminated:
            try:
                client_address, _, frame = worker.recv_multipart()
                reply = b"READY"
                worker.send_multipart([client_address, b"", reply])
                # Send frame and json response to streaming server
                streamfe.send_multipart([client_address, frame, reply])
            except zmq.ZMQError as e:
                if e.strerror == "Context was terminated":
                    break
                else:
                    raise e

        worker.close()
        ctx.term()
        self._terminated = True
        
    def terminate(self):
        self._terminated = True

def main():
    try:
        worker = DeepLearningWorker(
            worker_url='tcp://localhost:5551', 
            stream_url='tcp://localhost:5552')
        worker.start_worker()
    except (KeyboardInterrupt, SystemExit):
        worker.terminate()

if __name__ == '__main__':
    main()