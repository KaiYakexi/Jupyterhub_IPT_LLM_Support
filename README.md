1. Keep ports 80 and 433 open
2. Install Docker and add user to 'docker' group
3. git clone this repository
4. git switch tudortmund
5. mv .env.template .env
6. vi .env and fill it out
7. bash setup.sh (takes a good while)
8. Run docker compose ps, check if nginxproxymanager, db and jupyterhub are running.
Sometimes db exits, just run docker compose up -d and it should work all fine.
9. Wait a minute or two, then use SSH Tunnel to access nginxproxymanager.
 ```
ssh -L 8493:127.0.0.1:81 username@serverip
 ```
10. Once connected, open your browser and go to http://localhost:8493/login
11. Default login details are: 'admin@example.com' and 'changeme' (you will be asked to change details once logged in)
12. http://localhost:8493/nginx/certificates -> Add Certificate -> Lets Encrypt or Custom (I just used letsencrypt)
13. http://localhost:8493/nginx/proxy -> Add Proxy Host:

# Details:
```
Domain name: Domain name
Scheme: http
Forward Hostname/IP: jupyterhub
Forward Port: 8000
Websockets Support: Yes
```
    
# Custom locations:
```
location: /jupyterhub/services/askLLM
Scheme: http
Forward Hostname/IP: jupyterhub
Forward Port: 8000       
Click on the settings symbol next to location and paste:
proxy_set_header X-Forwarded_Proto $scheme;
```
# SSL:
Choose certificate and Force SSL and click on saved once finished.
14. go to domain.com/jupyterhub
15. Click on sign up and sign up with the admin username specified in the .env
16. After logging in, you will see, that your jupyterlab server is not starting, you will need to go to the admin page /jupyterhub/hub/admin -> Manage groups -> New Group -> coursename specified in .env as group name -> add users to the group -> apply.
17. Do the same for the groups "customPrompt", "noSupport","personalizedSupport", "genericSupport". But only assign your user to one of these groups.

# How to share course materials
To share course materials, host your materials on a public github server and create a link using nbgitpuller https://nbgitpuller.readthedocs.io/en/latest/link.html.
* Jupyterhub URL: https://example.com/jupyterhub
* Git repository URL: https://github.com/sixonenines/course
* Branch: main
* Application to Open: JupyterLab

# How to prepare notebooks:
https://github.com/KaiYakexi/jupy-cell-lock