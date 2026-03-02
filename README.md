# Creating the JupyterLab image with AI support functions

JupyterHub uses DockerSpawner to create a JupyterLab environment for users. To do this, a JupyterLab docker image is required. You can use this [repo](https://github.com/COLAPS-Research/aipromptextensions), which also contains our implemented AI support functions in the form of JupyterLab extensions. The AI support functions only trigger on compile or runtime errors of cells with a specific _supportModel_ metatag. These extensions communicate with our logging and LLM service that this JupyterHub implementation manages. To create the JupyterLab image, follow these steps:
1. Go into the studentContainers directory
2. Clone the [git repository](https://github.com/COLAPS-Research/aipromptextensions) and move into it
3. Replace the value of _setJupyterHubBaseUrl_ with the base URL of JupyterHub (e.g. `http://localhost:8533/jupyterhub` for local deployment) in `extensionManager/src/index.ts`
4. Create the docker image inside the directory of the git repository using:
```
docker build -t jupyterlab-students:latest --label "courseName=jupyterlab-students" . --no-cache
```


# Adding student exercises

The created JupyterLab image contains a custom script (_start.sh_). When a JupyterLab container spawns, it runs that script and copies files from the specified directory into the student's work environment. If you want to add files to already spawned containers, use the _addToContainer.sh_ script in `/studentContainers/courses`.


# Local Deployment
1. Copy and fill in environment variables:
```
cp .env.template .env
```
Edit `.env` with your OpenAI API key and MongoDB credentials.

2. Build and run the containers:
```
docker compose build --no-cache
docker compose up -d
```
3. Access [JupyterHub](http://localhost:8533/jupyterhub) and register using the _admin_ username, then log in using the same username.

# Production

1. Keep ports 80 and 443 open
2. Install Docker and add your user to the `docker` group
3. Clone this repository
4. Copy and fill in environment variables:
```
cp .env.template .env
```
5. Set up a reverse proxy (e.g. Nginx Proxy Manager) on an external Docker network named `nginx-proxy`, forwarding traffic to `jupyterhub:8000` with WebSocket support enabled. Add a custom location for `/jupyterhub/services/askLLM` forwarding to `jupyterhub:8000` with the following advanced config:
```
proxy_set_header X-Forwarded-Proto $scheme;
```
6. Run the deploy script:
```
sudo bash prod-setup.sh
```
7. Run `docker compose -f docker-compose.prod.yml ps` and check that `db` and `jupyterhub` are running.
If there is an issue, run `docker compose -f docker-compose.prod.yml up -d`.

## How to prepare the notebooks
1. Create the Jupyter Notebook first
2. Design your exercise — add all your exercise content to the notebook
3. Set cell permissions (via Cell Metadata in Jupyter inspector):
    * For all cells: `"deletable": false`
    * For all question description cells (Markdown or code): set `"editable": false`
    * For all solution cells: set `"editable": true`
    * For every code cell that is meant to be executed by a user: give it a unique `"cellIdentifier"`, for example `courseName_exerciseSheet_exerciseNumber_stepNumber`