# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JupyterHub-based educational platform with AI-powered learning support. When students encounter Python errors in JupyterLab, the system provides progressive LLM-generated hints tailored to the error type and exercise context. Students receive escalating support (generic hints → personalized explanations → worked examples → teacher solutions) before seeing the final answer.

The JupyterLab extensions that students interact with live in a separate repo: https://github.com/COLAPS-Research/aipromptextensions

## Build & Deploy Commands

### Local Development
```bash
# Build and start (from project root)
docker compose -f docker-compose.yml build --no-cache
docker compose -f docker-compose.yml up -d

# Access at http://localhost:8533/jupyterhub
# Register with username "admin", then log in
```

### Production
```bash
# Copy and fill environment variables
cp .env.template .env
# Edit .env with credentials

# Deploy
sudo bash prod-setup.sh

# If services fail to start
docker compose -f docker-compose.prod.yml up -d
```

### Pushing files to running student containers
```bash
bash studentContainers/addToContainer.sh
```

## Architecture

### Services (all in one Docker container)

- **JupyterHub** (port 8000, exposed as 8533 locally): Multi-user notebook server using DockerSpawner + NativeAuthenticator. Config in `jupyterhub_config.py`.
- **Flask/Gunicorn service** (`logService.py`, port 10101): REST API registered as JupyterHub service `askLLM`. Handles LLM requests, prompt rendering, and MongoDB logging.
- **MongoDB** (`db` container, port 27017): Stores all interaction logs in `loggedData.loggedData_data`.

### Request Flow

1. Student runs code in a JupyterLab cell tagged with `cellIdentifier` metadata
2. JupyterLab extension detects error and POSTs to `/jupyterhub/services/askLLM/errorLog`
3. `logService.py` selects a prompt template based on `supportType` and `hintCounter`
4. Template variables (`$sourceCode`, `$traceback`, `$taskDescription`) are substituted
5. Prompt is sent to OpenAI API (`gpt-4.1`), response logged to MongoDB and returned

### Support Types & Prompt System

Five support types defined in `promptHandlers` dict in `logService.py`:
- `noSupport` — no LLM call
- `genericSupport` — simple error-name-based prompt
- `personalizedSupport` — includes traceback + source code
- `customPrompt` — user-provided prompt
- `instructionalText` — progressive templates from `prompts/instructionalHint{0,1,2}Template.md`
- `workedExample` — progressive templates from `prompts/workedExampleHint{0,1,2}Template.md`

After `maxHints=3` attempts, the teacher solution from `solutions.py` is returned. Templates use Python `string.Template` with `$sourceCode`, `$traceback`, `$taskDescription` substitution variables.

### Key Files

| File | Role |
|---|---|
| `logService.py` | Flask app: API endpoints, prompt logic, LLM calls, auth |
| `solutions.py` | Dict mapping `cellIdentifier` → teacher solution code |
| `jupyterhub_config.py` | Hub config: spawner, auth, service registration |
| `prompts/*.md` | LLM prompt templates (progressive hints) |
| `prompts/*.json` | Prompt metadata/descriptions |
| `Dockerfile` | JupyterHub image with all Python deps |
| `docker-compose.yml` | Local dev stack (hub + MongoDB) |
| `docker-compose.prod.yml` | Production stack (adds nginx proxy manager) |
| `prod-setup.sh` | Injects `.env` vars into config files via sed, builds & starts prod |

### Environment Variables (via `.env`)

Placeholders `$VAR_NAME` in `logService.py` and `docker-compose.yml` are replaced by `prod-setup.sh` at deploy time:
- `JUPYTERHUB_URL`, `OPENAI_API_KEY`, `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`

For local dev, replace these placeholders directly in the files (see README.md).

### Flask API Endpoints (all under `/jupyterhub/services/askLLM/`)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `errorLog` | POST | Token | Error logging + LLM hint generation |
| `errorLogBeforePrompt` | POST | Token | Pre-prompt error state capture |
| `successLog` | POST | Token | Success event logging |
| `userSupportGroup` | GET | Token | Get user's assigned support group |
| `testDB` | GET | OAuth | Dump all logged data (debug) |
| `oauth_callback` | GET | — | OAuth flow callback |

### Student Support Group Assignment

Users are assigned to support groups via JupyterHub groups. The `userSupportGroup` endpoint checks group membership to determine which prompt strategy to use. Groups are managed through JupyterHub admin.

### Adding Exercises

1. Create Jupyter notebook with cells tagged with unique `cellIdentifier` in metadata (pattern: `courseName_exerciseSheet_exerciseNumber_stepNumber`)
2. Set cell metadata: `"deletable": false` for all cells; `"editable": false` for instructions, `true` for solution cells
3. Add teacher solutions to `solutions.py` keyed by `cellIdentifier`
4. Place notebook in `studentContainers/courses/`
