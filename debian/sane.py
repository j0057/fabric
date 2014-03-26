import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-sane')
def sane_install():
    'Install sane'
    deb.packages(['libsane', 'sane-utils', 'hplip'])

@task(default=True)
@roles('debian-sane')
def sane():
    'Do all the sane things'
    execute(sane_install)
