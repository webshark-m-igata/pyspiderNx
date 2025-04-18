#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
from flask import request, jsonify

from .app import app

logger = logging.getLogger('api.tasks')

@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    scheduler_rpc = app.config.get('scheduler_rpc')
    if not scheduler_rpc:
        return jsonify({
            'error': 'Scheduler RPC not configured',
        }), 500
    
    task = request.json
    if not task:
        return jsonify({
            'error': 'Invalid task data',
        }), 400
    
    if not task.get('project') or not task.get('url'):
        return jsonify({
            'error': 'Project and URL are required',
        }), 400
    
    try:
        result = scheduler_rpc.newtask(task)
        if result:
            return jsonify(task), 201
        else:
            return jsonify({
                'error': 'Failed to create task',
            }), 500
    except Exception as e:
        logger.exception(e)
        return jsonify({
            'error': 'Failed to create task',
            'message': str(e),
        }), 500

@app.route('/tasks/<string:project_name>', methods=['GET'])
def get_tasks(project_name):
    """Get tasks by project name"""
    taskdb = app.config.get('taskdb')
    if not taskdb:
        return jsonify({
            'error': 'TaskDB not configured',
        }), 500
    
    status = request.args.get('status')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 20))
    
    tasks = []
    for task in taskdb.get_tasks(project_name, status, offset=offset, limit=limit):
        tasks.append(task)
    
    count = taskdb.count(project_name, status)
    
    return jsonify({
        'count': count,
        'tasks': tasks,
    })

@app.route('/tasks/<string:project_name>/<string:task_id>', methods=['GET'])
def get_task(project_name, task_id):
    """Get task by project name and task ID"""
    taskdb = app.config.get('taskdb')
    if not taskdb:
        return jsonify({
            'error': 'TaskDB not configured',
        }), 500
    
    task = taskdb.get_task(project_name, task_id)
    if not task:
        return jsonify({
            'error': 'Task not found',
        }), 404
    
    return jsonify(task)

@app.route('/tasks/<string:project_name>/<string:task_id>', methods=['DELETE'])
def delete_task(project_name, task_id):
    """Delete task by project name and task ID"""
    taskdb = app.config.get('taskdb')
    if not taskdb:
        return jsonify({
            'error': 'TaskDB not configured',
        }), 500
    
    task = taskdb.get_task(project_name, task_id)
    if not task:
        return jsonify({
            'error': 'Task not found',
        }), 404
    
    taskdb.delete(project_name, task_id)
    return '', 204
