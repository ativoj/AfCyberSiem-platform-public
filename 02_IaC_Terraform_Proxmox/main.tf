# Terraform Configuration for Proxmox SIEM Platform
# Main configuration file for deploying SIEM infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    proxmox = {
      source  = "telmate/proxmox"
      version = "~> 2.9"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# Provider configuration
provider "proxmox" {
  pm_api_url      = var.proxmox_api_url
  pm_user         = var.proxmox_user
  pm_password     = var.proxmox_password
  pm_tls_insecure = var.proxmox_tls_insecure
  pm_parallel     = var.proxmox_parallel
}

# Data sources
data "proxmox_template" "ubuntu_template" {
  most_recent = true
  name        = var.ubuntu_template_name
  node        = var.proxmox_node
}

# Local values for common configurations
locals {
  common_tags = {
    Environment = var.environment
    Project     = "siem-platform"
    ManagedBy   = "terraform"
  }
  
  # Network configuration
  network_config = {
    bridge    = var.network_bridge
    firewall  = true
    link_down = false
  }
  
  # Storage configuration
  storage_config = {
    storage = var.storage_pool
    size    = "20G"
    type    = "scsi"
    format  = "qcow2"
  }
}

# Random password generation for services
resource "random_password" "service_passwords" {
  for_each = toset([
    "wazuh_admin",
    "graylog_admin", 
    "grafana_admin",
    "thehive_admin",
    "opencti_admin",
    "misp_admin",
    "cassandra_admin"
  ])
  
  length  = 16
  special = true
}

# Cloud-init configuration template
data "template_file" "cloud_init" {
  template = file("${path.module}/templates/cloud-init.yml")
  vars = {
    ssh_public_key = var.ssh_public_key
    timezone       = var.timezone
  }
}

# Create cloud-init drive
resource "proxmox_cloud_init_disk" "siem_cloud_init" {
  count = var.deployment_mode == "single-node" ? 1 : var.node_count
  
  name     = "siem-cloud-init-${count.index + 1}"
  pve_node = var.proxmox_node
  storage  = var.storage_pool
  
  meta_data = yamlencode({
    instance_id    = "siem-${count.index + 1}"
    local-hostname = "siem-node-${count.index + 1}"
  })
  
  user_data = data.template_file.cloud_init.rendered
}

# Network configuration for multi-tenant setup
resource "proxmox_virtual_environment_network_linux_bridge" "tenant_bridges" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  node_name = var.proxmox_node
  name      = "vmbr${count.index + 10}"
  comment   = "Tenant ${count.index + 1} isolated bridge"
  
  ports = []
  vlan_aware = true
}

# SDN Zone configuration for multi-tenancy
resource "proxmox_virtual_environment_network_linux_vlan" "tenant_vlans" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  node_name = var.proxmox_node
  name      = "tenant-${count.index + 1}-vlan"
  interface = "vmbr${count.index + 10}"
  vlan      = 100 + count.index
  comment   = "Tenant ${count.index + 1} VLAN"
}

# Output important information
output "deployment_info" {
  value = {
    deployment_mode = var.deployment_mode
    node_count      = var.deployment_mode == "single-node" ? 1 : var.node_count
    tenant_count    = var.deployment_mode == "multi-tenant" ? var.tenant_count : 1
    proxmox_node    = var.proxmox_node
    storage_pool    = var.storage_pool
  }
}

output "service_passwords" {
  value = {
    for service, password in random_password.service_passwords : service => password.result
  }
  sensitive = true
}

output "cloud_init_ids" {
  value = proxmox_cloud_init_disk.siem_cloud_init[*].id
}

