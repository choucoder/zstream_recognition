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

- Streaming Client: Recibe y muestra el video streaming junto a la información de las personas detectadas.