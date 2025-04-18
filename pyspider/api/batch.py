#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
from flask import request, jsonify

from .app import app

logger = logging.getLogger('api.batch')

@app.route('/batch/tasks', methods=['POST'])
def batch_create_tasks():
    """Create multiple tasks"""
    scheduler_rpc = app.config.get('scheduler_rpc')
    if not scheduler_rpc:
        return jsonify({
            'error': 'Scheduler RPC not configured',
        }), 500
    
    tasks = request.json
    if not tasks or not isinstance(tasks, list):
        return jsonify({
            'error': 'Invalid tasks data',
        }), 400
    
    results = []
    for task in tasks:
        if not task.get('project') or not task.get('url'):
            results.append({
                'success': False,
                'error': 'Project and URL are required',
            })
            continue
        
        try:
            result = scheduler_rpc.newtask(task)
            if result:
                results.append({
                    'success': True,
                    'task': task,
                })
            else:
                results.append({
                    'success': False,
                    'error': 'Failed to create task',
                })
        except Exception as e:
            logger.exception(e)
            results.append({
                'success': False,
                'error': str(e),
            })
    
    return jsonify(results)

@app.route('/batch/projects', methods=['POST'])
def batch_update_projects():
    """Update multiple projects"""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return jsonify({
            'error': 'ProjectDB not configured',
        }), 500
    
    updates = request.json
    if not updates or not isinstance(updates, dict):
        return jsonify({
            'error': 'Invalid updates data',
        }), 400
    
    results = {}
    for project_name, update in updates.items():
        project = projectdb.get(project_name)
        if not project:
            results[project_name] = {
                'success': False,
                'error': 'Project not found',
            }
            continue
        
        try:
            projectdb.update(project_name, update)
            results[project_name] = {
                'success': True,
            }
        except Exception as e:
            logger.exception(e)
            results[project_name] = {
                'success': False,
                'error': str(e),
            }
    
    return jsonify(results)
