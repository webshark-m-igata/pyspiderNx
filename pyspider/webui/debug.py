#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-23 00:19:06


import sys
import time
import socket
import inspect
import datetime
import traceback
from flask import render_template, request, json, redirect

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

from pyspider.libs import utils, sample_handler, dataurl
from pyspider.libs.response import rebuild_response
from pyspider.processor.project_module import ProjectManager, ProjectFinder
from .app import app

default_task = {
    'taskid': 'data:,on_start',
    'project': '',
    'url': 'data:,on_start',
    'process': {
        'callback': 'on_start',
    },
}
default_script = inspect.getsource(sample_handler)


@app.route('/debug/<project>', methods=['GET', 'POST'])
def debug(project):
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    info = projectdb.get(project, fields=['name', 'script'])
    if info:
        script = info['script']
    else:
        script = (default_script
                  .replace('__DATE__', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                  .replace('__PROJECT_NAME__', project)
                  .replace('__START_URL__', request.values.get('start-urls') or '__START_URL__'))

    taskid = request.args.get('taskid')
    if taskid:
        taskdb = app.config['taskdb']
        task = taskdb.get_task(
            project, taskid, ['taskid', 'project', 'url', 'fetch', 'process'])
    else:
        task = default_task

    default_task['project'] = project
    return render_template("debug.html", task=task, script=script, project_name=project)


# Initialize projects import
_projects_import_initialized = False

@app.before_request
def enable_projects_import():
    global _projects_import_initialized
    if not _projects_import_initialized:
        sys.meta_path.append(ProjectFinder(app.config['projectdb']))
        _projects_import_initialized = True


@app.route('/debug/<project>/run', methods=['POST', ])
def run(project):
    start_time = time.time()
    try:
        task = utils.decode_unicode_obj(json.loads(request.form['task']))
    except Exception:
        result = {
            'fetch_result': "",
            'logs': u'task json error',
            'follows': [],
            'messages': [],
            'result': None,
            'time': time.time() - start_time,
        }
        return json.dumps(utils.unicode_obj(result)), \
            200, {'Content-Type': 'application/json'}

    project_info = {
        'name': project,
        'status': 'DEBUG',
        'script': request.form['script'],
    }

    # WebDAV mode has been removed

    fetch_result = {}
    try:
        module = ProjectManager.build_module(project_info, {
            'debugger': True,
            'process_time_limit': app.config['process_time_limit'],
        })

        # The code below is to mock the behavior that crawl_config been joined when selected by scheduler.
        # but to have a better view of joined tasks, it has been done in BaseHandler.crawl when `is_debugger is True`
        # crawl_config = module['instance'].crawl_config
        # task = module['instance'].task_join_crawl_config(task, crawl_config)

        fetch_result = app.config['fetch'](task)
        response = rebuild_response(fetch_result)

        ret = module['instance'].run_task(module['module'], task, response)
    except Exception:
        type, value, tb = sys.exc_info()
        tb = utils.hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        result = {
            'fetch_result': fetch_result,
            'logs': logs,
            'follows': [],
            'messages': [],
            'result': None,
            'time': time.time() - start_time,
        }
    else:
        result = {
            'fetch_result': fetch_result,
            'logs': ret.logstr(),
            'follows': ret.follows,
            'messages': ret.messages,
            'result': ret.result,
            'time': time.time() - start_time,
        }
        result['fetch_result']['content'] = response.text
        if (response.headers.get('content-type', '').startswith('image')):
            result['fetch_result']['dataurl'] = dataurl.encode(
                response.content, response.headers['content-type'])

    try:
        # binary data can't encode to JSON, encode result as unicode obj
        # before send it to frontend
        return json.dumps(utils.unicode_obj(result)), 200, {'Content-Type': 'application/json'}
    except Exception:
        type, value, tb = sys.exc_info()
        tb = utils.hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        result = {
            'fetch_result': "",
            'logs': logs,
            'follows': [],
            'messages': [],
            'result': None,
            'time': time.time() - start_time,
        }
        return json.dumps(utils.unicode_obj(result)), 200, {'Content-Type': 'application/json'}


@app.route('/debug/<project>/save', methods=['POST', ])
def save(project):
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    script = request.form['script']
    project_info = projectdb.get(project, fields=['name', 'status', 'group'])
    if project_info and 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    if project_info:
        info = {
            'script': script,
        }
        if project_info.get('status') in ('DEBUG', 'RUNNING', ):
            info['status'] = 'CHECKING'
        projectdb.update(project, info)
    else:
        info = {
            'name': project,
            'script': script,
            'status': 'TODO',
            'rate': app.config.get('max_rate', 1),
            'burst': app.config.get('max_burst', 3),
        }
        projectdb.insert(project, info)

    rpc = app.config['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            app.logger.warning('connect to scheduler rpc error: %r', e)
            return 'rpc error', 200

    return 'ok', 200


@app.route('/debug/<project>/get')
def get_script(project):
    projectdb = app.config['projectdb']
    if not projectdb.verify_project_name(project):
        return 'project name is not allowed!', 400
    info = projectdb.get(project, fields=['name', 'script'])
    return json.dumps(utils.unicode_obj(info)), \
        200, {'Content-Type': 'application/json'}


@app.route('/blank.html')
def blank_html():
    return ""


@app.route('/debug/new', methods=['POST'])
def new_project():
    projectdb = app.config['projectdb']
    project_name = request.form.get('project-name')
    start_urls = request.form.get('start-urls')
    script_mode = request.form.get('script-mode', 'script')

    if not projectdb.verify_project_name(project_name):
        return 'project name is not allowed!', 400

    # プロジェクト名が既に存在する場合、一意になるように番号を追加
    original_name = project_name
    counter = 1
    while projectdb.get(project_name):
        project_name = f"{original_name}_{counter}"
        counter += 1
        # 新しい名前が検証に合格するか確認
        if not projectdb.verify_project_name(project_name):
            return 'generated project name is not allowed!', 400

    script = (default_script
              .replace('__DATE__', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
              .replace('__PROJECT_NAME__', project_name)
              .replace('__START_URL__', start_urls or '__START_URL__'))

    info = {
        'name': project_name,
        'script': script,
        'status': 'TODO',
        'rate': app.config.get('max_rate', 1),
        'burst': app.config.get('max_burst', 3),
    }
    projectdb.insert(project_name, info)

    # 元の名前と異なる場合はユーザーに通知するためにフラッシュメッセージを設定
    if original_name != project_name:
        app.logger.info(f'Project name changed from {original_name} to {project_name} to avoid duplication')
        # フラッシュメッセージをセッションに追加（Flaskのflashを使用）
        try:
            from flask import flash
            flash(f'プロジェクト名が重複しているため、{original_name}から{project_name}に変更されました。', 'warning')
        except Exception as e:
            app.logger.error(f'Failed to set flash message: {e}')

    rpc = app.config['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            app.logger.warning('connect to scheduler rpc error: %r', e)

    return redirect('/debug/' + project_name)
