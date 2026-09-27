from dockerspawner import DockerSpawner
import nativeauthenticator
import os

# Core Hub
c.JupyterHub.authenticator_class = 'native'
c.JupyterHub.template_paths = [f"{os.path.dirname(nativeauthenticator.__file__)}/templates/"]
c.JupyterHub.log_level = os.environ.get('JUPYTERHUB_LOG_LEVEL', 'INFO')
c.JupyterHub.hub_ip = '0.0.0.0'
# hub_ip above is only the BIND address (what the Hub listens on inside its
# own container) -- it says nothing about what address spawned student
# containers should use to call BACK to the Hub. Without hub_connect_ip set
# explicitly, JupyterHub falls back to auto-detecting its own hostname,
# which inside a container defaults to that container's own ID (e.g.
# "4e2f59fd7829") -- fine until the hub container is ever rebuilt/recreated
# (a new image, `docker compose up --build`, a Kubernetes pod reschedule,
# etc.), at which point it gets a NEW id, and every student container that
# was already running still has the OLD id baked into its environment from
# when it was spawned. Their notebook then can't reach the Hub at all
# ("Failed to connect to Hub API at 'http://<old-id>:8081/...'") until that
# student's server is fully stopped and re-spawned.
#
# 'jupyterhub-container' is this service's container_name in BOTH
# docker-compose.yml and docker-compose.prod.yml, and Docker Compose
# registers container_name as a resolvable DNS alias on every network that
# container is attached to -- including 'students', the same network every
# DockerSpawner-managed student container joins (see network_name below).
# Pinning hub_connect_ip to that stable name means student containers
# always reach the Hub at the same address, no matter how many times the
# Hub container itself gets rebuilt/recreated behind it.
c.JupyterHub.hub_connect_ip = 'jupyterhub-container'
c.JupyterHub.db_url = "sqlite:///data/jupyterhub.sqlite"
c.JupyterHub.base_url="/jupyterhub"


# Auth
c.Authenticator.allowed_users = {'admin'}
c.Authenticator.admin_users = {'admin'}
c.NativeAuthenticator.open_signup = True

# Spawner
c.Spawner.http_timeout = 300
c.DockerSpawner.mem_limit = '4G'
c.DockerSpawner.network_name = 'students'
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
        'environment': {
            'FLASK_ENV': 'production',
            'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
            'MONGO_INITDB_ROOT_USERNAME': os.environ.get('MONGO_INITDB_ROOT_USERNAME', ''),
            'MONGO_INITDB_ROOT_PASSWORD': os.environ.get('MONGO_INITDB_ROOT_PASSWORD', ''),
        },
    },
    {
        'name': 'cull-idle',
        'command': ['python3', '-m', 'jupyterhub_idle_culler', '--timeout=3600'],
        'admin': True,
    },
    {
        # Periodically refits the AFM student model from logged attempts,
        # so Grey Area probabilities update automatically as students work
        # -- no manual `fit_afm.py` invocation needed. See fit_afm.py for
        # details; tune cadence via AFM_REFIT_INTERVAL_SECONDS below.
        'name': 'afm-refit',
        'command': ['python3', '/srv/jupyterhub/fit_afm.py'],
        'environment': {
            'MONGO_INITDB_ROOT_USERNAME': os.environ.get('MONGO_INITDB_ROOT_USERNAME', ''),
            'MONGO_INITDB_ROOT_PASSWORD': os.environ.get('MONGO_INITDB_ROOT_PASSWORD', ''),
            'AFM_REFIT_INTERVAL_SECONDS': os.environ.get('AFM_REFIT_INTERVAL_SECONDS', '120'),
        },
    },
]