import json
import itertools
import re

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian')
def deb_set_hostname():
    "Sets the right hostname based on config"
    current = run('hostname', quiet=True)
    wanted = env.config[env.host_string]['hostname']
    if current != wanted:
        with watch([ '/etc/hostname',
                     '/etc/hosts' ]) as etc_host:
            sed('/etc/hostname', current, wanted)
            sed('/etc/hosts', current, wanted)
        if etc_host.changed:
            run('hostname {0}'.format(wanted))

@task
@roles('debian')
def deb_set_passwords():
    'Sets the passwords based on user input'
    accounts = env.config[env.host_string]['accounts']
    passwords = [ (account, prompt('password for {0}: '.format(account)))
                  for account in accounts
                  if not contains('/etc/passwords_changed', account) ]
    if passwords:
        s = '\\n'.join(':'.join(t) for t in passwords)
        run('echo -e \'{0}\' | chpasswd'.format(s))
        for (a, _) in passwords:
            append('/etc/passwords_changed', a)
@task
@roles('debian')
def deb_apt_get_install():
    'Install apt packages'
    fabtools.require.deb.packages(env.config[env.host_string]['apt'])

@task
@roles('debian')
def deb_create_apt_update_stamp():
    "Create a time stamp on apt-get update"
    if not exists('/etc/apt/apt.conf.d/15update_stamp'):
        append('/etc/apt/apt.conf.d/15update_stamp',
            'APT::Update::Post-Invoke-Success' 
            ' {"date \'+%s\' >/var/lib/apt/periodic/update-success-stamp'
            ' 2>/dev/null '
            '|| true";}')

@task
@roles('debian-testing')
def deb_update_testing():
    "Upgrade from stable to testing"
    with watch([ '/etc/apt/sources.list',
                 '/etc/apt/sources.list.d/stable.list',
                 '/etc/apt/sources.list.d/stable-updates.list',
                 '/etc/apt/sources.list.d/unstable.list',
                 '/etc/apt/sources.list.d/testing.list',
                 '/etc/apt/sources.list.d/testing-updates.list' ]) as sources_list_d:
        if contains('/etc/apt/sources.list', '^deb', escape=False):
            comment('/etc/apt/sources.list', '^deb', use_sudo=True)
            components = ['main', 'contrib', 'non-free']
            deb.source('stable',            'http://ftp.nl.debian.org/debian/', 'stable', *components)
            deb.source('stable-updates',    'http://security.debian.org/',      'stable/updates', *components)
            deb.source('testing',           'http://ftp.nl.debian.org/debian/', 'testing', *components)
            deb.source('testing-updates',   'http://security.debian.org/',      'testing/updates', *components)
            deb.source('unstable',          'http://ftp.nl.debian.org/debian/', 'unstable', *components)
    fabtools.require.file('/etc/apt/preferences.d/testing', 'Package: *\nPin: release a=testing\nPin-Priority: 901\n')
    fabtools.require.file('/etc/apt/preferences.d/stable', 'Package: *\nPin: release a=stable\nPin-Priority: -2\n')
    fabtools.require.file('/etc/apt/preferences.d/unstable', 'Package: *\nPin: release a=unstable\nPin-Priority: -1\n')
    if sources_list_d.changed:
        run('DEBIAN_FRONTEND=noninteractive APT_LISTCHANGES_FRONTED=none apt-get'
            ' -o Dpkg::Options::="--force-confnew"'
            ' --force-yes'
            ' -fuy'
            ' --quiet'
            ' dist-upgrade')

@task
@roles('debian')
def deb_upgrade(dist=False):
    'Upgrade everything'
    with watch('/var/lib/apt/periodic/update-success-stamp') as update:
        deb.uptodate_index(max_age=3600)
    if update.changed:
        run('DEBIAN_FRONTED=noninteractive APT_LISTCHANGES_FRONTEND=none apt-get'
                ' -o Dpkg::Options::="--force-confnew"'
                ' --force-yes'
                ' -fuy'
                ' --quiet'
                ' upgrade')
        run('DEBIAN_FRONTED=noninteractive APT_LISTCHANGES_FRONTEND=none apt-get'
                ' -o Dpkg::Options::="--force-confnew"'
                ' --force-yes'
                ' -fuy'
                ' --quiet'
                ' autoremove')

@task
@roles('debian-systemd')
def deb_install_systemd():
    "Install systemd and update grub config"
    if not deb.is_installed('systemd'):
        deb.package('systemd')
        with watch('/etc/default/grub') as etc_default_grub:
            sed('/etc/default/grub', 
                'GRUB_CMDLINE_LINUX_DEFAULT="quiet"', 
                'GRUB_CMDLINE_LINUX_DEFAULT="quiet init=/bin/systemd"')
        if etc_default_grub.changed:
            run('update-grub2')
            reboot()
            run('/bin/true')

@task
@roles('debian')
def deb_bounce():
    "Reboot the server"
    reboot()
    run('/bin/true')

@task(default=True)
@roles('debian')
def deb_main():
    "Configure all the things"
    execute(deb_set_hostname)
    execute(deb_set_passwords)
    execute(deb_apt_get_install)
    execute(deb_create_apt_update_stamp)
    execute(deb_update_testing)
    execute(deb_upgrade)
    execute(deb_install_systemd)

