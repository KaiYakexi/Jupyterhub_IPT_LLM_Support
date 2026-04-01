# main.tf - Provider configuration and resource group
#
# This is the entry point for Terraform. It tells Terraform:
# 1. Which provider to use (azurerm = Azure Resource Manager)
# 2. What version of the provider to download
# 3. Creates the resource group (a logical container for all your Azure resources)

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0"
}

provider "azurerm" {
  features {}

  # Terraform will use the credentials from `az login`.
  # In CI/CD (Phase 8), we'll use a service principal instead.
}

# Import the existing resource group into Terraform state.
# This block can be removed after the first successful apply.
import {
  to = azurerm_resource_group.main
  id = "/subscriptions/${data.azurerm_subscription.current.subscription_id}/resourceGroups/rg-${var.project_name}-${var.environment}"
}

data "azurerm_subscription" "current" {}

# A resource group is like a folder - everything in your project goes inside it.
# Deleting the resource group deletes everything in it, which is great for cleanup.
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}
