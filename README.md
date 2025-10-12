# Creating the JupyterLab image with AI support functions.

JupyterHub uses DockerSpawner to create a JupyterLab environment for users. To do this. A JupyterLab docker image is required. You can use this [repo](https://github.com/COLAPS-Research/aipromptextensionshttps://github.com/COLAPS-Research/aipromptextensions), which also contains our implemented AI support functions in form of JupyterLab extensions. THe AI support functions only trigger on compile or runtime-errors of cells with a speciic _supportModel_ metatag. These extensions communicate with our logging and llm service that this JupyterHub implementation manages. To create the JupyterLab image, follow these steps:
1. Go into the studentContainers repository
2. Clone the [git repository](https://github.com/COLAPS-Research/aipromptextensionshttps://github.com/COLAPS-Research/aipromptextensions) and move into it. 
3. Replace the value of _setJupyterHubBaseUrl_ with the base url of JupyterHub (e.g. http://localhost:8533/jupyterhub for local deployment)
4. Create the docker image inside the directory of the git repository using:
`docker build -t jupyterlab-students:latest --label "courseName=jupyterlab-students" . --no-cache`



# Adding student exercises

The created JupyterLab images contains a custom script (_start.sh_). If a JupyterLab container spawns, it will run that script and copy files inside that specified directory into the students work environment. If you want to add files to already spawned containers, use the _addToContainer.sh_ script in /studentContainers/courses


# Local Deployment
1. Replace _$JUPYTERHUB_URL_ with "http://host.docker.internal:8000/jupyterhub/hub" in **logService.py**
2. Replace _$OPENAI_API_KEY_ with your OpenAI API Key in **logService.py**
3. Configure MongoDB Credentials
In both **logService.py** and **docker-compose.yml**, replace  _$MONGO_INITDB_ROOT_USERNAME_ and _$MONGO_INITDB_ROOT_PASSWORD_  with your desired MongoDBD credentials
4. Set the Course Directory Path
In both **jupyuterhub_config.py** and **/studentContainers/addToContainer.sh**, replace:
_$ABSOLUTE_PATH_TO_COURSE_DIRECTORY_ with the absolute path to the directory containing the exercises you want to share with students.
5. Build and run the containers
Run the following commands from the project root:
```
docker compose -f docker-compose..yml build --no-cache
docker compose -f docker-compose.yml up -d
```

# Production

1. Keep ports 80 and 433 open
2. Install Docker and add user to 'docker' group
3. git clone this repository
4. mv .env.template .env
5. vi .env and fill it out
6. sudo bash prod-setup.sh (takes a good while)
7. Run docker compose ps, check if nginxproxymanager, db and jupyterhub are running.
If there is an issue, run `docker compose -f docker-compose.prod.yml up -d`and it might fix the issue.
8. Wait a minute or two, then use SSH Tunnel to access nginxproxymanager.
 ```
ssh -L 8493:127.0.0.1:81 username@serverip
 ```
9. Once connected, open your browser and go to http://localhost:8493/login
10. Default login details are: _admin@example.com_ and _changeme_ (you will be asked to change details once logged in)
11. http://localhost:8493/nginx/certificates -> Add Certificate -> Lets Encrypt or Custom
12. http://localhost:8493/nginx/proxy -> Add Proxy Host:

## Details:
```
Domain name: Domain name
Scheme: http
Forward Hostname/IP: jupyterhub
Forward Port: 8000
Websockets Support: Yes
Block Common explots: Yes
```
    
## Custom locations:
```
location: /jupyterhub/services/askLLM
Scheme: http
Forward Hostname/IP: jupyterhub
Forward Port: 8000       
Click on the settings symbol next to location and paste:
proxy_set_header X-Forwarded_Proto $scheme;
```
## SSL:
```
Choose certificate and Force SSL and click on saved once finished.
```

## Jupyterhub Setup
1. go to yourdomain.com/jupyterhub
2. Click on sign up and sign up with the username "admin"
4. After logging in, go to the admin page /jupyterhub/hub/admin -> Manage groups -> New Group and create these four groups: _customPrompt_, _noSupport_,_personalizedSupport_, _genericSupport_. Only assign each user to one of these groups.


## How to prepare the notebooks:
1. Create the Jupyter Notebook first.
2. Design your exercise – Add all your exercise content to the notebook.
3. Set cell permissions (via Cell Metadata in Jupyter inspector):
    * For all cells: "deletable": false
    * For all question description cells (Markdown or code): set "editable": false. 
    * For all solution cells: set "editable": true and give it an unique "identifier" for example: courseName_exerciseSheet_exerciseNumber_stepNumber
4. Add completed Notebook to the system