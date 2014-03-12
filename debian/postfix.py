#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-postfix')
def install():
    'Install postfix and friends'
    deb.packages(['postfix', 'postgrey', 'postfix-policyd-spf-python'])

def ensure_directive(filename, key, *values):
    value = ', '.join(values)
    regex = '^{0} ='.format(key)
    if contains(filename, regex, escape=False):
        if not contains(filename, '{0} = {1}'.format(key, value), exact=True):
            sed(filename, regex + '.*$', '{0} = {1}'.format(key, value))
    else:
        append(filename, '{0} = {1}'.format(key, value))

@task
@roles('debian-postfix')
def configure():
    config = env.config[env.host_string]['postfix']

    with watch('/etc/mailname') as mailname:
        fabtools.require.file('/etc/mailname', config['mailname'])

    with watch('/etc/postfix/main.cf') as main_cf:
        for (key, value) in config['main.cf'].items():
            if isinstance(value, list):
                ensure_directive('/etc/postfix/main.cf', key, *value)
            else:
                ensure_directive('/etc/postfix/main.cf', key, value)

    with watch('/etc/postfix/master.cf') as master_cf:
        if not contains('/etc/postfix/master.cf', 'policy-spf'):
            append('/etc/postfix/master.cf', config['master.cf'])

    if not exists('/etc/postfix/virtual'):
        run('touch /etc/postfix/virtual')
    with watch('/etc/postfix/virtual') as virtual:
        fabtools.require.file('/etc/postfix/virtual', config['virtual'])
    if virtual.changed:
        run('postmap /etc/postfix/virtual')

    if any([mailname.changed, main_cf.changed, master_cf.changed, virtual.changed]):
        run('systemctl restart postfix.service')

@task(default=True)
@roles('debian-postfix')
def postfix():
    'Do all the postfix things'
    execute(install)
    execute(configure)
