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

@task
@roles('debian-nfs')
def nfs_configure():
    with watch('/etc/exports') as exports:
        for n in env.config[env.host_string]['nfs']['exports']:
            line = '{0:16} {1}({2})'.format(n['path'], n['net'], ','.join(n['options']))
            if not contains('/etc/exports', line):
                append('/etc/exports', line)
    if exports.changed:
        run('systemctl restart nfs-kernel-server')

@task(default=True)
@roles('debian-nfs')
def nfs():
    'Do all the NFS things'
    execute(nfs_install)
    execute(nfs_configure)
