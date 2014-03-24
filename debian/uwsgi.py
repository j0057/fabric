#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

import yaml

@task
@roles('debian-uwsgi')
def uwsgi_install():
    'Install uWSGI from unstable'
    for pkg in ['uwsgi', 'uwsgi-plugin-python', 'uwsgi-plugin-python3']:
        if not deb.is_installed(pkg):
            deb.package(pkg + '/unstable')

@task
@roles('debian-uwsgi')
def uwsgi_create_run_uwsgi():
    'Create /run/uwsgi directory'
    if not exists('/etc/tmpfiles.d/run_uwsgi.conf'):
        fabtools.require.file('/etc/tmpfiles.d/run_uwsgi.conf',
            'd /run/uwsgi 0755 www-data www-data - -')
        run('systemctl restart systemd-tmpfiles-setup')

@task
@roles('debian-uwsgi')
def uwsgi_create_systemd_unit_files():
    'Create unit files for socket-activated uWSGI apps (awesome)'
    fabtools.require.file('/etc/systemd/system/uwsgi@.service', UWSGI_SERVICE)
    fabtools.require.file('/etc/systemd/system/uwsgi@.socket', UWSGI_SOCKET)

@task
@roles('debian-uwsgi')
def uwsgi_create_uwsgi_apps():
    'Enable and start sockets for uWSGI apps'
    for app in env.config[env.host_string]['uwsgi']:
        if not exists('/etc/systemd/system/sockets.target.wants/uwsgi@{name}.socket'.format(**app)):
            run('systemctl enable uwsgi@{name}.socket'.format(**app))
            run('systemctl start uwsgi@{name}.socket'.format(**app))
        config = yaml.dump(app['config'], default_flow_style=False)
        if not exists('/etc/uwsgi/apps-enabled/{name}.yaml'.format(**app)):
            run('touch /etc/uwsgi/apps-enabled/{name}.yaml'.format(**app))
        with watch('/etc/uwsgi/apps-enabled/{name}.yaml'.format(**app)) as config_yaml:
            fabtools.require.file('/etc/uwsgi/apps-enabled/{name}.yaml'.format(**app), contents=config)
        if config_yaml.changed:
            run('systemctl stop uwsgi@{name}.service'.format(**app))

@task(default=True)
@roles('debian-uwsgi')
def uwsgi():
    'Do all the uWSGI things'
    execute(uwsgi_install)
    execute(uwsgi_create_run_uwsgi)
    execute(uwsgi_create_systemd_unit_files)
    execute(uwsgi_create_uwsgi_apps)

UWSGI_SERVICE = """
[Unit]
Description=uWSGI server for %i
After=syslog.target

[Service]
ExecStart=/usr/bin/uwsgi \\
    --socket=/run/uwsgi/%i.socket \\
    --yaml=/etc/uwsgi/apps-enabled/%i.yaml
KillSignal=SIGQUIT
Type=notify
StandardOutput=syslog
StandardError=syslog
NotifyAccess=all
User=www-data
Group=www-data
"""

UWSGI_SOCKET = """
[Unit]
Description=uWSGI socket for %i

[Socket]
ListenStream=/run/uwsgi/%i.socket
User=www-data
Group=www-data

[Install]
WantedBy=sockets.target
"""
