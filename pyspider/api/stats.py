#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
from flask import jsonify

from .app import app

logger = logging.getLogger('api.stats')

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get scheduler statistics"""
    scheduler_rpc = app.config.get('scheduler_rpc')
    if not scheduler_rpc:
        return jsonify({
            'error': 'Scheduler RPC not configured',
        }), 500
    
    try:
        result = scheduler_rpc.webui_update()
        return jsonify(result)
    except Exception as e:
        logger.exception(e)
        return jsonify({
            'error': 'Failed to get statistics',
            'message': str(e),
        }), 500

@app.route('/stats/<string:project_name>', methods=['GET'])
def get_project_stats(project_name):
    """Get project statistics"""
    scheduler_rpc = app.config.get('scheduler_rpc')
    if not scheduler_rpc:
        return jsonify({
            'error': 'Scheduler RPC not configured',
        }), 500
    
    try:
        result = scheduler_rpc.webui_update()
        
        project_stats = {
            'counter': {},
            'paused': False,
        }
        
        for counter_type, counters in result.get('counter', {}).items():
            if project_name in counters:
                project_stats['counter'][counter_type] = counters[project_name]
        
        if project_name in result.get('pause_status', {}):
            project_stats['paused'] = result['pause_status'][project_name]
        
        return jsonify(project_stats)
    except Exception as e:
        logger.exception(e)
        return jsonify({
            'error': 'Failed to get project statistics',
            'message': str(e),
        }), 500
