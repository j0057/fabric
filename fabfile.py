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

#with open('config.json') as jsonf:
#    config = json.load(jsonf)

with open('config.yaml') as yamlf:
    config = yaml.load(yamlf)

servers = config['root@127.0.0.1:20022']['context']['nginx']
print servers['test-site']
print

env.context = { host: cfg['context'] for (host, cfg) in config.items() }
env.roledefs = { role: [ host for (host, cfg) in config.items() if role in cfg['roles'] ]
                 for role in { role for (host, cfg) in config.items() for role in cfg['roles'] } }
env.use_ssh_config = True

if 0:
    print '------------------'
    print 'HOSTS:', env.hosts
    print 'CONTEXT:', env.context
    print 'ROLEDEFS:', env.roledefs
    print '------------------'

@roles('info')
def info():
    "Just dump some stats"
    print '  hostname:', run('hostname', quiet=True)
    print '  uname -a:', run('uname -a', quiet=True)
    print '  whoami  :', run('whoami', quiet=True)
