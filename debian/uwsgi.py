#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-uwsgi')
def uwsgi_install():
    'Install uWSGI'
    deb.packages(['uwsgi', 'uwsgi-plugin-python', 'uwsgi-plugin-python3', 
                  'uwsgi-plugin-cgi'])

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
    for name in env.config[env.host_string]['uwsgi']:
        if not exists('/etc/systemd/system/sockets.target.wants/uwsgi@{0}.socket'
                      .format(name)):
            run('systemctl enable uwsgi@{0}.socket'.format(name))
            run('systemctl start uwsgi@{0}.socket'.format(name))

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
    --plugins=python --master --workers=1 \\
	--socket=/run/uwsgi/%i.socket \\
	--chdir=/srv/%i --virtualenv=/srv/%i \\
	--module=%i --callable=app \\
	--auto-procname --procname-prefix-spaced=%i
KillSignal=SIGQUIT
Type=notify
StandardOutput=syslog
StandardError=syslog
NotifyAccess=main
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
