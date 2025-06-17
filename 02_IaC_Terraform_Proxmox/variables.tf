# Variables for Proxmox SIEM Platform Terraform Configuration

# Proxmox connection variables
variable "proxmox_api_url" {
  description = "Proxmox API URL"
  type        = string
  default     = "https://proxmox.local:8006/api2/json"
}

variable "proxmox_user" {
  description = "Proxmox username"
  type        = string
  default     = "root@pam"
}

variable "proxmox_password" {
  description = "Proxmox password"
  type        = string
  sensitive   = true
}

variable "proxmox_tls_insecure" {
  description = "Skip TLS verification"
  type        = bool
  default     = true
}

variable "proxmox_parallel" {
  description = "Number of parallel operations"
  type        = number
  default     = 4
}

variable "proxmox_node" {
  description = "Proxmox node name"
  type        = string
  default     = "pve"
}

# Deployment configuration
variable "deployment_mode" {
  description = "Deployment mode: single-node or multi-tenant"
  type        = string
  default     = "single-node"
  validation {
    condition     = contains(["single-node", "multi-tenant"], var.deployment_mode)
    error_message = "Deployment mode must be either 'single-node' or 'multi-tenant'."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "node_count" {
  description = "Number of Proxmox nodes for multi-tenant deployment"
  type        = number
  default     = 3
}

variable "tenant_count" {
  description = "Number of tenants for multi-tenant deployment"
  type        = number
  default     = 5
}

# Network configuration
variable "network_bridge" {
  description = "Proxmox network bridge"
  type        = string
  default     = "vmbr0"
}

variable "network_cidr" {
  description = "Network CIDR for SIEM platform"
  type        = string
  default     = "10.0.0.0/16"
}

variable "management_subnet" {
  description = "Management subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "tenant_subnet_base" {
  description = "Base subnet for tenant networks"
  type        = string
  default     = "10.0.100.0/22"
}

# Storage configuration
variable "storage_pool" {
  description = "Proxmox storage pool"
  type        = string
  default     = "local-lvm"
}

variable "ceph_pool" {
  description = "Ceph storage pool for distributed deployment"
  type        = string
  default     = "ceph-siem"
}

# Template configuration
variable "ubuntu_template_name" {
  description = "Ubuntu template name"
  type        = string
  default     = "ubuntu-22.04-cloudinit"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
}

variable "timezone" {
  description = "System timezone"
  type        = string
  default     = "UTC"
}

# Resource allocation for single-node deployment
variable "single_node_resources" {
  description = "Resource allocation for single-node deployment"
  type = object({
    cores  = number
    memory = number
    disk   = string
  })
  default = {
    cores  = 16
    memory = 32768
    disk   = "500G"
  }
}

# Resource allocation for individual services
variable "service_resources" {
  description = "Resource allocation per service"
  type = map(object({
    cores  = number
    memory = number
    disk   = string
  }))
  default = {
    wazuh-manager = {
      cores  = 4
      memory = 8192
      disk   = "100G"
    }
    wazuh-indexer = {
      cores  = 8
      memory = 16384
      disk   = "500G"
    }
    graylog = {
      cores  = 4
      memory = 8192
      disk   = "100G"
    }
    mongodb = {
      cores  = 2
      memory = 4096
      disk   = "50G"
    }
    grafana = {
      cores  = 2
      memory = 4096
      disk   = "20G"
    }
    thehive = {
      cores  = 4
      memory = 8192
      disk   = "100G"
    }
    cortex = {
      cores  = 4
      memory = 8192
      disk   = "50G"
    }
    opencti = {
      cores  = 4
      memory = 8192
      disk   = "100G"
    }
    misp = {
      cores  = 4
      memory = 8192
      disk   = "100G"
    }
    velociraptor = {
      cores  = 4
      memory = 8192
      disk   = "200G"
    }
    cassandra = {
      cores  = 8
      memory = 16384
      disk   = "500G"
    }
    praeco = {
      cores  = 2
      memory = 4096
      disk   = "20G"
    }
    shuffle = {
      cores  = 4
      memory = 8192
      disk   = "50G"
    }
  }
}

# High availability configuration
variable "enable_ha" {
  description = "Enable high availability features"
  type        = bool
  default     = false
}

variable "ha_group" {
  description = "HA group configuration"
  type = object({
    group    = string
    priority = number
  })
  default = {
    group    = "siem-ha"
    priority = 100
  }
}

# Backup configuration
variable "backup_schedule" {
  description = "Backup schedule configuration"
  type = object({
    enabled  = bool
    schedule = string
    storage  = string
    keep     = number
  })
  default = {
    enabled  = true
    schedule = "daily"
    storage  = "backup-storage"
    keep     = 7
  }
}

# Security configuration
variable "firewall_enabled" {
  description = "Enable Proxmox firewall"
  type        = bool
  default     = true
}

variable "allowed_networks" {
  description = "Networks allowed to access SIEM platform"
  type        = list(string)
  default     = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
}

# Monitoring configuration
variable "monitoring_enabled" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 90
}

# Integration configuration
variable "external_integrations" {
  description = "External integration endpoints"
  type = map(object({
    enabled  = bool
    endpoint = string
    api_key  = string
  }))
  default = {
    slack = {
      enabled  = false
      endpoint = ""
      api_key  = ""
    }
    teams = {
      enabled  = false
      endpoint = ""
      api_key  = ""
    }
    pagerduty = {
      enabled  = false
      endpoint = ""
      api_key  = ""
    }
  }
  sensitive = true
}

