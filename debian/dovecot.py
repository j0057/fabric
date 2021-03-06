import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-dovecot')
def dovecot_install():
    'Install dovecot'
    deb.packages(['dovecot-imapd'])

@task(default=True)
@roles('debian-dovecot')
def dovecot():
    'Do all the dovecot things'
    execute(dovecot_install)
