#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
import json
import os
from flask import jsonify, render_template, send_from_directory

from .app import app

logger = logging.getLogger('api.swagger')

@app.route('/swagger.json', methods=['GET'])
def swagger_json():
    """Get Swagger JSON specification"""
    swagger_path = os.path.join(os.path.dirname(__file__), 'swagger.json')
    if os.path.exists(swagger_path):
        with open(swagger_path, 'r') as f:
            return jsonify(json.load(f))
    else:
        return jsonify({
            'swagger': '2.0',
            'info': {
                'title': 'PySpider API',
                'description': 'PySpider API Documentation',
                'version': '1.0.0',
            },
            'host': 'localhost:5000',
            'basePath': '/',
            'schemes': ['http'],
            'paths': {},
        })

@app.route('/docs', methods=['GET'])
def swagger_ui():
    """Get Swagger UI"""
    return render_template('swagger.html')
