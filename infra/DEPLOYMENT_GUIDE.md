# Deployment Guide — JupyterHub LLM Extension on Azure AKS

Deploy the JupyterHub LLM Extension to Azure Kubernetes Service using Terraform and GitHub Actions.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) (`az`)
- An Azure subscription
- A GitHub account

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
│   └── outputs.tf                      # Terraform outputs
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

Uses OIDC federated credentials — no passwords to manage.

```bash
az login
az account list -o table
az account set --subscription "<subscription-id>"
```

> **Terminology:**
> - `<subscription-id>` — Your Azure subscription ID. Find it in the `SubscriptionId` column of `az account list`.
> - `<appId>` — The unique ID of the app registration you create below. It appears in the output of `az ad app create` as the `appId` field.
> - `<owner>/<repo>` — Your GitHub username and repository name (e.g., `sixonenines/Jupyterhub_LLM_Extension`).

### Create app registration + service principal

```bash
# Creates an app registration in Azure AD — note the appId from the output
az ad app create --display-name "github-jupyterhub"

# Creates a service principal so the app can act on Azure resources
az ad sp create --id "<appId>"

# Grant Contributor role (can create/manage Azure resources)
az role assignment create \
  --assignee "<appId>" \
  --role Contributor \
  --scope /subscriptions/<subscription-id>

# Grant User Access Administrator role (needed for AKS ↔ ACR role binding)
az role assignment create \
  --assignee "<appId>" \
  --role "User Access Administrator" \
  --scope /subscriptions/<subscription-id>
```

### Add federated credential for GitHub Actions

This lets GitHub Actions authenticate to Azure without a password, using OpenID Connect (OIDC):

```bash
az ad app federated-credential create --id "<appId>" --parameters '{
  "name": "github-actions-deploy",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:<owner>/<repo>:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

> **Note:** The `subject` must match your repo and branch exactly. If you trigger from a different branch, update accordingly.

### Values to save for Step 4

| Value | How to get it |
|---|---|
| `AZURE_CLIENT_ID` | The `appId` from the `az ad app create` output |
| `AZURE_TENANT_ID` | `az account show --query tenantId -o tsv` |
| `AZURE_SUBSCRIPTION_ID` | `az account show --query id -o tsv` |

---

## Step 3: Create a GitHub OAuth App

1. Go to [GitHub Settings → Developer settings → OAuth Apps → New](https://github.com/settings/applications/new)
2. Fill in:
   - **Application name**: JupyterHub (or any name)
   - **Homepage URL**: `https://<your-domain>`
   - **Authorization callback URL**: `https://<your-domain>/hub/oauth_callback`
3. Note the **Client ID** and generate a **Client Secret**

---

## Step 4: Configure GitHub Secrets and Variables

Go to your GitHub repo → **Settings → Secrets and variables → Actions**.

### Secrets (sensitive values)

| Secret | Value | How to get it |
|---|---|---|
| `AZURE_CLIENT_ID` | `appId` from Step 2 | App registration output |
| `AZURE_TENANT_ID` | Tenant ID | `az account show --query tenantId -o tsv` |
| `AZURE_SUBSCRIPTION_ID` | Subscription ID | `az account show --query id -o tsv` |
| `OPENAI_API_KEY` | Your OpenAI API key | [OpenAI dashboard](https://platform.openai.com/api-keys) |
| `MONGO_PASSWORD` | MongoDB root password | `openssl rand -base64 24` |
| `OAUTH_CLIENT_ID` | From Step 3 | GitHub OAuth App page |
| `OAUTH_CLIENT_SECRET` | From Step 3 | GitHub OAuth App page |
| `JUPYTERHUB_ASKLLM_API_TOKEN` | Shared Hub ↔ Flask token | `openssl rand -hex 32` |

### Variables (non-sensitive, under the "Variables" tab)

| Variable | Example | Required? |
|---|---|---|
| `DOMAIN` | `example.com` | Yes |
| `CONTACT_EMAIL` | `admin@example.com` | Yes |
| `OAUTH_ADMIN_USER` | `your-github-username` | Yes |
| `TF_PROJECT_NAME` | `my-jupyterhub` | No (default: `jupyterhub-edu`) |
| `TF_LOCATION` | `westeurope` | No (default: `westeurope`) |

> **Note:** `TF_PROJECT_NAME` must be globally unique — it's used for the Azure Container Registry name.

### What's hardcoded (you don't need to set these)

| Setting | Default |
|---|---|
| MongoDB username | `root` |
| Flask secret key | Auto-generated each deploy |
| K8s namespace | `jupyterhub` |
| Environment | `prod` |
| AKS VM size | `Standard_B2s_v2` |
| AKS node count | 1–3 (autoscaling) |
| ACR SKU | `Basic` |

---

## Step 5: Build the Student Notebook Image

JupyterHub requires a student notebook image (`jupyterlab-students`) to be available in your ACR before students can start their servers. Build and push it by following the instructions in the [JupyterLab-AI-Support-Extensions](https://github.com/sixonenines/JupyterLab-AI-Support-Extensions) repository.

---

## Step 6: Run the Pipeline

1. Go to your repo → **Actions** → **Deploy to AKS**
2. Click **Run workflow** → **Run workflow**

The pipeline runs three jobs:

1. **Provision Infrastructure** — Creates Terraform state storage, then creates resource group, VNet, AKS cluster, and ACR
2. **Build & Push Images** — Builds JupyterHub and Flask logService Docker images, pushes to ACR
3. **Deploy to AKS** — Creates K8s secrets, deploys MongoDB + JupyterHub + Flask logService via Helm/kubectl

---

## Step 7: DNS Setup

After the pipeline completes, get the external IP from the workflow output (or run):

```bash
az aks get-credentials --resource-group <rg-name> --name <aks-name>
kubectl get svc proxy-public -n jupyterhub
```

Create a DNS **A record** pointing your domain to this IP.

> LetsEncrypt needs DNS to resolve before issuing certificates. HTTPS will work once DNS propagates.

---

## Step 8: Verification

```bash
# All pods should be Running
kubectl get pods -n jupyterhub

# Expected pods: hub, proxy, autohttps, flask-logservice, mongodb,
#                continuous-image-puller, user-scheduler (x2)

# Check logs if something is wrong
kubectl logs -l app=flask-logservice -n jupyterhub
kubectl logs -l component=hub -n jupyterhub
```

Visit `https://<your-domain>/hub/login` — you should see the GitHub OAuth login page.

---

## Teardown

### Option A: Using Terraform (recommended)

Terraform tracks what it created, so this cleanly removes only the infrastructure resources:

```bash
az login
cd infra/terraform

# Connect to the remote state
terraform init \
  -backend-config="resource_group_name=rg-<project-name>-tfstate" \
  -backend-config="storage_account_name=st<projectnamenohyphens>tfstate" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=terraform.tfstate" \
  -backend-config="use_oidc=false"

# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy
```

Then manually delete the Terraform state storage (Terraform can't delete its own backend):

```bash
az group delete --name rg-<project-name>-tfstate --yes
```

### Option B: Delete resource groups directly

Faster but less precise — deletes everything inside each resource group:

```bash
az login
az group list -o table

# Delete the main resource group (deletes AKS, ACR, VNet, everything inside)
az group delete --name rg-<project-name>-prod --yes

# Delete the Terraform state resource group
az group delete --name rg-<project-name>-tfstate --yes
```

---

## Troubleshooting

### Pods stuck in ImagePullBackOff

AKS can't pull from ACR. Check the AcrPull role assignment:

```bash
az role assignment list --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ContainerRegistry/registries/<acr> -o table
```

### Flask logService CrashLoopBackOff

Check logs:

```bash
kubectl logs -l app=flask-logservice -n jupyterhub --previous
```

### LetsEncrypt certificate not issued

- Verify DNS points to the correct IP: `dig <your-domain>`
- Check autohttps logs: `kubectl logs -l component=autohttps -n jupyterhub -c traefik`
- If DNS was updated after the first deploy, restart the autohttps pod to retry:
  ```bash
  kubectl rollout restart deployment autohttps -n jupyterhub
  ```
- LetsEncrypt has [rate limits](https://letsencrypt.org/docs/rate-limits/)

### MongoDB connection refused

```bash
kubectl get svc mongodb -n jupyterhub
kubectl logs -l app.kubernetes.io/name=mongodb -n jupyterhub
```
