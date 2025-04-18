#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2024-04-17 17:00:00

import logging
from flask import request, jsonify

from .app import app

logger = logging.getLogger('api.projects')

@app.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return jsonify({
            'error': 'ProjectDB not configured',
        }), 500
    
    projects = list(projectdb.get_all())
    return jsonify(projects)

@app.route('/projects/<string:project_name>', methods=['GET'])
def get_project(project_name):
    """Get project by name"""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return jsonify({
            'error': 'ProjectDB not configured',
        }), 500
    
    project = projectdb.get(project_name)
    if not project:
        return jsonify({
            'error': 'Project not found',
        }), 404
    
    return jsonify(project)

@app.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return jsonify({
            'error': 'ProjectDB not configured',
        }), 500
    
    project = request.json
    if not project:
        return jsonify({
            'error': 'Invalid project data',
        }), 400
    
    if not project.get('name'):
        return jsonify({
            'error': 'Project name is required',
        }), 400
    
    if projectdb.get(project['name']):
        return jsonify({
            'error': 'Project already exists',
        }), 409
    
    projectdb.insert(project)
    return jsonify(project), 201

@app.route('/projects/<string:project_name>', methods=['PUT'])
def update_project(project_name):
    """Update project by name"""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return jsonify({
            'error': 'ProjectDB not configured',
        }), 500
    
    project = projectdb.get(project_name)
    if not project:
        return jsonify({
            'error': 'Project not found',
        }), 404
    
    update = request.json
    if not update:
        return jsonify({
            'error': 'Invalid project data',
        }), 400
    
    projectdb.update(project_name, update)
    return jsonify(projectdb.get(project_name))

@app.route('/projects/<string:project_name>', methods=['DELETE'])
def delete_project(project_name):
    """Delete project by name"""
    projectdb = app.config.get('projectdb')
    if not projectdb:
        return jsonify({
            'error': 'ProjectDB not configured',
        }), 500
    
    project = projectdb.get(project_name)
    if not project:
        return jsonify({
            'error': 'Project not found',
        }), 404
    
    projectdb.drop(project_name)
    return '', 204
