#!/usr/bin/env python2.7

import fabric.api
import fabric.contrib.files
import fabtools.require

fabric.api.env.hosts = [
    'root@xi.fritz.box:20022'
]

context = {
    'root@xi.fritz.box:20022': {
        'hostname': 'debian-vbox'
    }
}

def info():
    fabric.api.run('echo {0}'.format(fabric.api.env.host_string))
    fabric.api.run('hostname')
    fabric.api.run('uname -a')
    fabric.api.run('whoami')

def set_hostname():
    current = fabric.api.run('hostname')
    wanted = context[fabric.api.env.host_string]['hostname']
    if current != wanted:
        fabric.contrib.files.sed('/etc/hostname', current, wanted)
        fabric.api.run('hostname {0}'.format(wanted))
        
def update_testing():
    components = ['main', 'contrib', 'non-free']
    fabtools.require.deb.package('sudo')
    with fabtools.files.watch([ '/etc/apt/sources.list.d/testing.list',
                                '/etc/apt/sources.list.d/testing-updates.list' ]) as watch:
        fabric.contrib.files.comment('/etc/apt/sources.list', '^deb', use_sudo=True)
        fabtools.require.deb.source('testing', 'http://ftp.nl.debian.org/debian/', 'testing', *components)
        fabtools.require.deb.source('testing-updates', 'http://security.debian.org/', 'testing/updates', *components)
    if watch.changed or True:
        fabric.api.run('DEBIAN_FRONTEND=noninteractive apt-get'
                       ' -o Dpkg::Options::="--force-confnew"'
                       ' --force-yes'
                       ' -fuy'
                       ' --quiet'
                       ' dist-upgrade')

