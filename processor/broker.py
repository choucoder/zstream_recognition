#!/usr/bin/env python3
import sys
import zmq

class InferenceBroker(object):

    def __init__(self, frontend_url, backend_url, statefe_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.statefe_url = statefe_url
        self._terminated = False
    
    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        self._terminated = True
        self.backend.close()
        self.statefe.close()
        self.frontend.close()

    def start_process(self):
        
        ctx = zmq.Context()
        self.frontend = ctx.socket(zmq.ROUTER)
        self.frontend.bind(self.frontend_url)
        self.backend = ctx.socket(zmq.ROUTER)
        self.backend.bind(self.backend_url)

        # status socket
        self.statefe = ctx.socket(zmq.PULL)
        self.statefe.bind(self.statefe_url)
        
        workers_list = []
        available_workers = 0

        poller = zmq.Poller()
        poller.register(self.backend, zmq.POLLIN)
        poller.register(self.frontend, zmq.POLLIN)
        poller.register(self.statefe, zmq.POLLIN)
        print("[INFO] Inference broker has been started.")

        while not self.terminated:
            sockets = dict(poller.poll())

            if (self.backend in sockets and sockets[self.backend] == zmq.POLLIN):
                msg = self.backend.recv_multipart()
                (worker_address, _), msg = msg[: 2], msg[2: ]
                
                available_workers += 1
                workers_list.append(worker_address)

                if msg[0] == b'0x1':
                    print("[INFO] Worker {} has been connected.".format(worker_address))
                else:
                    pass
                    #self.frontend.send_multipart(msg)

            if (self.statefe in sockets and sockets[self.statefe] == zmq.POLLIN):
                (worker_address, signal) = self.statefe.recv_multipart()
                available_workers -= 1
                if worker_address in workers_list:
                    worker_index = workers_list.index(worker_address)
                    workers_list.pop(worker_index)
                print("[INFO] Worker {} has been terminated.".format(worker_address))

            if available_workers > 0:
                if (self.frontend in sockets) and sockets[self.frontend] == zmq.POLLIN:
                    msg = self.frontend.recv_multipart()
                    available_workers -= 1
                    worker_address = workers_list.pop()
                    msg = [worker_address, b""] + msg
                    self.backend.send_multipart(msg)

        self.terminated = True

def main():
    try:
        client_url = 'tcp://*:5550'
        worker_url = 'tcp://*:5551'
        statefe_url = 'tcp://*:5555'
        broker = InferenceBroker(client_url, worker_url, statefe_url)
        broker.start_process()
    except (KeyboardInterrupt, SystemExit):
        broker.terminate()
    finally:
        sys.exit(0)

if __name__ == '__main__':
    main()