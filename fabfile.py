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

with open('config.yaml') as yamlf:
    env.config = yaml.load(yamlf)
    env.roledefs = { role: [ host for (host, cfg) in env.config.items() if role in cfg['roles'] ]
                     for role in { role for (host, cfg) in env.config.items() for role in cfg['roles'] } }
    env.use_ssh_config = True

@task
def everything():
    execute(debian.configure)
    execute(debian.nginx.nginx)
    execute(debian.uwsgi.uwsgi)
    execute(debian.postfix.postfix)
    execute(debian.dovecot.dovecot)
