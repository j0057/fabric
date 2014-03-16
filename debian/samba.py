#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-samba')
def samba_install():
    'Install samba'
    deb.packages(['samba'])

@task
@roles('debian-samba')
def samba_configure_usershares():
    for u in env.config[env.host_string]['samba']['usershare']:
        with settings(hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True): 
            groups = run('su {user} -c \'groups\''.format(**u)).split()
        if 'sambashare' not in groups:
            run('usermod -a -G sambashare {user}'.format(**u))
        with settings(hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True): 
            usershares = run('su {user} -c \'net usershare list\''.format(**u)).split()
        if u['name'] not in usershares:
            cmd = 'su {user} -c \'net usershare add {name} {path} {comment} {acl} guest_ok={guest_ok}\''.format(**u)
            run(cmd)


@task(default=True)
@roles('debian-samba')
def samba():
    'Do all the samba things'
    execute(samba_install)
    execute(samba_configure_usershares)
