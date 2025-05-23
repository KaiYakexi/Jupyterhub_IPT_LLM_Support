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


c.JupyterHub.template_vars = {'announcement_login': """Information for participants and consent form:
Thank you for considering participating in this research study. This information sheet outlines the purpose of the study and provides a description of your involvement and rights as a participant, if you agree to take part.

In this study, we aim to explore which large language model support functions are suited best for learning python programming. You will be able to use a self-hosted online learning platform to study materials and practice python programming. If you run into an error while programming, the error contents will be logged in our database and an AI supported function is going to try and help you solve it. To that end, we use the OpenAI API for submitting Python error messages and user-generated prompts to Open AI’s LLM. No personal or sensitive data are shared. 

Participation in the study is voluntary, and you can withdraw from the study at any point. We will use the collected information for research purposes, and academic publications. Your data is anonymous, and we do not collect any personal information that can be used to identify you. The records from this study will be kept confidential. Only the researchers involved in this research will have access to the data generated from this study. Anonymized, processed data may be shared via a data archive for research purposes.

If you have any questions regarding this study please contact the Principal Investigator, Irene-Angelica Chounta at irene-angelica.chounta@uni-due.de

By proceeding to the next step, you provide consent for the following:

	•	I have read and understood the study information, or it has been read to me. I have no questions about the study
	•	I have read and understood the above information and I wish to participate in the research.
	•	I consent voluntarily to be a participant in this study,  Iunderstand that I can refuse to answer questions and that I can withdraw from the study throughout its duration without having to give a reason.
	•	I understand that the information I provide will be used for research purposes and academic publications
	•	I understand that no personal information that can be used to identify me is collected at any point of this research.
	•	I give permission for the anonymised information I provide to be deposited in a data archive so that it may be used for future research.
"""}

def pre_spawn_hook(spawner):
    group_names = [group.name for group in spawner.user.groups]
    if '$COURSE_NAME' in group_names:
        spawner.volumes={ 'jupyterhub-user-{username}': '/home/jovyan/work',
                        '$ABSOLUTE_PATH_TO_COURSE_DIRECTORY':'/tmp/source'}
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
    },
        {
        "name": "jupyterhub-idle-culler-role",
        "scopes": [
            "list:users",
            "read:users:activity",
            "read:servers",
            "delete:servers",
            # "admin:users", # if using --cull-users
        ],
        # assignment of role's permissions to:
        "services": ["jupyterhub-idle-culler-service"],
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