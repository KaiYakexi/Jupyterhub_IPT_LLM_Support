from dockerspawner import DockerSpawner
from nativeauthenticator import NativeAuthenticator
import os

c.Jupyterhub_template.paths=['/srv/jupyterhub/templates']

c.JupyterHub.authenticator_class = NativeAuthenticator
c.JupyterHub.base_url='/jupyterhub'

c.GenericOAuthenticator.enable_auth_state = True
c.Spawner.http_timeout = 300
c.JupyterHub.log_level = 'DEBUG'
c.JupyterHub.hub_ip = '0.0.0.0'
c.Spawner.mem_limit = '4G'
c.DockerSpawner.network_name = 'jupyterhub'

c.DockerSpawner.remove = True

c.JupyterHub.spawner_class = DockerSpawner

c.JupyterHub.db_url = "sqlite:///data/jupyterhub.sqlite"

# Enable user registration
c.Authenticator.allowed_users = {'$ADMIN_USERNAME'}
c.Authenticator.admin_users = {'$ADMIN_USERNAME'}
c.NativeAuthenticator.open_signup = True


def pre_spawn_hook(spawner):
    group_names = [group.name for group in spawner.user.groups]
    if '$COURSE_NAME' in group_names:
        spawner.volumes={ 'jupyterhub-user-{username}': '/home/jovyan/work'}
        spawner.notebook_dir='/home/jovyan/work'
        spawner.image = '$STUDENT_IMAGE_NAME:latest'
    else:
        spawner.image = 'jupyterlab-nocourse:latest'

c.DockerSpawner.pre_spawn_hook = pre_spawn_hook

c.JupyterHub.services = [
    {
        'name': 'askLLM',
        'url': 'http://127.0.0.1:10101',
        'command': [
            'gunicorn',
            '--bind', '127.0.0.1:10101',
            '--workers', '1',
            '--timeout', '120',
            'logService:app'
        ],
        'environment': {
            'FLASK_ENV': 'production'
    }
    }
]
c.JupyterHub.load_roles = [
    {
        'name': 'user',
        'scopes': [
            'access:services!service=askLLM',
            'self',
            'admin:users',
            'admin:groups',
            
        ],
    }
]