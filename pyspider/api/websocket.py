#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
import json
import threading
import time
import tornado.websocket
import tornado.web
import tornado.ioloop

logger = logging.getLogger('api.websocket')

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    """WebSocket handler"""
    
    def check_origin(self, origin):
        """Allow cross-origin WebSocket connections"""
        return True
    
    def open(self):
        """Called when a WebSocket connection is opened"""
        logger.info('WebSocket connection opened: %s', self.request.remote_ip)
        self.application.add_client(self)
    
    def on_message(self, message):
        """Called when a message is received from the client"""
        try:
            data = json.loads(message)
            if data.get('type') == 'ping':
                self.write_message(json.dumps({
                    'type': 'pong',
                    'timestamp': time.time(),
                }))
        except Exception as e:
            logger.exception(e)
    
    def on_close(self):
        """Called when a WebSocket connection is closed"""
        logger.info('WebSocket connection closed: %s', self.request.remote_ip)
        self.application.remove_client(self)

class WebSocketServer(object):
    """WebSocket server"""
    
    def __init__(self, host='0.0.0.0', port=5002):
        self.host = host
        self.port = port
        self.clients = set()
        self.application = None
        self.server = None
        self.ioloop = None
        self.thread = None
    
    def add_client(self, client):
        """Add a WebSocket client"""
        self.clients.add(client)
    
    def remove_client(self, client):
        """Remove a WebSocket client"""
        if client in self.clients:
            self.clients.remove(client)
    
    def broadcast(self, message):
        """Broadcast a message to all clients"""
        for client in list(self.clients):
            try:
                client.write_message(message)
            except Exception as e:
                logger.exception(e)
                self.remove_client(client)
    
    def start(self):
        """Start the WebSocket server"""
        def run():
            try:
                self.application = tornado.web.Application([
                    (r'/ws', WebSocketHandler),
                ])
                self.application.add_client = self.add_client
                self.application.remove_client = self.remove_client
                
                self.server = tornado.httpserver.HTTPServer(self.application)
                self.server.listen(self.port, self.host)
                
                self.ioloop = tornado.ioloop.IOLoop.current()
                logger.info('WebSocket server started on %s:%s', self.host, self.port)
                self.ioloop.start()
            except Exception as e:
                logger.exception(e)
        
        self.thread = threading.Thread(target=run)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the WebSocket server"""
        if self.ioloop:
            self.ioloop.add_callback(self.server.stop)
            self.ioloop.add_callback(self.ioloop.stop)
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info('WebSocket server stopped')
