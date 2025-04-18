#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-24 22:27:45


import sys
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

import pyspider

install_requires = [
    'Flask>=2.0.0',
    'Jinja2>=3.0.0',
    'chardet>=5.0.0',
    'cssselect>=1.2.0',
    "lxml>=4.9.3",
    'pycurl>=7.45.2',
    'requests>=2.28.0',
    'Flask-Login>=0.6.2',
    'u-msgpack-python>=2.7.2',
    'click>=8.1.7',
    'six>=1.16.0',
    'tblib>=3.0.0',
    'tornado>=6.3.3',
    'pyquery>=2.0.0',
]

extras_require_all = [
    'mysql-connector-python>=8.2.0',
    'pymongo>=4.6.1',
    'redis>=5.0.1',  # redis-py-clusterを削除し、新しいredisパッケージのみを使用
    'psycopg2>=2.9.9',
    'elasticsearch>=8.11.0',
    'kombu>=5.3.4',
    'amqp>=5.2.0',
    'SQLAlchemy>=2.0.27',
    'pika>=1.3.2'
]

setup(
    name='pyspider',
    version=pyspider.__version__,

    description='A Powerful Spider System in Python',
    long_description=long_description,

    url='https://github.com/binux/pyspider',

    author='Roy Binux',
    author_email='roy@binux.me',

    license='Apache License, Version 2.0',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',

        'License :: OSI Approved :: Apache Software License',

        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',

        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='scrapy crawler spider webui',

    packages=find_packages(exclude=['data', 'tests*']),

    install_requires=install_requires,

    extras_require={
        'all': extras_require_all,
        'test': [
            'coverage>=7.4.1',
            'Werkzeug>=3.0.1',
            'httpbin>=0.10.0',
            'pyproxy>=0.1.6',
        ]
    },

    package_data={
        'pyspider': [
            'logging.conf',
            'fetcher/phantomjs_fetcher.js',
            'fetcher/splash_fetcher.lua',
            'webui/static/*.js',
            'webui/static/*.css',
            'webui/templates/*'
        ],
    },

    entry_points={
        'console_scripts': [
            'pyspider=pyspider.run:main'
        ]
    },

    test_suite='tests.all_suite',
)
