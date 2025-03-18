from dockerspawner import DockerSpawner
from nativeauthenticator import NativeAuthenticator
import os

c.JupyterHub.authenticator_class = NativeAuthenticator
c.JupyterHub.base_url='/jupyterhub'

c.GenericOAuthenticator.enable_auth_state = True
c.Spawner.http_timeout = 300
c.JupyterHub.log_level = 'DEBUG'
c.JupyterHub.hub_ip = '0.0.0.0'

c.DockerSpawner.network_name = 'jupyterhub'

c.DockerSpawner.remove = True

c.JupyterHub.spawner_class = DockerSpawner
c.NativeAuthenticator.create_system_users = True


notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR') or '/home/jovyan/work'
c.DockerSpawner.notebook_dir = notebook_dir

c.DockerSpawner.volumes = { 'jupyterhub-user-{username}': notebook_dir }
#c.DockerSpawner.image = "jupyterlab-llmextension:latest"

# Persistence
c.JupyterHub.db_url = "sqlite:///data/jupyterhub.sqlite"

# Enable user registration
c.Authenticator.allowed_users = {'ye','myadmin','tester','irene','demo-user'}
c.Authenticator.admin_users = {'myadmin'}
c.NativeAuthenticator.open_signup = True

def pre_spawn_hook(spawner):
    group_names = [group.name for group in spawner.user.groups]
    if 'course1' in group_names:
        spawner.image = 'jupyterlab-customprompt:latest'
    elif 'course2' in group_names:
        spawner.image = 'jupyterlab-nosupport:latest'
    else:
        spawner.image = 'jupyterlab-genericsupport:latest'

c.DockerSpawner.pre_spawn_hook = pre_spawn_hook

c.JupyterHub.services = [
    {
        'name': 'askLLM',
        'url': 'http://127.0.0.1:10101',
        'command': ['flask', 'run', '--port=10101'],
        'environment': {'FLASK_APP': 'logService.py'},
    },
]
c.JupyterHub.load_roles = [
    {
        'name': 'user',
        'scopes': [
            'access:services!service=askLLM',  # access this service
            'self',  # and all of the standard things for a user
        ],
    }
]