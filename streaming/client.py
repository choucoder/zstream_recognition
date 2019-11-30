import sys
import zmq
import time

url = 'tcp://0.0.0.0:5553'
context = zmq.Context(io_threads=1)
topic_filter = sys.argv[1] if len(sys.argv) > 1 else "Client-video.mp4"
streambe = context.socket(zmq.SUB)
streambe.connect(url)
streambe.setsockopt_string(zmq.SUBSCRIBE, topic_filter)

frames = 0
startTime = time.time()

while True:
    msg = streambe.recv_multipart()
    client_address, frame, results = msg
    
    elapsedTime = time.time() - startTime
    frames += 1
    fps = round(frames / elapsedTime, 2)
    print("fps {}: {}".format(client_address, fps))

streambe.close()
context.term()