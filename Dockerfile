FROM jupyterhub/jupyterhub:5.4

RUN pip install --no-cache \
    oauthenticator==17.3.0 \
    dockerspawner==14.0.0 \
    jupyterhub-nativeauthenticator \
    flask==3.1.3 \
    pymongo==4.16.0 \
    openai==2.24.0 \
    requests==2.32.5 \
    werkzeug==3.1.6 \
    gunicorn==25.1.0 \
    flask-limiter==4.1.1 \
    jupyterhub-idle-culler==1.4.0 \
    numpy==2.2.6 \
    scikit-learn==1.7.2


COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
COPY logService.py /srv/jupyterhub/logService.py
COPY afm.py /srv/jupyterhub/afm.py
COPY fit_afm.py /srv/jupyterhub/fit_afm.py
COPY solutions.py /srv/jupyterhub/solutions.py
COPY prompts /srv/jupyterhub/prompts