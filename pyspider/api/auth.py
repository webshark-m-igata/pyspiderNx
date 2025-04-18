#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
from flask import request, jsonify

from .app import app

logger = logging.getLogger('api.auth')

def init_auth():
    """Initialize authentication"""
    
    @app.before_request
    def authenticate():
        """Authenticate request"""
        # Skip authentication for OPTIONS requests
        if request.method == 'OPTIONS':
            return None
        
        # Skip authentication for public endpoints
        if request.path in ['/health', '/version']:
            return None
        
        # Get authentication credentials
        auth = request.authorization
        if not auth:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required',
            }), 401
        
        # Validate credentials
        username = app.config.get('username')
        password = app.config.get('password')
        if not username or not password:
            return None
        
        if auth.username != username or auth.password != password:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid credentials',
            }), 401
        
        return None
