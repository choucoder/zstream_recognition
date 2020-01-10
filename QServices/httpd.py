import zmq
import sys
from flask import Flask
from threading import Thread
from os import makedirs, path, urandom

class QServer(object):

    def __init__(self, frontend_url, backend_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword arguments {}".format(kwargs))
        
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.statefe_url = "tcp://*:8003"
        self.FaceQ = []
        self.EstimationQ = []
        self.workers_list = []
        self.available_workers = 0
        self._terminated = False

    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        self._terminated = True
        self.backend.close()
        self.frontend.close()

    def run(self):
        
        ctx = zmq.Context()
        # Server to receive frames via http requests
        self.frontend = ctx.socket(zmq.ROUTER)
        self.frontend.bind(self.frontend_url)
        # Set endpoint to QWorkers
        self.backend = ctx.socket(zmq.ROUTER)
        self.backend.bind(self.backend_url)

        # status socket
        self.statefe = ctx.socket(zmq.PULL)
        self.statefe.bind(self.statefe_url)

        poller = zmq.Poller()
        poller.register(self.frontend, zmq.POLLIN)
        poller.register(self.backend, zmq.POLLIN)
        poller.register(self.statefe, zmq.POLLIN)
        print("[INFO] Qserver at {} is ONLINE".format(self.frontend_url))

        while not self.terminated:
            sockets = dict(poller.poll())

            if (self.backend in sockets and sockets[self.backend] == zmq.POLLIN):
                msg = self.backend.recv_multipart()
                (worker_address, _), msg = msg[: 2], msg[2: ]

                if msg[0] == b"0x1":
                    print("[INFO] Worker {} has been connected.".format(worker_address))
                elif msg[0] == b"0x2":
                    pass
                else:
                    self.frontend.send_multipart(msg)
                try:
                    msg = self.FaceQ.pop(0)
                    msg = [worker_address, b""] + msg
                    self.backend.send_multipart(msg)
                except IndexError:
                    self.workers_list.append(worker_address)
                    self.available_workers += 1
            
            if (self.statefe in sockets and sockets[self.statefe] == zmq.POLLIN):
                (worker_address, signal) = self.statefe.recv_multipart()
                if signal == b"KILLED":
                    if worker_address in self.workers_list:
                        worker_index = self.workers_list.index(worker_address)
                        self.workers_list.pop(worker_index)
                        self.available_workers -= 1
                        print("[INFO] Worker {} has been terminated.".format(worker_address))

            if (self.frontend in sockets and sockets[self.frontend] == zmq.POLLIN):
                msg = self.frontend.recv_multipart()
                if self.available_workers > 0:
                    self.available_workers -= 1
                    worker_address = self.workers_list.pop(0)
                    msg = [worker_address, b""] + msg
                    self.backend.send_multipart(msg)
                else:
                    # QWorkers are busy so, we are going to Push to Queue
                    self.FaceQ.append(msg)
        ctx.term()
        self.terminate()

def main():
    try:
        frontend_url = 'tcp://*:8001'
        backend_url = 'tcp://*:8002'
        qserver = QServer(frontend_url, backend_url)
        qserver.run()
    
    except (KeyboardInterrupt, SystemExit):
        qserver.terminate()
    finally:
        sys.exit(0)

if __name__ == '__main__':
    main()
