#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-nfs')
def nfs_install():
    'Install NFS'
    deb.packages(['nfs-kernel-server'])

@task(default=True)
@roles('debian-nfs')
def nfs():
    'Do all the NFS things'
    execute(nfs_install)
