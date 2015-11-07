#!/usr/bin/python
# coding: utf-8

from flask import Flask
from flask import jsonify

import os
import sys
import datetime
import json


def create_initial_statistics_db(path):
    sys.stderr.write("create DB statistics file: {}\n".format(path))
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    d = dict()
    d['item-bytes-overtime'] = list()
    #d['item-bytes-overtime'].append(list())
    #d['item-bytes-overtime'][0] = (today, 0, 0)
    d_jsonfied =  json.dumps(d, sort_keys=True,indent=4, separators=(',', ': '))
    with open(path,"w+") as f:
        f.write(d_jsonfied)

def check_db_environmet(path):
    if not os.path.isdir(path):
        os.makedirs(path)
    obj_path = os.path.join(path, 'objects')
    app.config['DB_OBJECT_PATH'] = obj_path
    if not os.path.isdir(obj_path):
        os.makedirs(obj_path)

    obj_path = os.path.join(path, 'data_uncompressed')
    app.config['DB_UNCOMPRESSED_PATH'] = obj_path
    if not os.path.isdir(obj_path):
        os.makedirs(obj_path)

    obj_path = os.path.join(path, 'data_compressed')
    app.config['DB_COMPRESSED_PATH'] = obj_path
    if not os.path.isdir(obj_path):
        os.makedirs(obj_path)

    obj_path = os.path.join(path, 'statistics.db')
    app.config['DB_STATISTICS_FILEPATH'] = obj_path
    if not os.path.isfile(obj_path):
        create_initial_statistics_db(obj_path)


app = Flask(__name__, static_folder='app', static_url_path='')

app.config.from_pyfile('testcolld.cfg', silent=False)
app.config.from_envvar('APP_CONFIG_FILE', silent=True)

# log to stderr
import logging
from logging import StreamHandler
del app.logger.handlers[:]
file_handler = StreamHandler()
app.logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

db_path_root = os.path.join(app.instance_path, app.config['RELATIVE_DB_PATH'])
app.config['DB_ROOT_PATH'] = db_path_root
check_db_environmet(db_path_root)


# application wide global variables and config parameters must be defined here
# (not in `run.py`) for being able to import them in the beginning of the
# views files but we can perfectly imagine a smarter config procedure
app.config['HELLO_WORLD'] = 'Hello Flask!'

# The views modules that contain the application's routes are imported here
# Importing views modules MUST BE in the end of the file to avoid problems
# related to circular imports http://flask.pocoo.org/docs/patterns/packages
import hippod.gui_app

import hippod.api_object_post
import hippod.api_object_get
import hippod.api_resources
