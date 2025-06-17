# SIEM Platform PowerShell Deployment Package
# Installation and Setup Guide

## Overview

This PowerShell deployment package provides automated deployment of the World's Best Open-Source SIEM Platform on Proxmox infrastructure. It supports both single-node and multi-tenant SaaS deployments with complete automation using Terraform and Ansible.

## Prerequisites

### Software Requirements
- **PowerShell 5.0 or higher** (Windows PowerShell or PowerShell Core)
- **Terraform 1.0+** - Infrastructure as Code tool
- **Ansible 2.9+** - Configuration management tool
- **Git** - For cloning repositories and version control
- **SSH Client** - For secure access to deployed VMs

### PowerShell Modules
The deployment script will automatically install required modules:
- **Posh-SSH** - SSH client for PowerShell
- **PowerCLI** - VMware vSphere PowerShell module (optional)

### Infrastructure Requirements
- **Proxmox VE 7.0+** cluster with API access
- **Minimum 3 nodes** for multi-tenant deployment
- **Ceph storage cluster** (recommended for multi-tenant)
- **Network connectivity** between deployment machine and Proxmox
- **SSH key pair** for VM authentication

### Resource Requirements

#### Single-Node Deployment
- **CPU**: 32+ vCPUs
- **Memory**: 64+ GB RAM
- **Storage**: 1+ TB
- **Network**: 1 Gbps

#### Multi-Tenant Deployment (per tenant)
- **CPU**: 30+ vCPUs per tenant
- **Memory**: 48+ GB RAM per tenant
- **Storage**: 800+ GB per tenant
- **Network**: 10 Gbps (recommended)

## Installation Steps

### 1. Download and Extract Package

```powershell
# Download the SIEM platform package
git clone https://github.com/siem-platform/powershell-deployment.git
cd powershell-deployment
```

### 2. Configure Deployment

#### Single-Node Configuration
Edit `single-node\config\single-node-config.json`:

```json
{
  "proxmox": {
    "api_url": "https://your-proxmox.local:8006/api2/json",
    "username": "root@pam",
    "password": "your-proxmox-password",
    "node": "pve",
    "storage_pool": "local-lvm",
    "network_bridge": "vmbr0"
  },
  "deployment": {
    "environment": "production",
    "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2E... your-public-key",
    "ssh_private_key": "~/.ssh/siem_platform_key"
  },
  "resources": {
    "cores": 32,
    "memory": 65536,
    "disk": "1T"
  }
}
```

#### Multi-Tenant Configuration
Edit `multi-tenant\config\multi-tenant-config.json`:

```json
{
  "proxmox": {
    "api_url": "https://your-proxmox-cluster.local:8006/api2/json",
    "username": "root@pam",
    "password": "your-proxmox-password",
    "ceph_pool": "ceph-siem"
  },
  "cluster": {
    "node_count": 3,
    "nodes": ["pve-node1", "pve-node2", "pve-node3"]
  },
  "features": {
    "enable_ha": true,
    "enable_backup": true,
    "enable_monitoring": true
  }
}
```

### 3. Generate SSH Key Pair

```powershell
# Generate SSH key pair for VM access
ssh-keygen -t rsa -b 4096 -f ~/.ssh/siem_platform_key -N ""

# Copy public key content to configuration file
Get-Content ~/.ssh/siem_platform_key.pub
```

### 4. Test Proxmox Connectivity

```powershell
# Test Proxmox API connectivity
$apiUrl = "https://your-proxmox.local:8006/api2/json"
$creds = @{
    username = "root@pam"
    password = "your-password"
}

try {
    $response = Invoke-RestMethod -Uri "$apiUrl/access/ticket" -Method POST -Body ($creds | ConvertTo-Json) -ContentType "application/json" -SkipCertificateCheck
    Write-Host "Proxmox connection successful" -ForegroundColor Green
} catch {
    Write-Host "Proxmox connection failed: $($_.Exception.Message)" -ForegroundColor Red
}
```

## Deployment Commands

### Single-Node Deployment

```powershell
# Basic single-node deployment
.\Deploy-SIEM.ps1 -DeploymentMode single-node

# Preview deployment without executing
.\Deploy-SIEM.ps1 -DeploymentMode single-node -WhatIf

# Destroy existing and redeploy
.\Deploy-SIEM.ps1 -DeploymentMode single-node -DestroyExisting

# Skip prerequisite checks
.\Deploy-SIEM.ps1 -DeploymentMode single-node -SkipPrerequisites
```

### Multi-Tenant Deployment

```powershell
# Deploy with 5 tenants (default)
.\Deploy-SIEM.ps1 -DeploymentMode multi-tenant

# Deploy with 10 tenants
.\Deploy-SIEM.ps1 -DeploymentMode multi-tenant -TenantCount 10

# Preview multi-tenant deployment
.\Deploy-SIEM.ps1 -DeploymentMode multi-tenant -TenantCount 3 -WhatIf

# Custom configuration file
.\Deploy-SIEM.ps1 -DeploymentMode multi-tenant -ConfigFile "custom-config.json"
```

### Advanced Options

```powershell
# Get help and usage information
.\Deploy-SIEM.ps1 -Help

# Deploy with custom configuration
.\Deploy-SIEM.ps1 -DeploymentMode single-node -ConfigFile "my-config.json"

# Skip prerequisites and destroy existing
.\Deploy-SIEM.ps1 -DeploymentMode multi-tenant -SkipPrerequisites -DestroyExisting
```

## Deployment Process

### Phase 1: Prerequisites Check
- Validates PowerShell version
- Checks for required tools (Terraform, Ansible)
- Installs PowerShell modules
- Tests Proxmox connectivity

### Phase 2: Infrastructure Deployment
- Executes Terraform scripts
- Creates VMs/containers on Proxmox
- Configures networking and storage
- Sets up tenant isolation (multi-tenant)

### Phase 3: Service Configuration
- Runs Ansible playbooks
- Installs and configures SIEM components
- Sets up monitoring and alerting
- Configures backup schedules

### Phase 4: Validation and Access
- Validates service health
- Generates access credentials
- Creates management scripts
- Provides connection information

## Post-Deployment

### Access Information
After successful deployment, access information is saved to:
- `single-node-access-info.txt` (single-node)
- `multi-tenant-access-info.txt` (multi-tenant)

### Service URLs
- **Wazuh Dashboard**: https://your-ip/
- **Graylog**: http://your-ip:9000
- **Grafana**: http://your-ip:3000
- **TheHive**: http://your-ip:9000

### Default Credentials
Default passwords are generated and saved in the access information files. **Change these immediately after first login.**

### Management Scripts
The deployment creates management scripts on each VM:
- `/opt/siem-status.sh` - Check platform status
- `/opt/siem-backup.sh` - Manual backup execution
- `/opt/check-services.sh` - Service health monitoring

## Troubleshooting

### Common Issues

#### Terraform Errors
```powershell
# Check Terraform version
terraform --version

# Validate configuration
terraform validate

# Debug with verbose output
terraform apply -auto-approve -var-file="terraform.tfvars" -debug
```

#### Ansible Errors
```powershell
# Test connectivity to VMs
ansible all -i inventory/hosts -m ping

# Run playbook with verbose output
ansible-playbook -i inventory/hosts playbooks/site.yml -vvv

# Check specific service
ansible-playbook -i inventory/hosts playbooks/wazuh-manager.yml --tags="health-check"
```

#### Network Connectivity
```powershell
# Test VM SSH access
Test-NetConnection -ComputerName "vm-ip" -Port 22

# Test service ports
Test-NetConnection -ComputerName "vm-ip" -Port 9200  # Wazuh Indexer
Test-NetConnection -ComputerName "vm-ip" -Port 9000  # Graylog
```

### Log Files
Deployment logs are saved to:
- `logs\siem-deployment-YYYYMMDD_HHMMSS.log`

Service logs on VMs:
- Wazuh: `/var/ossec/logs/`
- Graylog: `/var/log/graylog-server/`
- Grafana: `/var/log/grafana/`

### Recovery Procedures

#### Restart Services
```bash
# On deployed VMs
sudo systemctl restart wazuh-manager
sudo systemctl restart wazuh-indexer
sudo systemctl restart graylog-server
sudo systemctl restart grafana-server
```

#### Rebuild Single Component
```powershell
# Redeploy specific component
ansible-playbook -i inventory/hosts playbooks/wazuh-manager.yml --limit="wazuh-manager-host"
```

#### Complete Rebuild
```powershell
# Destroy and redeploy
.\Deploy-SIEM.ps1 -DeploymentMode single-node -DestroyExisting
```

## Maintenance

### Regular Tasks
1. **Monitor resource usage** - Check CPU, memory, and disk usage
2. **Update components** - Apply security updates regularly
3. **Backup verification** - Test backup and restore procedures
4. **Log rotation** - Ensure log files don't fill disk space
5. **Certificate renewal** - Update SSL certificates before expiration

### Scaling Operations
```powershell
# Add more tenants (multi-tenant deployment)
.\Deploy-SIEM.ps1 -DeploymentMode multi-tenant -TenantCount 15

# Upgrade resources (modify config and redeploy)
# Edit configuration file, then:
.\Deploy-SIEM.ps1 -DeploymentMode single-node -DestroyExisting
```

### Backup and Restore
```bash
# Manual backup execution
sudo /opt/siem-backup.sh

# Restore from backup
sudo /opt/siem-restore.sh /backup/path/backup-file.tar.gz
```

## Support and Documentation

### Resources
- **GitHub Repository**: https://github.com/siem-platform/powershell-deployment
- **Documentation**: https://docs.siem-platform.org
- **Community Forum**: https://community.siem-platform.org
- **Issue Tracker**: https://github.com/siem-platform/issues

### Getting Help
1. Check the troubleshooting section above
2. Review log files for error messages
3. Search existing issues on GitHub
4. Create a new issue with:
   - Deployment mode and configuration
   - Error messages and log excerpts
   - Environment details (Proxmox version, etc.)

### Contributing
Contributions are welcome! Please see the contributing guidelines in the repository.

---

**Note**: This deployment package is designed for production use but should be thoroughly tested in a development environment first. Always follow security best practices and change default passwords immediately after deployment.

