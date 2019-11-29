import sys
import zmq

class StreamingBroker(object):

    def __init__(self, frontend_url, backend_url, **kwargs):
        if kwargs:
            raise TypeError("Unrecognized keyword argument: {}".format(kwargs))
        self.backend_url = backend_url
        self.frontend_url = frontend_url

    def start_streaming_broker(self):
        try:
            context = zmq.Context(io_threads=5)
            frontend = context.socket(zmq.SUB)
            frontend.bind(self.frontend_url)

            frontend.setsockopt_string(zmq.SUBSCRIBE, "")

            backend = context.socket(zmq.PUB)
            backend.bind(self.backend_url)
            
            print("[INFO] Streaming broker has been started.")
            zmq.device(zmq.FORWARDER, frontend, backend)
        except zmq.ZMQError as e:
            print(e)
            if e.strerror == "Context was terminated":
                return
            else:
                raise e
        finally:
            backend.close()
            frontend.close()
            context.term()

def main():
    url_backend = 'tcp://*:5553' 
    url_frontend = 'tcp://*:5552'

    try:
        StreamingBroker(url_frontend, url_backend).start_streaming_broker()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

if __name__ == '__main__':
    main()

