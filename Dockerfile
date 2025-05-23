FROM jupyterhub/jupyterhub:latest

RUN pip install --no-cache \
    oauthenticator \
    dockerspawner \
    jupyterhub-nativeauthenticator \
    flask \
    pymongo \
    openai \
    requests \
    werkzeug \
    gunicorn \
    nbgitpuller \
    jupyterhub-idle-culler

    
COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py