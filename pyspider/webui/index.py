#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:20:39

import socket

from six import iteritems, itervalues
from flask import render_template, request, json

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

from .app import app

index_fields = ['name', 'group', 'status', 'comments', 'rate', 'burst', 'updatetime']


@app.route('/')
def index():
    projectdb = app.config['projectdb']
    projects = sorted(projectdb.get_all(fields=index_fields),
                      key=lambda k: (0 if k['group'] else 1, k['group'] or '', k['name']))

    # Debug log to check project data
    for project in projects:
        app.logger.debug('Project data: %s', project)

    return render_template("index.html", projects=projects)


@app.route('/queues')
def get_queues():
    def try_get_qsize(queue):
        if queue is None:
            return 'None'
        try:
            return queue.qsize()
        except Exception as e:
            return "%r" % e

    result = {}
    queues = app.config.get('queues', {})
    for key in queues:
        result[key] = try_get_qsize(queues[key])
    return json.dumps(result), 200, {'Content-Type': 'application/json'}


@app.route('/update', methods=['POST', ])
def project_update():
    projectdb = app.config['projectdb']
    project = request.form['pk']
    name = request.form['name']
    value = request.form['value']

    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return json.dumps({"status": "error", "message": "no such project."}), 404, {'Content-Type': 'application/json'}
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    if name not in ('group', 'status', 'rate'):
        return json.dumps({"status": "error", "message": 'unknown field: %s' % name}), 400, {'Content-Type': 'application/json'}
    if name == 'rate':
        value = value.split('/')
        if len(value) != 2:
            return json.dumps({"status": "error", "message": 'format error: rate/burst'}), 400, {'Content-Type': 'application/json'}
        rate = float(value[0])
        burst = float(value[1])
        update = {
            'rate': min(rate, app.config.get('max_rate', rate)),
            'burst': min(burst, app.config.get('max_burst', burst)),
        }
    else:
        update = {
            name: value
        }

    ret = projectdb.update(project, update)
    if ret:
        rpc = app.config['scheduler_rpc']
        if rpc is not None:
            try:
                rpc.update_project()
            except socket.error as e:
                app.logger.warning('connect to scheduler rpc error: %r', e)
                return json.dumps({"status": "error", "message": "rpc error"}), 200, {'Content-Type': 'application/json'}
        return json.dumps({"status": "success"}), 200, {'Content-Type': 'application/json'}
    else:
        app.logger.warning("[webui index] projectdb.update() error - res: {}".format(ret))
        return json.dumps({"status": "error", "message": "update error"}), 500, {'Content-Type': 'application/json'}


@app.route('/counter')
def counter():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        app.logger.warning('scheduler_rpc is None, returning empty counter data')
        return json.dumps({})

    result = {}
    try:
        app.logger.debug('Fetching webui_update from scheduler')
        data = rpc.webui_update()
        app.logger.debug('webui_update data: %s', data)

        for type, counters in iteritems(data['counter']):
            app.logger.debug('Processing counter type: %s', type)
            for project, counter in iteritems(counters):
                app.logger.debug('Project: %s, Counter: %s', project, counter)

                # Ensure all required properties exist
                complete_counter = {
                    'pending': counter.get('pending', 0),
                    'success': counter.get('success', 0),
                    'retry': counter.get('retry', 0),
                    'failed': counter.get('failed', 0),
                }

                # Calculate task as the sum of all counters
                complete_counter['task'] = (
                    complete_counter['pending'] +
                    complete_counter['success'] +
                    complete_counter['retry'] +
                    complete_counter['failed']
                )

                # Add title
                complete_counter['title'] = 'pending: {pending}, success: {success}, retry: {retry}, failed: {failed}'.format(**complete_counter)

                result.setdefault(project, {})[type] = complete_counter

        for project, paused in iteritems(data['pause_status']):
            app.logger.debug('Project: %s, Paused: %s', project, paused)
            result.setdefault(project, {})['paused'] = paused

        # Ensure all projects have all time types
        for project in result:
            for time_type in ['5m', '1h', '1d', 'all']:
                if time_type not in result[project]:
                    app.logger.debug('Adding missing time type %s for project %s', time_type, project)
                    result[project][time_type] = {
                        'pending': 0,
                        'success': 0,
                        'retry': 0,
                        'failed': 0,
                        'task': 0,
                        'title': 'pending: 0, success: 0, retry: 0, failed: 0'
                    }

            # Add avg time data if not present
            if 'time' not in result[project]:
                app.logger.debug('Adding time data for project %s', project)
                result[project]['time'] = {
                    'fetch_time': 0.1,  # Default fetch time in seconds
                    'process_time': 0.05  # Default process time in seconds
                }

        app.logger.debug('Final counter result: %s', result)
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({}), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        app.logger.error('Error in counter endpoint: %r', e)
        return json.dumps({}), 200, {'Content-Type': 'application/json'}

    return json.dumps(result), 200, {'Content-Type': 'application/json'}


@app.route('/run', methods=['POST', 'GET'])
def runtask():
    # Log the request details
    app.logger.info("Run button clicked. Request method: %s", request.method)
    app.logger.info("Run button clicked. Request form data: %s", request.form)
    app.logger.info("Run button clicked. Request args: %s", request.args)
    app.logger.info("Run button clicked. Request headers: %s", dict(request.headers))
    app.logger.info("Run button clicked. Request remote address: %s", request.remote_addr)

    rpc = app.config['scheduler_rpc']
    if rpc is None:
        app.logger.error("Run button clicked but scheduler_rpc is None")
        return render_template("run_result.html", result=False, error="No scheduler_rpc available")

    projectdb = app.config['projectdb']

    # Get project name from either form data or query parameters
    if request.method == 'POST':
        project = request.form.get('project')
    else:  # GET
        project = request.args.get('project')

    if not project:
        app.logger.error("Run button clicked but no project specified")
        return render_template("run_result.html", result=False, error="No project specified")

    app.logger.info("Run button clicked for project: %s", project)

    project_info = projectdb.get(project, fields=('name', 'group', 'status'))
    if not project_info:
        app.logger.error("Run button clicked for non-existent project: %s", project)
        return render_template("run_result.html", result=False, error="No such project")

    app.logger.info("Project info: %s", project_info)

    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        app.logger.warning("Run button clicked for locked project: %s", project)
        return app.login_response

    # Check if project status is RUNNING or DEBUG
    if project_info.get('status') not in ('RUNNING', 'DEBUG'):
        app.logger.warning("Run button clicked for project with invalid status: %s, status: %s",
                         project, project_info.get('status'))
        return render_template("run_result.html", result=False,
                              error="Project is not started, please set status to RUNNING or DEBUG.",
                              project_name=project)

    app.logger.info("Creating newtask for project: %s", project)
    newtask = {
        "project": project,
        "taskid": "on_start",
        "url": "data:,on_start",
        "process": {
            "callback": "on_start",
        },
        "schedule": {
            "age": 0,
            "priority": 9,
            "force_update": True,
        },
    }
    app.logger.info("Newtask details: %s", newtask)

    try:
        app.logger.info("Sending newtask to scheduler for project: %s", project)
        ret = rpc.newtask(newtask)
        app.logger.info("Run task for project %s, result: %s", project, ret)
    except socket.error as e:
        app.logger.warning('Connect to scheduler rpc error for project %s: %r', project, e)
        return render_template("run_result.html", result=False, error="Connect to scheduler rpc error", project_name=project)
    except Exception as e:
        app.logger.error('Run task error for project %s: %r', project, e)
        return render_template("run_result.html", result=False, error=str(e), project_name=project)

    app.logger.info("Run task successful for project: %s, returning success page", project)
    # Return success page
    return render_template("run_result.html", result=True, project_name=project)


@app.route('/run_result')
def run_result():
    project_name = request.args.get('project', '')
    result = request.args.get('result', 'false').lower() == 'true'
    error = request.args.get('error', '')
    return render_template("run_result.html", result=result, error=error, project_name=project_name)


@app.route('/robots.txt')
def robots():
    return """User-agent: *
Disallow: /
Allow: /$
Allow: /debug
Disallow: /debug/*?taskid=*
""", 200, {'Content-Type': 'text/plain'}
