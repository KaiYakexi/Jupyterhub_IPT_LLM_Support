FROM jupyterhub/jupyterhub:5.3.0-17

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