#!/usr/bin/env python2.7

import json
import itertools
import re

import fabric.api
import fabric.contrib.files

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

import yaml

import debian
import debian.nginx
import debian.postfix
import debian.dovecot
import debian.uwsgi
import debian.python

def load_yaml(path):
    with open(path) as f:
        return yaml.load(f)

env.config = load_yaml('config.yaml')
env.roledefs = { role: [ host for (host, cfg) in env.config.items() if role in cfg['roles'] ]
                 for role in { role for (host, cfg) in env.config.items() for role in cfg['roles'] } }
env.update(load_yaml('settings.yaml'))

@task
def go():
    execute(debian.main)
    execute(debian.nginx.main)
    execute(debian.uwsgi.main)
    execute(debian.postfix.main)
    execute(debian.dovecot.main)
    execute(debian.python.main)
