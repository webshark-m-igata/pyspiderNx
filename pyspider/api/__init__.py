#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

from .app import app

# Initialize API components
def init_api():
    """Initialize API components"""
    # Import API modules inside the function to avoid circular imports
    import pyspider.api.projects
    import pyspider.api.tasks
    import pyspider.api.stats
    import pyspider.api.auth
    import pyspider.api.limiter
    import pyspider.api.errors
    import pyspider.api.swagger
    import pyspider.api.batch
    import pyspider.api.websocket
    
    # Initialize error handlers
    pyspider.api.errors.init_error_handlers()

    # Initialize authentication if needed
    if app.config.get('need_auth', False):
        pyspider.api.auth.init_auth()

    # Initialize rate limiting if needed
    if app.config.get('enable_rate_limit', False):
        pyspider.api.limiter.init_rate_limit()

    # Initialize WebSocket server if enabled
    if app.config.get('enable_websocket', False):
        ws_host = app.config.get('websocket_host', '0.0.0.0')
        ws_port = app.config.get('websocket_port', 5002)
        app.websocket_server = pyspider.api.websocket.WebSocketServer(host=ws_host, port=ws_port)
        app.websocket_server.start()

# Initialize API components
init_api()

# Or use before_request with a flag to ensure initialization happens only once
_api_initialized = False

@app.before_request
def initialize_api_before_request():
    global _api_initialized
    if not _api_initialized:
        # init_api() # Already called above
        _api_initialized = True
