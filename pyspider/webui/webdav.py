#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-6-3 11:29


# Python 3.13 compatibility: WebDAV is disabled
# Create a dummy app that returns 404 for all requests
class DummyApp:
    def __call__(self, environ, start_response):
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'WebDAV is disabled in Python 3.13']

dav_app = DummyApp()
