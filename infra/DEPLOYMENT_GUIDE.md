# Deployment Guide — JupyterHub LLM Extension on Azure AKS

This guide walks through deploying the JupyterHub LLM Extension to Azure Kubernetes Service (AKS) using Terraform for infrastructure and GitHub Actions for CI/CD.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) (`az`)
- [Terraform](https://developer.hashicorp.com/terraform/downloads) (>= 1.0)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm 3](https://helm.sh/docs/intro/install/)
- [Docker](https://docs.docker.com/get-docker/)
- An Azure subscription
- A GitHub account with a [GitHub OAuth App](https://github.com/settings/applications/new)

## Project Structure

```
infra/
├── terraform/                          # Azure infrastructure (IaC)
│   ├── main.tf                         # Provider + resource group
│   ├── variables.tf                    # Input variable declarations
│   ├── aks.tf                          # AKS cluster
│   ├── network.tf                      # VNet + subnet
│   ├── acr.tf                          # Azure Container Registry
│   ├── aks_acr_role.tf                 # RBAC: AKS can pull from ACR
│   ├── outputs.tf                      # Terraform outputs
│   └── terraform.tfvars.template       # Copy → terraform.tfvars (for local runs)
├── docker/
│   ├── Dockerfile.flask                # Flask logService container
│   └── logService.py                   # Flask app (K8s version)
├── k8s/
│   └── flask-logservice/
│       ├── deployment.yaml.template    # envsubst template
│       └── service.yaml.template       # envsubst template
├── helm/
│   ├── config.yaml.template            # JupyterHub Helm values (envsubst template)
│   └── mongodb-values.yaml             # Bitnami MongoDB Helm values

.github/workflows/
└── deploy.yml                          # Full CI/CD pipeline
```

---

## Step 1: Fork the Repository

Fork this repository to your own GitHub account. The CI/CD pipeline runs via GitHub Actions, so you need your own fork to configure secrets and trigger deployments.

---

## Step 2: Azure Setup

Log in to Azure and select your subscription:

```bash
az login
az account list -o table
az account set --subscription "<subscription-id>"
```

### Create a Service Principal for GitHub Actions

GitHub Actions needs credentials to interact with Azure:

```bash
az ad sp create-for-rbac \
  --name "github-actions-jupyterhub" \
  --role contributor \
  --scopes /subscriptions/<subscription-id> \
  --sdk-auth
```

Save the JSON output — you'll add it as a GitHub secret in Step 5.

---

## Step 3: Create a GitHub OAuth App

1. Go to [GitHub Settings → Developer settings → OAuth Apps → New](https://github.com/settings/applications/new)
2. Fill in:
   - **Application name**: JupyterHub (or any name)
   - **Homepage URL**: `https://<your-domain>`
   - **Authorization callback URL**: `https://<your-domain>/hub/oauth_callback`
3. After creating, note the **Client ID** and generate a **Client Secret**

---

## Step 4: Configure Terraform (Optional — for local runs)

If you want to run Terraform locally (instead of via GitHub Actions):

```bash
cd infra/terraform
cp terraform.tfvars.template terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_name   = "my-jupyterhub"        # Globally unique (used for ACR name)
location       = "westeurope"            # Azure region
environment    = "dev"                   # dev, staging, prod
vm_size        = "Standard_B2s_v2"       # AKS node VM size
node_min_count = 1                       # Min autoscale nodes
node_max_count = 3                       # Max autoscale nodes
acr_sku        = "Basic"                 # Basic, Standard, or Premium
```

Then run:

```bash
terraform init
terraform plan
terraform apply
```

---

## Step 5: Configure GitHub Secrets and Variables

Go to your GitHub repo → **Settings → Secrets and variables → Actions**.

### Secrets (sensitive values)

| Secret Name | Value | How to generate |
|---|---|---|
| `AZURE_CREDENTIALS` | Service principal JSON from Step 2 | `az ad sp create-for-rbac --sdk-auth` |
| `OPENAI_API_KEY` | Your OpenAI API key | [OpenAI dashboard](https://platform.openai.com/api-keys) |
| `MONGO_USERNAME` | MongoDB root username | Choose one (e.g., `root`) |
| `MONGO_PASSWORD` | MongoDB root password | `openssl rand -base64 24` |
| `FLASK_SECRET_KEY` | Flask session signing key | `openssl rand -hex 32` |
| `JUPYTERHUB_ASKLLM_API_TOKEN` | Shared Hub ↔ Flask token | `openssl rand -hex 32` |
| `OAUTH_CLIENT_ID` | From Step 3 | GitHub OAuth App page |
| `OAUTH_CLIENT_SECRET` | From Step 3 | GitHub OAuth App page |

### Variables (non-sensitive configuration)

| Variable Name | Example Value | Description |
|---|---|---|
| `DOMAIN` | `example.com` | Your domain name |
| `CONTACT_EMAIL` | `admin@example.com` | LetsEncrypt contact email |
| `OAUTH_ADMIN_USER` | `your-github-username` | JupyterHub admin user |
| `LOAD_BALANCER_IP` | *(empty or static IP)* | Leave empty for Azure-assigned IP |
| `TF_PROJECT_NAME` | `my-jupyterhub` | Base name for Azure resources |
| `TF_LOCATION` | `westeurope` | Azure region |
| `TF_ENVIRONMENT` | `dev` | Environment name |
| `TF_VM_SIZE` | `Standard_B2s_v2` | AKS node VM size |
| `TF_NODE_MIN_COUNT` | `1` | Min autoscale nodes |
| `TF_NODE_MAX_COUNT` | `3` | Max autoscale nodes |
| `TF_ACR_SKU` | `Basic` | ACR pricing tier |
| `K8S_NAMESPACE` | `jupyterhub` | Kubernetes namespace |

---

## Step 6: Run the Pipeline

1. Go to your repo → **Actions** → **Deploy to AKS**
2. Click **Run workflow** → **Run workflow**

The pipeline runs three jobs in sequence:

### Job 1: Provision Azure Infrastructure
- Initializes Terraform and creates `terraform.tfvars` from GitHub Variables
- Runs `terraform plan` and `terraform apply`
- Creates: Resource Group, VNet + Subnet, AKS Cluster, ACR
- Outputs ACR login server and AKS cluster name for subsequent jobs

### Job 2: Build & Push Docker Images
- Logs in to ACR using admin credentials from Terraform
- Builds and pushes two images:
  1. **JupyterHub** — from root `Dockerfile`
  2. **Flask logService** — from `infra/docker/Dockerfile.flask`

> **Note:** The student notebook image is **not** built by this pipeline. You must build and push it separately from the [COLAPS-Research/aipromptextensions](https://github.com/COLAPS-Research/aipromptextensions) repository. See the [Docker Images](#docker-images) section below for instructions.

### Job 3: Deploy to AKS
- Connects to AKS cluster via `az aks get-credentials`
- Creates K8s namespace and secrets
- Deploys MongoDB via Bitnami Helm chart
- Generates `config.yaml` from template via `envsubst` and deploys JupyterHub via Helm
- Generates and applies Flask logService deployment + service
- Verifies all pods are running

---

## Step 7: DNS Setup

After the pipeline completes, get the external IP:

```bash
# Connect to your cluster
az aks get-credentials --resource-group <rg-name> --name <aks-name>

# Get the load balancer IP
kubectl get svc proxy-public -n jupyterhub
```

Create a DNS **A record** pointing your domain to this IP address.

> **Note:** LetsEncrypt needs the domain to resolve before it can issue certificates. HTTPS will start working once DNS propagates (usually within a few minutes, can take up to 48 hours).

---

## Step 8: Verification

Check that everything is running:

```bash
# All pods should be Running
kubectl get pods -n jupyterhub

# Expected pods:
#   hub-...                  (JupyterHub)
#   proxy-...                (configurable-http-proxy)
#   flask-logservice-...     (Flask askLLM service)
#   mongodb-...              (MongoDB)

# Check Flask logService logs
kubectl logs -l app=flask-logservice -n jupyterhub

# Check JupyterHub logs
kubectl logs -l component=hub -n jupyterhub

# Access JupyterHub
# https://<your-domain>
```

Test the Flask logService is connected:

```bash
# Port-forward to test locally
kubectl port-forward svc/flask-logservice 10101:10101 -n jupyterhub

# In another terminal — should return an auth error (expected, means Flask is running)
curl http://localhost:10101/services/askLLM/userSupportGroup
```

---

## Docker Images

### JupyterHub Image
Built from the root `Dockerfile`. Contains JupyterHub, Flask logService code, and all Python dependencies.

```bash
# Manual build (from repo root)
docker build -t <acr>.azurecr.io/jupyterhub:latest .
```

### Flask logService Image
Built from `infra/docker/Dockerfile.flask`. Standalone Flask app with HubAuth for K8s deployment.

```bash
# Manual build (from repo root — needs solutions.py and prompts/)
docker build -f infra/docker/Dockerfile.flask -t <acr>.azurecr.io/flask-logservice:latest .
```

### Student Notebook Image
Built from the [COLAPS-Research/aipromptextensions](https://github.com/COLAPS-Research/aipromptextensions) repository. Contains the JupyterLab extensions that students interact with.

```bash
# Manual build
git clone https://github.com/COLAPS-Research/aipromptextensions.git
docker build -t <acr>.azurecr.io/jupyterlab-students:latest aipromptextensions/
```

---

## Secrets Reference

Two K8s secrets are used:

### `jupyterhub-secrets`
Consumed by the Flask logService deployment (mounted at `/app/secrets/`):

| Key | Used by | Purpose |
|---|---|---|
| `openai-api-key` | Flask | OpenAI API calls |
| `mongo-username` | Flask | MongoDB authentication |
| `mongo-password` | Flask | MongoDB authentication |
| `flask-secret-key` | Flask | Session signing |
| `jupyterhub-askllm-api-token` | Flask + Hub | Shared auth token |

### `mongodb-auth`
Consumed by the Bitnami MongoDB Helm chart:

| Key | Purpose |
|---|---|
| `mongodb-root-password` | MongoDB root password (must match `mongo-password` above) |

To create these manually (if not using GitHub Actions):

```bash
kubectl create secret generic jupyterhub-secrets \
  --namespace=jupyterhub \
  --from-literal=openai-api-key='sk-...' \
  --from-literal=mongo-username='root' \
  --from-literal=mongo-password='<password>' \
  --from-literal=flask-secret-key="$(openssl rand -hex 32)" \
  --from-literal=jupyterhub-askllm-api-token="$(openssl rand -hex 32)"

kubectl create secret generic mongodb-auth \
  --namespace=jupyterhub \
  --from-literal=mongodb-root-password='<same-password-as-above>'
```

---

## Teardown

To remove everything:

```bash
# Remove K8s deployments
kubectl delete -f infra/k8s/flask-logservice/ -n jupyterhub
helm uninstall jupyterhub -n jupyterhub
helm uninstall mongodb -n jupyterhub
kubectl delete namespace jupyterhub

# Destroy Azure infrastructure
cd infra/terraform
terraform destroy
```

> **Warning:** `terraform destroy` deletes all Azure resources including the AKS cluster and ACR. All data in MongoDB PVCs will be lost.

---

## Troubleshooting

### Pods stuck in ImagePullBackOff
AKS can't pull from ACR. Check the AcrPull role assignment:
```bash
az role assignment list --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ContainerRegistry/registries/<acr> -o table
```

### Flask logService CrashLoopBackOff
Check logs for missing secrets or connection issues:
```bash
kubectl logs -l app=flask-logservice -n jupyterhub --previous
```

### LetsEncrypt certificate not issued
- Verify DNS A record resolves: `dig <your-domain>`
- Check proxy logs: `kubectl logs -l component=proxy -n jupyterhub`
- LetsEncrypt has [rate limits](https://letsencrypt.org/docs/rate-limits/) — if you've been testing heavily, you may need to wait

### MongoDB connection refused
Verify MongoDB is running and the service name matches:
```bash
kubectl get svc mongodb -n jupyterhub
kubectl logs -l app.kubernetes.io/name=mongodb -n jupyterhub
```

### Terraform state conflicts
If multiple people run Terraform, consider adding a [remote backend](https://developer.hashicorp.com/terraform/language/backend/azurerm) (Azure Storage Account) to `main.tf`.
