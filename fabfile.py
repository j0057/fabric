#!/usr/bin/env python2.7

import json
import itertools
import re

import fabric.api
import fabric.contrib.files
import fabtools.require

from fabric.api import *
#from fabric.contrib.files import comment, sed
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

with open('config.json') as jsonf:
    config = json.load(jsonf)
    env.context = { host: cfg['context'] for (host, cfg) in config.items() }
    env.roledefs = { role: [ host for (host, cfg) in config.items() if role in cfg['roles'] ]
                     for role in { role for (host, cfg) in config.items() for role in cfg['roles'] } }
    env.use_ssh_config = True

    if 0:
        print '------------------'
        print 'HOSTS:', env.hosts
        print 'CONTEXT:', env.context
        print 'ROLEDEFS:', env.roledefs
        print '------------------'

@roles('info')
def info():
    "Just dump some stats"
    print '  hostname:', run('hostname', quiet=True)
    print '  uname -a:', run('uname -a', quiet=True)
    print '  whoami  :', run('whoami', quiet=True)

@roles('debian')
def debian_set_hostname():
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

@roles('debian')
def debian_set_passwords():
    accounts = env.context[env.host_string]['accounts']
    passwords = [ (account, prompt('password for {0}: '.format(account)))
                  for account in accounts
                  if not contains('/etc/passwords_changed', account) ]
    if passwords:
        s = '\\n'.join(':'.join(t) for t in passwords)
        run('echo -e \'{0}\' | chpasswd'.format(s))
        for (a, _) in passwords:
            append('/etc/passwords_changed', a)

@roles('debian')
def debian_create_apt_update_stamp():
    if not exists('/etc/apt/apt.conf.d/15update_stamp'):
        append('/etc/apt/apt.conf.d/15update_stamp',
            'APT::Update::Post-Invoke-Success' 
            ' {"date \'+%s\' >/var/lib/apt/periodic/update-success-stamp'
            ' 2>/dev/null '
            '|| true";}')

@roles('debian-testing')
def debian_update_testing():
    "Upgrade from stable to testing"
    deb.package('sudo')
    with watch([ '/etc/apt/sources.list',
                 '/etc/apt/sources.list.d/testing.list',
                 '/etc/apt/sources.list.d/testing-updates.list' ]) as sources_list_d:
        if fabric.contrib.files.contains('/etc/sources.list', '^deb', escape=False):
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

@roles('debian')
def debian_upgrade():
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


@roles('systemd')
def debian_install_systemd():
    "Install systemd and update grub config"
    if not deb.is_installed('systemd'):
        deb.package('systemd')
        with watch('/etc/default/grub') as etc_default_grub:
            sed('/etc/default/grub', 
                'GRUB_CMDLINE_LINUX_DEFAULT="quiet"', 
                'GRUB_CMDLINE_LINUX_DEFAULT="quiet init=/bin/systemd"')
        if etc_default_grub.changed:
            run('update-grub2')
            fabric.operations.reboot()
            run('/bin/true')

def configure():
    "Configure all the things"
    execute(debian_set_hostname)
    execute(debian_set_passwords)
    execute(debian_create_apt_update_stamp)
    execute(debian_update_testing)
    execute(debian_upgrade)
    execute(debian_install_systemd)
    #xecute(info)

