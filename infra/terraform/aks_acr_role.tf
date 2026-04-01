# aks_acr_role.tf - Grant AKS permissions for ACR and networking
#
# Without the ACR role, pods would fail with "ImagePullBackOff" errors because
# the K8s nodes wouldn't have credentials to access your private registry.
#
# Without the network role, AKS wouldn't be able to attach pods to the subnet
# when using Azure CNI.

resource "azurerm_role_assignment" "aks_acr_pull" {
  # The principal is the kubelet identity — the identity that runs on each node
  # and is responsible for pulling container images.
  principal_id = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id

  # AcrPull is a built-in Azure role that grants read-only access to a container registry.
  role_definition_name = "AcrPull"

  # Scope it to just this ACR, not the entire resource group.
  scope = azurerm_container_registry.main.id
}

# Grant AKS the ability to manage networking on the subnet.
# With Azure CNI, AKS needs to assign IPs from the subnet to pods.
resource "azurerm_role_assignment" "aks_network_contributor" {
  principal_id         = azurerm_kubernetes_cluster.main.identity[0].principal_id
  role_definition_name = "Network Contributor"
  scope                = azurerm_subnet.aks.id
}
