FROM jupyterhub/jupyterhub:5.3.0-17

RUN pip install --no-cache \
    oauthenticator==17.2.0 \
    dockerspawner==13.0.0 \
    jupyterhub-nativeauthenticator==1.3.0 \
    flask==3.1.3 \
    pymongo==4.16.0 \
    openai==2.24.0 \
    requests==2.32.5 \
    werkzeug==3.1.6 \
    gunicorn==25.1.0 \
    flask-limiter==4.1.1 \
    nbgitpuller==1.2.2 \
    jupyterhub-idle-culler==1.4.1


COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY logService.py /srv/jupyterhub/logService.py
COPY solutions.py /srv/jupyterhub/solutions.py
COPY prompts /srv/jupyterhub/prompts
