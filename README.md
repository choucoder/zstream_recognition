# ZEYE Qfacial recognition
Software de reconocimiento facial en tiempo real.

Este software utiliza:
- MTCNN para la detección de rostro
- DLIB para obtener encodings del rostro
- Faiss para hacer matching en la base de datos

## Arquitectura
La arquitectura del software se muestra en la imagen: 
![](doc/architecture.jpeg)

- Streaming Sender: Este proceso recoge streaming desde una o varias cámaras y lo envia hacia el Servidor de reconocimiento para ser procesado. En otras palabras, envia cada frame leido del flujo de la cámara al servidor de Reconocimiento.

- DetectorTest: Recoge streaming desde una camara, detecta rostros, hace reconocimiento facial sobre estos y envia el streaming + la información de las caras detectadas al Servidor de Streaming.

- Face Recognition Server: Este servidor actua de middleware entre los Streaming Senders y los Workers. Obtiene los frames enviados por los Senders y los envia al Worker disponible para realizar Reconocimiento facial sobre este utilizando balanceo de carga.

- Face Recognition Worker: Realiza detección de rostros y reconocimiento facial sobre los frames recibidos, escribe en la db las personas que han sido detectadas y envia el frame + la información (PUB) de las personas detectadas al Servidor de Streaming.

- Streaming Server: Actua de middleware entre el Worker y el Cliente Streaming. Recibe la data publicada por el Worker y la envia al cliente que la está solicitando.

- Proxy Server: Servidor proxy utilizado para obtener streaming desde la Web de una cámara.

- Streaming Client: Recibe (SUB) y muestra el video streaming en tiempo real junto a la información de las personas detectadas.

## Instalación
Dependencias: OpenCV 4.0.1+, zmq, imutils, Tensorflow 1.8+, faiss, mongoengine, mtcnn, face_recognition, uuid.

- Probado en Ubuntu Linux 16.04 con y sin GPU.
- Instalar OpenCV 4.0.1 o nuevo. Recomendado instalar con ```pip3 install opencv-python``` o compilarlo con soporte para GPU (En caso de tener una).
- Instalar Tensorflow (1.5 o nuevo) ```pip3 install tensorflow``` o ```pip3 install tensorflow-gpu``` (Recomendado).
- Instalar zmq. ````pip3 install pyzmq```
- Instalar imutils ```pip3 install imutils```
- Instalar dlib (Compilar con soporte para GPU, en caso de que se vaya a usar detectionTest.py o worker.py)
- Instalar face_recognition
- Instalar faiss ```pip3 install faiss-cpu``` (Soporte para GPU recomendado).

## Estructura de directorios

La estructura de directorios es la siguiente:

1. **processor**: Contiene el Face Recognition Server, el worker y el detectorTest.
2. **sender:** Contiene el sender.py para enviar streaming hacia el Face Recognition Server.
3. **streaming:** Contiene el Streaming Server y el Client Server.
4. **websocket:** Contiene el servidor proxy y la pagina web de prueba para visualizar streaming desde la web.

## Instrucciones de uso

Se puede usar de las siguentes maneras:
 1. Leer cada frame, procesarlo y enviarlo al servidor de streaming (detectorTest.py) o
 2. Enviar streaming hacia el face recognition streaming, procesarlo en el worker y enviarlo hacia el streaming server. (sender.py) 

En resumen, si se va a utilizar el detectorTest.py, no es necesario iniciar el Face Recognition Server y el worker; en cambio, si se utiliza el sender.py, es necesario utilizar dichos procesos ya que es en estos donde se realiza la detección y el reconocimiento facial para el sender.

#### Enviar streaming o enviar streaming procesado:

- ```python3 processor/detectorTest.py [url-camara]```
- ```python3 sender/sender.py [url-cam1, url-cam2, ..., url-camn]```


Para el primer caso, tiene que estar iniciado el Streaming Server si se quiere obtener streaming procesado de esa cámara. Y, para el segundo caso, tiene que estar iniciado el Face Recognition Server y tener al menos un worker conectado para procesar el stream que envia el sender.

#### Servidor de Reconocimiento facial
- ```sudo service mongod start```
- ```python3 processor/broker.py```
- ```python3 processor/worker.py```

#### Servidor de Streaming
- ```python3 streaming/broker.py```

#### Cliente Desktop
- ```python3 streaming/client.py Client-[url-camara]```

donde [url-camara] es la camara de la cual se quiere obtener streaming procesado.

#### Cliente Web
- Iniciar servidor proxy: ```python3 websocket/server.py```
- Abrir websocket/index.html y en la caja de texto colocar Client-[url-camara] y dar click en streaming.

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

## Licencia

MIT

Contribuidores: **José Chourio**, Adrian Trononis