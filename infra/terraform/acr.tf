# acr.tf - Azure Container Registry
#
# ACR is your private Docker registry in the cloud.
# Instead of building images locally and hoping they exist on every machine,
# you push images to ACR and Kubernetes pulls them from there.
#
# Think of it like Docker Hub, but private and in your Azure account.

resource "azurerm_container_registry" "main" {
  # ACR names must be globally unique and alphanumeric only (no hyphens).
  # We use replace() to strip hyphens from the project name.
  name                = replace("${var.project_name}${var.environment}", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku

  # Admin access lets you log in with username/password.
  # Fine for learning; in production you'd use managed identities instead.
  admin_enabled = true

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}
