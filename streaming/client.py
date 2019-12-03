import cv2
import sys
import zmq
import json
import time
from pickle import loads
from utils.draw import drawFaces

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
    frame = loads(frame)
    results = json.loads(results)

    elapsedTime = time.time() - startTime
    frames += 1
    fps = round(frames / elapsedTime, 2)

    frame = drawFaces(frame, results['boxes'], results['ids'], results['names'])
    cv2.putText(frame, 'fps: ' + str(fps), (int(10), int(20)),
                cv2.FONT_HERSHEY_DUPLEX, 0.50, (190, 75, 23), 1)
    
    cv2.imshow(topic_filter, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

streambe.close()
context.term()
cv2.destroyAllWindows()