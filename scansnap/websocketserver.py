from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import logging
import sys
import threading

# The WebSocket library is from this repo:
# https://github.com/dpallot/simple-websocket-server
# 
# We import two classes for our tasks:
# - WebSocket: we derive a class from this and define custom behaviors
#   of our web socket server.
# - SimpleWebSocketServer: this one is simply instantiated 


class ScannerWebSocket(WebSocket):
    websocket = None
    ws_server = None

    def __init__(self, server, sock, address):
        super().__init__(server, sock, address)

    def handleMessage(self):
        logging.info('ws:message received: {}'.format(self.data))

    def handleConnected(self):
        logging.info('ws:connected')
        self.__class__.websocket = self

    def handleClose(self):
        logging.info('ws:closed')

def send_message_to_client(msg):
    print('websocketserver.send_message_to_client',msg)
    if ScannerWebSocket.websocket:
        ScannerWebSocket.websocket.sendMessage(msg)

def start_web_socket_server(ws_port):

    if ScannerWebSocket.ws_server:
        return

    logging.info('Setting up the WebSocket server...')
    try:
        ScannerWebSocket.ws_server = SimpleWebSocketServer('', ws_port, ScannerWebSocket)
        logging.debug("Starting a WebSocket server (port: {}).".format(ws_port))
        websocket_server_thread = threading.Thread(
            target = ScannerWebSocket.ws_server.serveforever
        )
        websocket_server_thread.start()
    except:
        logging.error('websocket exception:', sys.exc_info()[0])
