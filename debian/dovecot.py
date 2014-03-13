#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-dovecot')
def install():
    'Install dovecot'
    deb.packages(['dovecot-imapd'])

@task(default=True)
@roles('debian-dovecot')
def main():
    'Do all the dovecot things'
    execute(install)
