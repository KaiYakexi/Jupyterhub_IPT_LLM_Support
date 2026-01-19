from dockerspawner import DockerSpawner
from nativeauthenticator import NativeAuthenticator
import os

# Templates
c.JupyterHub.template_paths = ['/srv/jupyterhub/templates']

# Core Hub
c.JupyterHub.authenticator_class = NativeAuthenticator
c.JupyterHub.log_level = 'DEBUG'
c.JupyterHub.hub_ip = '0.0.0.0'
c.JupyterHub.db_url = "sqlite:///data/jupyterhub.sqlite"

# Auth
c.Authenticator.allowed_users = {'admin'}
c.Authenticator.admin_users = {'admin'}
c.NativeAuthenticator.open_signup = True

# Spawner
c.Spawner.http_timeout = 300
c.DockerSpawner.mem_limit = '4G'
c.DockerSpawner.network_name = 'jupyterhub'
c.DockerSpawner.remove = True
c.JupyterHub.spawner_class = DockerSpawner

def pre_spawn_hook(spawner):
    group_names = [g.name for g in spawner.user.groups]
    # Not required if you only host one course
    #if 'courseone' in group_names:
    spawner.volumes = {
            'jupyterhub-user-{username}': '/home/jovyan/work'    #,
         #   '$ABSOLUTE_PATH_TO_COURSE_DIRECTORY': '/tmp/source',  # ensure this exists on the host
    }
    spawner.notebook_dir = '/home/jovyan/work'
    spawner.image = 'jupyterlab-students:latest'
    #else:
    #    spawner.image = 'jupyterlab-nocourse:latest'

c.DockerSpawner.pre_spawn_hook = pre_spawn_hook

# Services
c.JupyterHub.services = [
    {
        'name': 'askLLM',
        'url': 'http://127.0.0.1:10101',
        'command': [
            'gunicorn', '--bind', '127.0.0.1:10101',
            '--workers', '1', '--timeout', '120',
            'logService:app'
        ],
        'environment': {'FLASK_ENV': 'production'},
    },
    {
        'name': 'cull-idle',
        'command': ['python3', '-m', 'jupyterhub_idle_culler', '--timeout=3600'],
        'admin': True,
    },
]