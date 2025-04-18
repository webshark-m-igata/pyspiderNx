#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import os
import logging
from flask import Flask

logger = logging.getLogger('api')

class APIFlask(Flask):
    """API Flask application"""
    
    @property
    def logger(self):
        return logger
    
    def run(self, host=None, port=None, debug=None, **options):
        """Run the API server"""
        import tornado.wsgi
        import tornado.ioloop
        import tornado.httpserver
        
        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = self.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000
        if debug is not None:
            self.debug = bool(debug)
        
        hostname = host
        port = port
        application = self
        
        if self.debug:
            from werkzeug.debug import DebuggedApplication
            application = DebuggedApplication(application, True)
        
        container = tornado.wsgi.WSGIContainer(application)
        self.http_server = tornado.httpserver.HTTPServer(container)
        self.http_server.listen(port, hostname)
        
        self.logger.info('api running on %s:%s', hostname, port)
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ioloop.start()
    
    def quit(self):
        """Quit the API server"""
        if hasattr(self, 'ioloop'):
            self.ioloop.add_callback(self.http_server.stop)
            self.ioloop.add_callback(self.ioloop.stop)
        self.logger.info('api exiting...')

# Create Flask application
app = APIFlask('api',
               static_folder=os.path.join(os.path.dirname(__file__), 'static'),
               template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.urandom(24)

# Configure application
app.config.update({
    'DEBUG': False,
    'TESTING': False,
    'SECRET_KEY': os.urandom(24),
    'JSONIFY_PRETTYPRINT_REGULAR': True,
    'JSON_AS_ASCII': False,
    'JSON_SORT_KEYS': True,
    'PRESERVE_CONTEXT_ON_EXCEPTION': False,
})
