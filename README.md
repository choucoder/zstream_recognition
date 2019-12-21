# ZEYE facial recognition
Software de reconocimiento facial en tiempo real.

Este software utiliza:
- MTCNN para la detección de rostro
- DLIB para obtener encodings del rostro
- Faiss para hacer matching en la base de datos

## Arquitectura
![](architecture.jpeg)

- Streaming Sender: Este proceso recoge streaming desde una o varias cámaras y lo envia hacia el Servidor de reconocimiento para ser procesado. En otras palabras, envia cada frame leido del flujo de la cámara al servidor de Reconocimiento.

- DetectorTest: Recoge streaming desde una camara, detecta rostros, hace reconocimiento facial sobre estos y envia el streaming + la información de las caras detectadas al Servidor de Streaming.

- Face Recognition Server: Este servidor actua de middleware entre los Streaming Senders y los Workers. Obtiene los frames enviados por los Senders y los envia al Worker disponible para realizar Reconocimiento facial sobre este utilizando balanceo de carga.

- Face Recognition Worker: Realiza detección de rostros y reconocimiento facial sobre los frames recibidos, escribe en la db las personas que han sido detectadas y envia el frame + la información (PUB) de las personas detectadas al Servidor de Streaming.

- Streaming Server: Actua de middleware entre el Worker y el Cliente Streaming. Recibe la data publicada por el Worker y la envia al cliente que la está solicitando.

- Proxy Server: Servidor proxy utilizado para obtener streaming desde la Web de una cámara.

- Streaming Client: Recibe (SUB) y muestra el video streaming en tiempo real junto a la información de las personas detectadas.

## Estructura de directorios

La estructura de directorios es la siguiente:

- processor: Contiene el Face Recognition Server, el worker y el detectorTest.
- sender: Contiene el sender.py para enviar streaming hacia el Face Recognition Server.
- streaming: Contiene el Streaming Server y el Client Server.
- websocket: Contiene el servidor proxy y la pagina web de prueba para visualizar streaming desde la web.

## Instrucciones de uso


## Requerimientos

### Streaming Sender
- [OpenCV 4.0.1+] (https://opencv.org)
- [ZMQ] (https://pyzmq.readthedocs.io/en/latest/)

### DetectorTest
- OpenCV
- zmq
- imutils
- MTCNN
- Tensorflow 1.5+
- faiss
- face_recognition
- mongoengine

### Face Recognition Server
- zmq

### Face Recognition Worker
- zmq
- uuid
- imutils
- face_recognition
- mtcnn
- tensorflow
- faiss
- mongoengine

### Streaming Server
- zmq

### Proxy Server
- zmq
- autobahn.asyncio.websocket
- json
- uuid

### Streaming Client
- zmq
- OpenCV