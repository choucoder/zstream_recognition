import os
import zmq
import sys
import pickle
import configparser
from uuid import uuid4
from time import time
from flask import Flask
from threading import Thread
from os import makedirs, path, urandom

class QServer(object):

    def __init__(self, frontend_url, backend_url, statefe_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword arguments {}".format(kwargs))
        
        self.frontend_url = frontend_url
        self.backend_url = backend_url
        self.statefe_url = statefe_url
        self.FaceQ = []
        self.EstimationQ = []
        self.workers_list = []
        self.available_workers = 0
        self._terminated = False
        self.dirpath = os.path.join(os.getcwd(), 'tmp')

        if not os.path.exists(self.dirpath):
            os.mkdir(self.dirpath)
        self.Files = []
        self.load_tmp_files()
    
    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        self._terminated = True
        self.backend.close()
        self.frontend.close()

    def load_tmp_files(self):
        if os.path.exists(self.dirpath):
            for _, _, files in os.walk(self.dirpath):
                for name in files:
                    filename = os.path.join(self.dirpath, name)
                    self.Files.append(filename)
        self.Files.sort()
        print("[INFO] Files loaded from {}".format(self.dirpath))

    def saveQueryFile(self, msg):
        filename = time()
        filename = str(filename).replace('.', '')
        filename += str(uuid4()).replace('-', '')[: 4] + '.zy'

        filepath = os.path.join(self.dirpath, filename)

        with open(filepath, 'wb') as f:
            f.write(pickle.dumps(msg))
            f.close()

        self.Files.append(filepath)

    def loadQueryFile(self):
        try:
            filepath = self.Files[0]
            print("laoding.: {}".format(filepath.split('/')[-1]))
            with open(filepath, 'rb') as f:
                msg = pickle.loads(f.read())
                f.close()
            os.remove(filepath)
            del self.Files[0]
            return msg
        except IndexError:
            raise IndexError

        except Exception as e:
            os.remove(filepath)
            del self.Files[0]
            print("[ERRNO] File was deleted by ran out of input")
            raise FileExistsError

    def run(self):
        
        ctx = zmq.Context()
        # Server to receive frames via http requests
        self.frontend = ctx.socket(zmq.ROUTER)
        self.frontend.bind(self.frontend_url)
        self.frontend.hwm = 100
        self.frontend.sndhwm = 100
        
        # Set endpoint to QWorkers
        self.backend = ctx.socket(zmq.ROUTER)
        self.backend.bind(self.backend_url)
        self.backend.sndhwm = 100

        # status socket
        self.statefe = ctx.socket(zmq.PULL)
        self.statefe.bind(self.statefe_url)

        poller = zmq.Poller()
        poller.register(self.frontend, zmq.POLLIN)
        poller.register(self.backend, zmq.POLLIN)
        poller.register(self.statefe, zmq.POLLIN)
        print("[INFO] Qserver at {} is ONLINE".format(self.frontend_url))

        while not self.terminated:
            sockets = dict(poller.poll(1))

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
                    msg = self.loadQueryFile()
                    msg = [worker_address, b""] + msg
                    self.backend.send_multipart(msg)
                except (IndexError, FileExistsError):
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
                if 'proxy' in str(msg[0]):
                    self.saveQueryFile(msg)
                    if self.available_workers > 0:
                        self.available_workers -= 1
                        worker_address = self.workers_list.pop(0)
                        msg = [worker_address, b""] + self.loadQueryFile()
                        self.backend.send_multipart(msg)

            if len(self.Files) > 0 and self.available_workers > 0:
                try:
                    msg = self.loadQueryFile()
                    msg = [worker_address, b""] + msg
                    worker_address = self.workers_list.pop(0)
                    self.available_workers -= 1
                    self.backend.send_multipart(msg)
                except (IndexError, FileExistsError) as e:
                    pass

        ctx.term()
        self.terminate()

def main():
    try:
        params = configparser.ConfigParser()
        params.read("config.ini")
        frontend_url = 'tcp://*:{}'.format(params.get("frontend", "port"))
        backend_url = 'tcp://*:{}'.format(params.get("backend", "port"))
        statefe_url = 'tcp://*:{}'.format(params.get("statefe", "port"))
        qserver = QServer(frontend_url, backend_url, statefe_url)
        qserver.run()
    
    except (KeyboardInterrupt, SystemExit):
        qserver.terminate()
    finally:
        sys.exit(0)

if __name__ == '__main__':
    main()