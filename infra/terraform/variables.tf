# variables.tf - Input variables for the project
#
# Variables let you parameterize your Terraform config.
# You set actual values in terraform.tfvars (which is gitignored).
# This file just declares what variables exist and their defaults.

variable "project_name" {
  description = "Base name for all resources (must be globally unique for ACR)"
  type        = string
  default     = "jupyterhub-edu"
}

variable "location" {
  description = "Azure region where resources will be created"
  type        = string
  default     = "westeurope"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vm_size" {
  description = "VM size for AKS default node pool"
  type        = string
  default     = "Standard_B2s_v2"
}

variable "node_min_count" {
  description = "Minimum node count for autoscaling"
  type        = number
  default     = 1
}

variable "node_max_count" {
  description = "Maximum node count for autoscaling"
  type        = number
  default     = 3
}

variable "acr_sku" {
  description = "SKU for Azure Container Registry (Basic, Standard, Premium)"
  type        = string
  default     = "Basic"
}
