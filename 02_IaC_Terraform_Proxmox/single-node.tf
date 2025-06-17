# Single Node SIEM Deployment Module
# This module creates a single VM with all SIEM components

resource "proxmox_vm_qemu" "siem_single_node" {
  count = var.deployment_mode == "single-node" ? 1 : 0
  
  name        = "siem-single-node"
  target_node = var.proxmox_node
  clone       = var.ubuntu_template_name
  
  # VM Configuration
  cores   = var.single_node_resources.cores
  sockets = 1
  memory  = var.single_node_resources.memory
  
  # Boot configuration
  boot    = "order=scsi0"
  agent   = 1
  onboot  = true
  
  # Network configuration
  network {
    model  = "virtio"
    bridge = var.network_bridge
    tag    = -1
  }
  
  # Disk configuration
  disk {
    storage = var.storage_pool
    type    = "scsi"
    size    = var.single_node_resources.disk
    format  = "qcow2"
    cache   = "writeback"
    backup  = true
  }
  
  # Cloud-init configuration
  os_type   = "cloud-init"
  ipconfig0 = "ip=dhcp"
  
  # SSH configuration
  sshkeys = var.ssh_public_key
  
  # Lifecycle management
  lifecycle {
    ignore_changes = [
      network,
      disk,
    ]
  }
  
  # Tags
  tags = join(",", [
    "siem",
    "single-node",
    var.environment
  ])
  
  # Description
  desc = "SIEM Single Node - All components in one VM"
}

# Output single node information
output "single_node_info" {
  value = var.deployment_mode == "single-node" ? {
    vm_id       = proxmox_vm_qemu.siem_single_node[0].vmid
    name        = proxmox_vm_qemu.siem_single_node[0].name
    target_node = proxmox_vm_qemu.siem_single_node[0].target_node
    cores       = proxmox_vm_qemu.siem_single_node[0].cores
    memory      = proxmox_vm_qemu.siem_single_node[0].memory
    ssh_host    = proxmox_vm_qemu.siem_single_node[0].ssh_host
    ssh_port    = proxmox_vm_qemu.siem_single_node[0].ssh_port
  } : null
}

