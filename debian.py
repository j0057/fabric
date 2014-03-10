#!/usr/bin/env python2.7

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
def set_hostname():
    "Sets the right hostname based on context"
    current = run('hostname', quiet=True)
    wanted = env.context[env.host_string]['hostname']
    if current != wanted:
        with watch([ '/etc/hostname',
                     '/etc/hosts' ]) as etc_host:
            sed('/etc/hostname', current, wanted)
            sed('/etc/hosts', current, wanted)
        if etc_host.changed:
            run('hostname {0}'.format(wanted))

@task
@roles('debian')
def set_passwords():
    accounts = env.context[env.host_string]['accounts']
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
def create_apt_update_stamp():
    if not exists('/etc/apt/apt.conf.d/15update_stamp'):
        append('/etc/apt/apt.conf.d/15update_stamp',
            'APT::Update::Post-Invoke-Success' 
            ' {"date \'+%s\' >/var/lib/apt/periodic/update-success-stamp'
            ' 2>/dev/null '
            '|| true";}')

@task
@roles('debian-testing')
def update_testing():
    "Upgrade from stable to testing"
    deb.package('sudo')
    with watch([ '/etc/apt/sources.list',
                 '/etc/apt/sources.list.d/testing.list',
                 '/etc/apt/sources.list.d/testing-updates.list' ]) as sources_list_d:
        if contains('/etc/apt/sources.list', '^deb', escape=False):
            comment('/etc/apt/sources.list', '^deb', use_sudo=True)
            components = ['main', 'contrib', 'non-free']
            deb.source('testing', 'http://ftp.nl.debian.org/debian/', 'testing', *components)
            deb.source('testing-updates', 'http://security.debian.org/', 'testing/updates', *components)
    if sources_list_d.changed:
        run('DEBIAN_FRONTEND=noninteractive APT_LISTCHANGES_FRONTED=none apt-get'
            ' -o Dpkg::Options::="--force-confnew"'
            ' --force-yes'
            ' -fuy'
            ' --quiet'
            ' dist-upgrade')

@task
@roles('debian')
def upgrade():
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
def install_systemd():
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
def bounce():
    "Reboot the server"
    reboot()

@task(default=True)
def configure():
    "Configure all the things"
    execute(set_hostname)
    execute(set_passwords)
    execute(create_apt_update_stamp)
    execute(update_testing)
    execute(upgrade)
    execute(install_systemd)

