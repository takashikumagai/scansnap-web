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

websocket = None
ws_server = None

class ScannerWebSocket(WebSocket):

    def __init__(self, server, sock, address):
        super().__init__(server, sock, address)

    def handleMessage(self):
        logging.info('ws:message received: {}'.format(self.data))

    def handleConnected(self):
        global websocket
        logging.info('ws:connected')
        websocket = self

    def handleClose(self):
        logging.info('ws:closed')

def send_message_to_client(msg):
    global websocket
    print('websocketserver.send_message_to_client',msg)
    websocket.sendMessage(msg)

def start_web_socket_server(ws_port):
    global ws_server

    if ws_server is not None:
        return

    logging.info('Setting up the WebSocket server...')
    try:
        ws_server = SimpleWebSocketServer('', ws_port, ScannerWebSocket)
        logging.debug("Starting a WebSocket server (port: {}).".format(ws_port))
        websocket_server_thread = threading.Thread(target = ws_server.serveforever)
        websocket_server_thread.start()
    except:
        logging.error('websocket exception:', sys.exc_info()[0])
