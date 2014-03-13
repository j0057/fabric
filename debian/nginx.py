#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-nginx')
def install():
    'Install nginx'
    deb.package('nginx-full')
    if exists('/etc/nginx/sites-enabled/default'):
        run('rm /etc/nginx/sites-enabled/default')

@task
@roles('debian-nginx')
def configure():
    'Configure nginx servers'
    for (site, content) in env.config[env.host_string]['nginx'].items():
        fabtools.require.file(site, contents=content)

@task(default=True)
@roles('debian-nginx')
def main():
    'Do all the nginx things'
    execute(install)
    execute(configure)
    run('systemctl restart nginx.service')

