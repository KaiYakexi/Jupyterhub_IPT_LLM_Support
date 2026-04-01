# network.tf - Virtual Network and Subnet for AKS
#
# A Virtual Network (VNet) is an isolated network in Azure — like your own
# private LAN in the cloud. A subnet is a range of IPs within that VNet.
#
# AKS nodes and pods will live inside this subnet. With Azure CNI, every pod
# gets a real IP address from the subnet, so the subnet needs to be large
# enough to hold both nodes and all their pods.
#
# The guide uses:
# - VNet:   10.0.0.0/8      (16 million IPs — the whole private range)
# - Subnet: 10.240.0.0/16   (65,536 IPs — plenty for nodes + pods)

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_space       = ["10.0.0.0/8"]

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

resource "azurerm_subnet" "aks" {
  name                 = "snet-aks-${var.project_name}-${var.environment}"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.240.0.0/16"]
}
