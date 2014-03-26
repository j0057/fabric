import fabtools.require

from fabric.api import *
from fabric.contrib.files import *

from fabtools.files import watch
from fabtools.require import deb

@task
@roles('debian-nginx')
def nginx_install():
    'Install nginx'
    deb.package('nginx-full')
    if exists('/etc/nginx/sites-enabled/default'):
        run('rm /etc/nginx/sites-enabled/default')

@task
@roles('debian-nginx')
def nginx_configure():
    'Configure nginx servers'
    for site in env.config[env.host_string]['nginx']['sites']:
        if not exists('/etc/nginx/sites-enabled/' + site):
            run('touch /etc/nginx/sites-enabled/' + site)
    with watch([ '/etc/nginx/sites-enabled/' + site
                 for site in env.config[env.host_string]['nginx']['sites'] ]) as sites:
        for (site, content) in env.config[env.host_string]['nginx']['sites'].items():
            fabtools.require.file('/etc/nginx/sites-enabled/' + site, contents=content)
    if sites.changed:
        run('nginx -t')
        run('systemctl restart nginx')

@task(default=True)
@roles('debian-nginx')
def nginx():
    'Do all the nginx things'
    execute(nginx_install)
    execute(nginx_configure)

