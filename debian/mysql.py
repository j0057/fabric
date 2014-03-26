
import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-mysql')
def mysql_install():
    deb.package('mariadb-server')

@task(default=True)
@roles('debian-mysql')
def mysql():
    execute(mysql_install)
