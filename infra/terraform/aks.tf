# aks.tf - Azure Kubernetes Service cluster
#
# AKS is a managed Kubernetes service. Azure handles the control plane
# (API server, etcd, scheduler, controller manager) for free.
# You only pay for the worker nodes (VMs) that run your pods.
#
# Key concepts:
# - Node pool: a group of identical VMs that run your workloads
# - System-assigned identity: AKS creates a managed identity automatically,
#   which is used to interact with other Azure resources (like pulling from ACR)
# - Azure CNI: each pod gets a real IP from the VNet subnet, so pods are
#   directly reachable within the network without extra routing

resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "${var.project_name}-${var.environment}"

  # AKS auto-generates a node resource group name that can exceed the 80-char limit.
  # Setting it explicitly avoids that error.
  node_resource_group = "rg-${var.project_name}-${var.environment}-nodes"

  default_node_pool {
    name       = "default"
    node_count = 1                # Start with 1 node to keep costs low
    vm_size    = var.vm_size

    # Place nodes in our dedicated subnet so they use our VNet
    vnet_subnet_id = azurerm_subnet.aks.id

    auto_scaling_enabled = true
    min_count           = var.node_min_count
    max_count           = var.node_max_count
  }

  # System-assigned identity means Azure creates and manages the credentials.
  # No service principal passwords to rotate — Azure handles it.
  identity {
    type = "SystemAssigned"
  }

  # Azure CNI: pods get real IPs from the subnet (unlike kubenet where pods
  # get IPs from a separate overlay). This means:
  # - Pods are directly routable within the VNet
  # - Required when using a custom VNet/subnet
  # - Network policies can be enforced by Azure
  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
    service_cidr   = "10.0.0.0/16"
    dns_service_ip = "10.0.0.10"
  }

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}
