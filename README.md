# JupyterHub LLM Extension

A JupyterHub-based educational platform with AI-powered learning support. When students encounter Python errors in JupyterLab, the system provides progressive LLM-generated hints tailored to the error type and exercise context.

## Architecture

- **JupyterHub** — Multi-user notebook server with GitHub OAuth
- **Flask logService** — REST API handling LLM requests, prompt rendering, and logging
- **MongoDB** — Stores all interaction logs
- **JupyterLab Extensions** — Student-facing UI ([separate repo](https://github.com/sixonenines/JupyterLab-AI-Support-Extensions))

## Production (Kubernetes)

For deploying to **Azure Kubernetes Service** using Terraform and GitHub Actions, see the [Deployment Guide](infra/DEPLOYMENT_GUIDE.md).

## Production (Single Server)

1. Keep ports 80 and 443 open
2. Install Docker and add your user to the `docker` group
3. Clone this repository
4. Copy and fill in environment variables:

   ```bash
   cp .env.template .env
   ```

5. Set up a reverse proxy (e.g., Nginx Proxy Manager) on an external Docker network named `nginx-proxy`, forwarding traffic to `jupyterhub:8000`. Add a custom location for `/jupyterhub/services/askLLM` forwarding to `jupyterhub:8000` with the following advanced config:

   ```
   proxy_set_header X-Forwarded-Proto $scheme;
   ```

6. Run the deploy script:

   ```bash
   sudo bash prod-setup.sh
   ```

7. Check with `docker compose -f docker-compose.prod.yml ps` if all services are running.

## Local Development

1. Copy and fill in environment variables:

   ```bash
   cp .env.template .env
   ```

   Edit `.env` with your OpenAI API key and MongoDB credentials.

2. Build and run the containers:

   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

3. Access [JupyterHub](http://localhost:8533/jupyterhub) and register using the `admin` username, then log in.

## Adding Exercises

1. Create a Jupyter Notebook with your exercise content
2. Set cell metadata (via the Jupyter inspector):
   - All cells: `"deletable": false`
   - Instruction cells (Markdown or code): `"editable": false`
   - Solution cells: `"editable": true`
   - Code cells for students to run: add a unique `"cellIdentifier"` (e.g., `courseName_sheet1_ex1_step1`)
3. Add teacher solutions to `solutions.py` keyed by `cellIdentifier`
4. Place the notebook in `studentContainers/courses/`

To push files to already-running student containers:

```bash
bash studentContainers/addToContainer.sh
```
