import os.path

import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('data')
def get_files():
    local_dir = 'data/{0}'.format(env.host_string)
    for (remote, local) in env.config[env.host_string]['data'].items():
        get(remote, local_dir + '/' + local)

@task
@roles('data')
def put_files():
    local_dir = 'data/{0}'.format(env.host_string)
    for (remote, local) in env.config[env.host_string]['data'].items():
        put(local_dir + '/' + local, remote)

@task
@roles('data')
def get_db():
    local_dir = 'data/{0}'.format(env.host_string)
    for (db_name, local) in env.config[env.host_string]['mysql'].items():
        print db_name, local

@task
@roles('data')
def put_db():
    local_dir = 'data/{0}'.format(env.host_string)
    for (db_name, local) in env.config[env.host_string]['mysql'].items():
        put(local_dir + '/' + local, '/tmp/{0}.sql'.format(db_name))
        run('echo "drop database if exists {0}" | mysql'.format(db_name))
        run('echo "create database {0}" | mysql'.format(db_name))
        run('mysql -D {0} < /tmp/{0}.sql'.format(db_name))
        run('rm /tmp/{0}.sql'.format(db_name))
