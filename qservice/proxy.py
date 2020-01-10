from flask import Flask, Response, request
import zmq
from uuid import uuid4
from threading import Thread
from os import makedirs, path, urandom
import json

app = Flask(__name__)
app.secret_key = urandom(12)
ctx = zmq.Context()
ml_url = 'tcp://0.0.0.0:8001'

@app.route('/person-query', methods=['POST'])
def send_image():
    content = request.json
    if not content["wait"]:
        client = ctx.socket(zmq.DEALER)
        identity = str(uuid4()).replace('-', '')[: 8]
        client.setsockopt_string(zmq.IDENTITY, identity)
        client.connect(ml_url)

        # client.hwm = 50
        # client.sndhwm = 50
        print("Request: {}". format(content['filename']))

        client.send(b"", zmq.SNDMORE)
        client.send_pyobj(content)
        client.close()  

        return Response(response=json.dumps({
            "status": 200,
            "identity": identity,
        }), status=200, mimetype='application/json')
    else:
        client = ctx.socket(zmq.REQ)
        identity = str(uuid4()).replace('-', '')[: 8]
        client.setsockopt_string(zmq.IDENTITY, identity)
        client.connect(ml_url)

        client.send_pyobj(content)
        response = client.recv_json()
        client.close()

        return Response(response=json.dumps({
            "status": 200,
            "response": response
        }), status=200, mimetype="application/json")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8443, debug=True)
     