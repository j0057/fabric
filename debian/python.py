#!/usr/bin/env python2.7

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

def get_installed(outdated=False, path=None):
    with settings(hide('running', 'stdout', 'stderr', 'warnings'), warn_only=True): 
        if outdated:
            output = run(
                '{0} list --outdated --no-index --find-links={1} --local | cat'.format(
                    (path + '/bin/pip') if path else 'pip', env.pypkg_url))
            # this is actually buggy because pip insists on complaining about http
            # ..but who wants to name their package "Ignored" anyway? :-p
            return { pkg.split()[0] for pkg in output.splitlines() }
        else:
            output = run(
                '{0} list --local'.format(
                    (path + '/bin/pip') if path else 'pip'))
            return { pkg.split()[0] for pkg in output.splitlines() }

@task
@roles('debian-python')
def python_install():
    'Install Python'
    deb.packages(['python2.7'])

@task
@roles('debian-python')
def python_install_pip():
    'Install pip (ipip)'
    fabtools.require.deb.package('curl')
    if not fabtools.python.is_pip_installed():
        fabtools.python.install_pip()

@task
@roles('debian-python')
def python_copy_packages():
    'Copy packages to target machine'
    fabtools.require.files.directory(env.pypkg_url)
    for fn in os.listdir(env.pypkg_dir):
        if not fn.endswith('.whl'):
            continue
        fabtools.require.file(
            path=env.pypkg_url + '/' + fn, 
            source=env.pypkg_dir + '/' + fn,
            verify_remote=False)

@task
@roles('debian-python')
def python_install_virtualenv():
    'Make sure pip, virtualenv and setuptools are up to date'
    pkgs = 'pip virtualenv setuptools'.split()
    missing = set(pkgs) - get_installed()
    outdated = set(pkgs) & get_installed(outdated=True)
    if missing or outdated:
        run('pip install --upgrade --no-index --find-links={0} --use-wheel {1}'
            .format(env.pypkg_url, ' '.join(pkgs))) 

@task
@roles('debian-python')
def python_create_envs():
    'Create virtualenvs'
    for e in env.config[env.host_string]['virtualenv']:
        if not fabtools.files.is_dir(e['path']):
            fabtools.require.files.directory(e['path'])
            run('virtualenv --extra-search-dir={0} {1}'.format(env.pypkg_url, e['path']))
            run('chown -R {0}.{1} {2}'.format(e['uid'], e['gid'], e['path']))

@task
@roles('debian-python')
def python_install_packages():
    'Install packages in virtualenvs'
    for e in env.config[env.host_string]['virtualenv']:
        missing = set(e['packages']) - get_installed(path=e['path'])
        if missing:
            run('{0}/bin/pip install --upgrade --no-index --find-links={1} --use-wheel {2}'.format(
                e['path'], 
                env.pypkg_url, 
                ' '.join(e['packages']))) 
            run('chown -R {0}.{1} {2}'.format(e['uid'], e['gid'], e['path']))

@task
@roles('debian-python')
def python_update_packages():
    'Install packages in virtualenvs'
    for e in env.config[env.host_string]['virtualenv']:
        outdated = set(e['packages']) & get_installed(outdated=True, path=e['path'])
        if outdated:
            run('{0}/bin/pip install --upgrade --no-index --find-links={1} --use-wheel {2}'.format(
                e['path'], 
                env.pypkg_url, 
                ' '.join(e['packages']))) 
            run('chown -R {0}.{1} {2}'.format(e['uid'], e['gid'], e['path']))

@task(default=True)
@roles('debian-python')
def python():
    'Do all the Python things'
    execute(python_install)
    execute(python_copy_packages)
    execute(python_install_pip)
    execute(python_install_virtualenv)
    execute(python_create_envs)
    execute(python_install_packages)
