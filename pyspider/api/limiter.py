#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
import time
from flask import request, jsonify

from .app import app

logger = logging.getLogger('api.limiter')

# Rate limiting storage
_rate_limit_storage = {}

def init_rate_limit():
    """Initialize rate limiting"""
    
    @app.before_request
    def rate_limit():
        """Rate limit requests"""
        # Skip rate limiting for OPTIONS requests
        if request.method == 'OPTIONS':
            return None
        
        # Skip rate limiting for public endpoints
        if request.path in ['/health', '/version']:
            return None
        
        # Get client IP address
        client_ip = request.remote_addr
        
        # Get rate limit configuration
        rate = app.config.get('rate_limit_rate', 60)  # requests per minute
        per = app.config.get('rate_limit_per', 60)    # seconds
        
        # Initialize rate limit storage for client
        if client_ip not in _rate_limit_storage:
            _rate_limit_storage[client_ip] = {
                'reset': time.time() + per,
                'remaining': rate,
            }
        
        # Reset rate limit if expired
        if time.time() > _rate_limit_storage[client_ip]['reset']:
            _rate_limit_storage[client_ip] = {
                'reset': time.time() + per,
                'remaining': rate,
            }
        
        # Check if rate limit exceeded
        if _rate_limit_storage[client_ip]['remaining'] <= 0:
            return jsonify({
                'error': 'Too Many Requests',
                'message': 'Rate limit exceeded',
            }), 429
        
        # Decrement remaining requests
        _rate_limit_storage[client_ip]['remaining'] -= 1
        
        # Set rate limit headers
        response = app.make_response(None)
        response.headers['X-RateLimit-Limit'] = str(rate)
        response.headers['X-RateLimit-Remaining'] = str(_rate_limit_storage[client_ip]['remaining'])
        response.headers['X-RateLimit-Reset'] = str(int(_rate_limit_storage[client_ip]['reset']))
        
        return None
