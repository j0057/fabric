#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-uwsgi')
def install():
    'Install uWSGI'
    deb.packages(['uwsgi', 'uwsgi-plugin-python', 'uwsgi-plugin-python3', 
                  'uwsgi-plugin-cgi'])

@task(default=True)
@roles('debian-uwsgi')
def postfix():
    'Do all the uWSGI things'
    execute(install)
