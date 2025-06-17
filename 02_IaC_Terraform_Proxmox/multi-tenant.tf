# Multi-Tenant SIEM Deployment Module
# This module creates separate VMs/containers for each SIEM component with tenant isolation

# Wazuh Manager VMs
resource "proxmox_vm_qemu" "wazuh_manager" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  name        = "wazuh-manager-tenant-${count.index + 1}"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  cores   = var.service_resources.wazuh-manager.cores
  sockets = 1
  memory  = var.service_resources.wazuh-manager.memory
  
  boot   = "order=scsi0"
  agent  = 1
  onboot = true
  
  network {
    model  = "virtio"
    bridge = "vmbr${count.index + 10}"
    tag    = 100 + count.index
  }
  
  disk {
    storage = var.ceph_pool
    type    = "scsi"
    size    = var.service_resources.wazuh-manager.disk
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  os_type   = "cloud-init"
  ipconfig0 = "ip=10.${count.index + 100}.1.10/24,gw=10.${count.index + 100}.1.1"
  
  sshkeys = var.ssh_public_key
  
  tags = join(",", [
    "siem",
    "wazuh-manager",
    "tenant-${count.index + 1}",
    var.environment
  ])
  
  desc = "Wazuh Manager for Tenant ${count.index + 1}"
}

# Wazuh Indexer VMs
resource "proxmox_vm_qemu" "wazuh_indexer" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  name        = "wazuh-indexer-tenant-${count.index + 1}"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  cores   = var.service_resources.wazuh-indexer.cores
  sockets = 1
  memory  = var.service_resources.wazuh-indexer.memory
  
  boot   = "order=scsi0"
  agent  = 1
  onboot = true
  
  network {
    model  = "virtio"
    bridge = "vmbr${count.index + 10}"
    tag    = 100 + count.index
  }
  
  disk {
    storage = var.ceph_pool
    type    = "scsi"
    size    = var.service_resources.wazuh-indexer.disk
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  os_type   = "cloud-init"
  ipconfig0 = "ip=10.${count.index + 100}.1.11/24,gw=10.${count.index + 100}.1.1"
  
  sshkeys = var.ssh_public_key
  
  tags = join(",", [
    "siem",
    "wazuh-indexer",
    "tenant-${count.index + 1}",
    var.environment
  ])
  
  desc = "Wazuh Indexer for Tenant ${count.index + 1}"
}

# Graylog VMs
resource "proxmox_vm_qemu" "graylog" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  name        = "graylog-tenant-${count.index + 1}"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  cores   = var.service_resources.graylog.cores
  sockets = 1
  memory  = var.service_resources.graylog.memory
  
  boot   = "order=scsi0"
  agent  = 1
  onboot = true
  
  network {
    model  = "virtio"
    bridge = "vmbr${count.index + 10}"
    tag    = 100 + count.index
  }
  
  disk {
    storage = var.ceph_pool
    type    = "scsi"
    size    = var.service_resources.graylog.disk
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  os_type   = "cloud-init"
  ipconfig0 = "ip=10.${count.index + 100}.1.20/24,gw=10.${count.index + 100}.1.1"
  
  sshkeys = var.ssh_public_key
  
  tags = join(",", [
    "siem",
    "graylog",
    "tenant-${count.index + 1}",
    var.environment
  ])
  
  desc = "Graylog for Tenant ${count.index + 1}"
}

# MongoDB VMs for Graylog
resource "proxmox_vm_qemu" "mongodb" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  name        = "mongodb-tenant-${count.index + 1}"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  cores   = var.service_resources.mongodb.cores
  sockets = 1
  memory  = var.service_resources.mongodb.memory
  
  boot   = "order=scsi0"
  agent  = 1
  onboot = true
  
  network {
    model  = "virtio"
    bridge = "vmbr${count.index + 10}"
    tag    = 100 + count.index
  }
  
  disk {
    storage = var.ceph_pool
    type    = "scsi"
    size    = var.service_resources.mongodb.disk
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  os_type   = "cloud-init"
  ipconfig0 = "ip=10.${count.index + 100}.1.21/24,gw=10.${count.index + 100}.1.1"
  
  sshkeys = var.ssh_public_key
  
  tags = join(",", [
    "siem",
    "mongodb",
    "tenant-${count.index + 1}",
    var.environment
  ])
  
  desc = "MongoDB for Tenant ${count.index + 1}"
}

# TheHive VMs
resource "proxmox_vm_qemu" "thehive" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  name        = "thehive-tenant-${count.index + 1}"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  cores   = var.service_resources.thehive.cores
  sockets = 1
  memory  = var.service_resources.thehive.memory
  
  boot   = "order=scsi0"
  agent  = 1
  onboot = true
  
  network {
    model  = "virtio"
    bridge = "vmbr${count.index + 10}"
    tag    = 100 + count.index
  }
  
  disk {
    storage = var.ceph_pool
    type    = "scsi"
    size    = var.service_resources.thehive.disk
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  os_type   = "cloud-init"
  ipconfig0 = "ip=10.${count.index + 100}.1.30/24,gw=10.${count.index + 100}.1.1"
  
  sshkeys = var.ssh_public_key
  
  tags = join(",", [
    "siem",
    "thehive",
    "tenant-${count.index + 1}",
    var.environment
  ])
  
  desc = "TheHive for Tenant ${count.index + 1}"
}

# Cassandra VMs for TheHive
resource "proxmox_vm_qemu" "cassandra" {
  count = var.deployment_mode == "multi-tenant" ? var.tenant_count : 0
  
  name        = "cassandra-tenant-${count.index + 1}"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  cores   = var.service_resources.cassandra.cores
  sockets = 1
  memory  = var.service_resources.cassandra.memory
  
  boot   = "order=scsi0"
  agent  = 1
  onboot = true
  
  network {
    model  = "virtio"
    bridge = "vmbr${count.index + 10}"
    tag    = 100 + count.index
  }
  
  disk {
    storage = var.ceph_pool
    type    = "scsi"
    size    = var.service_resources.cassandra.disk
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  os_type   = "cloud-init"
  ipconfig0 = "ip=10.${count.index + 100}.1.31/24,gw=10.${count.index + 100}.1.1"
  
  sshkeys = var.ssh_public_key
  
  tags = join(",", [
    "siem",
    "cassandra",
    "tenant-${count.index + 1}",
    var.environment
  ])
  
  desc = "Cassandra for Tenant ${count.index + 1}"
}

# Load Balancer for multi-tenant access
resource "proxmox_vm_qemu" "load_balancer" {
  count = var.deployment_mode == "multi-tenant" ? 1 : 0
  
  name        = "siem-load-balancer"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  cores   = 4
  sockets = 1
  memory  = 8192
  
  boot   = "order=scsi0"
  agent  = 1
  onboot = true
  
  network {
    model  = "virtio"
    bridge = var.network_bridge
    tag    = -1
  }
  
  disk {
    storage = var.ceph_pool
    type    = "scsi"
    size    = "50G"
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  os_type   = "cloud-init"
  ipconfig0 = "ip=dhcp"
  
  sshkeys = var.ssh_public_key
  
  tags = join(",", [
    "siem",
    "load-balancer",
    var.environment
  ])
  
  desc = "Load Balancer for Multi-Tenant SIEM"
}

# Output multi-tenant deployment information
output "multi_tenant_info" {
  value = var.deployment_mode == "multi-tenant" ? {
    tenant_count = var.tenant_count
    wazuh_managers = [
      for i in range(var.tenant_count) : {
        tenant = i + 1
        vm_id  = proxmox_vm_qemu.wazuh_manager[i].vmid
        name   = proxmox_vm_qemu.wazuh_manager[i].name
        ip     = "10.${i + 100}.1.10"
      }
    ]
    wazuh_indexers = [
      for i in range(var.tenant_count) : {
        tenant = i + 1
        vm_id  = proxmox_vm_qemu.wazuh_indexer[i].vmid
        name   = proxmox_vm_qemu.wazuh_indexer[i].name
        ip     = "10.${i + 100}.1.11"
      }
    ]
    graylogs = [
      for i in range(var.tenant_count) : {
        tenant = i + 1
        vm_id  = proxmox_vm_qemu.graylog[i].vmid
        name   = proxmox_vm_qemu.graylog[i].name
        ip     = "10.${i + 100}.1.20"
      }
    ]
    load_balancer = var.deployment_mode == "multi-tenant" ? {
      vm_id = proxmox_vm_qemu.load_balancer[0].vmid
      name  = proxmox_vm_qemu.load_balancer[0].name
    } : null
  } : null
}

