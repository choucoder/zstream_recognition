#!/usr/bin/env python3
import os
from uuid import uuid4
from json import loads, dumps
from client import WebSocketClient
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

class WebSocketServer(WebSocketServerProtocol):
    def __init__(self):
        WebSocketServerProtocol.__init__(self)
        self._terminated = False
        self.subscriptors = {}
    
    def onConnect(self, request):
        print("[INFO] OnConnect request: {}".format(request))

    def onOpen(self):
        print("[INFO] WebSocket is opened.")

    @property
    def terminated(self):
        return self._terminated

    def is_subscribed(self, topic):
        keys = list(self.subscriptors.keys())
        for key in keys:
            try:
                if self.subscriptors[key].topic_filter == topic:
                    return True
            except:
                pass
        return False

    def subscribe(self, topic):
        key = str(uuid4()).replace('-', '')[:8]
        try:
            self.subscriptors[key] = WebSocketClient(
                key=key,
                parent=self,
                sserver_addr='tcp://0.0.0.0:5553',
                topic_filter=topic
            )
            self.subscriptors[key].start()
            print("[INFO] Subscriptor {} was subscribed to video {}".format(key, topic))
        except:
            pass

    def unsubscribe(self, topic):
        toDelete = []
        
        keys = list(self.subscriptors.keys())
        for key in keys:
            if self.subscriptors[key].topic_filter == topic:
                toDelete.append(key)

        for key in toDelete:
            try:
                self.subscriptors[key].terminate()
                del self.subscriptors[key]
            except:
                pass
    
    def terminate(self):
        self._terminated = True
        keys = list(self.subscriptors.keys())
        for key in keys:
            try:
                self.subscriptors[key].terminate()
            except:
                pass

    def onMessage(self, payload, isBinary):
        raw = payload.decode('utf-8')
        msg = loads(raw)

        if msg['signal'] == 0:
            topic_filter = msg['topic']
            if not self.is_subscribed(topic_filter):
                self.subscribe(topic_filter)

        elif msg['signal'] == 1:
            topic_filter = msg['topic']
            if self.is_subscribed(topic_filter):
                self.unsubscribe(topic_filter)
            
        print(msg)

    def onClose(self, wasClean, code, reason):
        print("[INFO] {} {} {}".format(wasClean, code, reason))
        self.terminate()

if __name__ == '__main__':
    import asyncio

    factory = WebSocketServerFactory()
    factory.protocol = WebSocketServer

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, host='0.0.0.0', port=5050)
    server = loop.run_until_complete(coro)

    print("[INFO] WebSocketServer has been created.")

    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        server.close()
        loop.close()