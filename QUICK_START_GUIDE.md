# SIEM Platform - Quick Start Deployment Guide

## Overview

This quick start guide provides step-by-step instructions for deploying the SIEM Platform in both single-node and multi-tenant configurations. Follow these instructions to get your SIEM platform operational quickly.

## Prerequisites

### Hardware Requirements

**Single-Node Deployment:**
- CPU: 32 vCPUs (minimum 16 vCPUs)
- RAM: 64 GB (minimum 32 GB)
- Storage: 1 TB SSD (minimum 500 GB)
- Network: 1 Gbps connection

**Multi-Tenant Deployment:**
- CPU: 128 vCPUs across cluster (minimum 64 vCPUs)
- RAM: 256 GB across cluster (minimum 128 GB)
- Storage: 10 TB distributed storage (minimum 2 TB)
- Network: 10 Gbps connection with redundancy

### Software Prerequisites

- Proxmox VE 8.0 or later
- PowerShell 7.0 or later (for Windows deployment)
- Terraform 1.5 or later
- Ansible 2.15 or later
- Git for repository access

## Single-Node Deployment

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/siem-platform.git
cd siem-platform
```

### Step 2: Configure Variables

Edit `terraform/terraform.tfvars`:

```hcl
# Proxmox Configuration
proxmox_api_url = "https://your-proxmox:8006/api2/json"
proxmox_api_token_id = "your-token-id"
proxmox_api_token_secret = "your-token-secret"

# Single Node Configuration
deployment_type = "single-node"
node_name = "proxmox-node1"
vm_template = "ubuntu-22.04-template"

# Network Configuration
network_bridge = "vmbr0"
network_vlan = 100
ip_range = "192.168.100.0/24"
gateway = "192.168.100.1"
dns_servers = ["8.8.8.8", "8.8.4.4"]

# Resource Allocation
vm_cpu_cores = 32
vm_memory = 65536
vm_disk_size = "1000G"
```

### Step 3: Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### Step 4: Configure Services

```bash
cd ../ansible
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

### Step 5: PowerShell Deployment (Alternative)

For Windows environments:

```powershell
# Navigate to PowerShell deployment directory
cd powershell

# Configure deployment
$config = Get-Content "single-node/config/single-node-config.json" | ConvertFrom-Json
$config.proxmox.api_url = "https://your-proxmox:8006/api2/json"
$config.proxmox.username = "your-username"
$config.proxmox.password = "your-password"
$config | ConvertTo-Json -Depth 10 | Set-Content "single-node/config/single-node-config.json"

# Deploy platform
.\Deploy-SIEM.ps1 -DeploymentType "single-node" -ConfigFile "single-node/config/single-node-config.json"
```

## Multi-Tenant Deployment

### Step 1: Prepare Cluster

Ensure Proxmox cluster is configured with:
- Shared storage (Ceph or NFS)
- Cluster networking
- High availability configuration

### Step 2: Configure Multi-Tenant Variables

Edit `terraform/terraform.tfvars`:

```hcl
# Proxmox Configuration
proxmox_api_url = "https://your-proxmox-cluster:8006/api2/json"
proxmox_api_token_id = "your-token-id"
proxmox_api_token_secret = "your-token-secret"

# Multi-Tenant Configuration
deployment_type = "multi-tenant"
cluster_nodes = ["proxmox-node1", "proxmox-node2", "proxmox-node3"]
vm_template = "ubuntu-22.04-template"

# Network Configuration
management_network = "vmbr0"
tenant_network_base = "vmbr1"
storage_network = "vmbr2"

# Control Plane Configuration
control_plane_cpu = 16
control_plane_memory = 32768
control_plane_disk = "500G"

# Tenant Configuration
default_tenant_cpu = 8
default_tenant_memory = 16384
default_tenant_disk = "200G"
max_tenants = 100

# Storage Configuration
shared_storage = "ceph-storage"
backup_storage = "backup-storage"
```

### Step 3: Deploy Control Plane

```bash
cd terraform
terraform init
terraform plan -var-file="terraform.tfvars" -target=module.control_plane
terraform apply -var-file="terraform.tfvars" -target=module.control_plane
```

### Step 4: Deploy Tenant Infrastructure

```bash
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

### Step 5: Configure Multi-Tenant Services

```bash
cd ../ansible
ansible-playbook -i inventory/multi-tenant-hosts.yml playbooks/multi-tenant-site.yml
```

## Post-Deployment Configuration

### Step 1: Access Platform

**Single-Node:**
- Grafana: https://your-siem-ip:3000
- Graylog: https://your-siem-ip:9000
- TheHive: https://your-siem-ip:9001
- Wazuh: https://your-siem-ip:443

**Multi-Tenant:**
- Management Console: https://your-control-plane-ip:8080
- Tenant Access: https://tenant-name.your-domain.com

### Step 2: Initial Login

Default credentials (change immediately):
- Username: admin
- Password: changeme123!

### Step 3: Configure Data Sources

1. **Add Log Sources:**
   ```bash
   # Install Wazuh agents on endpoints
   curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | apt-key add -
   echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | tee /etc/apt/sources.list.d/wazuh.list
   apt update && apt install wazuh-agent
   
   # Configure agent
   echo "WAZUH_MANAGER='your-siem-ip'" >> /var/ossec/etc/ossec.conf
   systemctl enable wazuh-agent
   systemctl start wazuh-agent
   ```

2. **Configure Syslog Sources:**
   - Point network devices to Graylog syslog input
   - Default port: 514 (UDP/TCP)

### Step 4: Import Dashboards

```bash
# Import Grafana dashboards
curl -X POST \
  http://admin:changeme123!@your-siem-ip:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @documentation/dashboards/executive_dashboard.json

curl -X POST \
  http://admin:changeme123!@your-siem-ip:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @documentation/dashboards/soc_operations_dashboard.json

curl -X POST \
  http://admin:changeme123!@your-siem-ip:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @documentation/dashboards/threat_hunting_dashboard.json
```

## Verification and Testing

### Step 1: System Health Check

```bash
# Check service status
ansible-playbook -i inventory/hosts.yml playbooks/health-check.yml

# Verify log ingestion
curl -X GET "http://your-siem-ip:9000/api/system/metrics/org.graylog2.throughput.input"

# Check Wazuh agent status
curl -u admin:changeme123! -X GET "https://your-siem-ip:55000/agents"
```

### Step 2: Generate Test Events

```bash
# Generate test security events
echo "Test failed login event" | logger -p auth.warning -t sshd
echo "Test malware detection" | logger -p daemon.alert -t antivirus

# Verify events in Graylog
curl -X GET "http://your-siem-ip:9000/api/search/universal/relative?query=*&range=300"
```

### Step 3: Test Alerting

1. Navigate to Grafana alerting
2. Verify alert rules are active
3. Test notification channels
4. Confirm TheHive case creation

## Troubleshooting

### Common Issues

**Service Not Starting:**
```bash
# Check service logs
journalctl -u wazuh-manager -f
journalctl -u graylog-server -f
journalctl -u grafana-server -f

# Restart services
systemctl restart wazuh-manager
systemctl restart graylog-server
systemctl restart grafana-server
```

**Network Connectivity:**
```bash
# Test network connectivity
telnet your-siem-ip 9000  # Graylog
telnet your-siem-ip 3000  # Grafana
telnet your-siem-ip 1514  # Syslog

# Check firewall rules
iptables -L -n
ufw status
```

**Performance Issues:**
```bash
# Check resource usage
htop
iotop
nethogs

# Monitor disk space
df -h
du -sh /var/log/*

# Check Elasticsearch cluster health
curl -X GET "localhost:9200/_cluster/health?pretty"
```

### Getting Help

1. **Documentation:** Check `/documentation/` directory
2. **Logs:** Review service logs in `/var/log/`
3. **Community:** Join our Discord/Slack community
4. **Support:** Contact support@your-org.com

## Next Steps

1. **Security Hardening:** Follow security hardening guide
2. **User Training:** Schedule user training sessions
3. **Integration:** Configure additional log sources
4. **Customization:** Implement custom rules and dashboards
5. **Monitoring:** Set up platform monitoring and alerting

## Maintenance

### Regular Tasks

**Daily:**
- Monitor system health
- Review critical alerts
- Check disk space

**Weekly:**
- Update threat intelligence feeds
- Review and tune alert rules
- Backup configuration

**Monthly:**
- Apply security updates
- Review user access
- Performance optimization
- Capacity planning

### Update Procedure

```bash
# Update platform components
cd siem-platform
git pull origin main

# Apply updates
cd terraform
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"

cd ../ansible
ansible-playbook -i inventory/hosts.yml playbooks/update.yml
```

---

*This quick start guide provides the essential steps for SIEM platform deployment. For detailed configuration options and advanced features, refer to the complete documentation.*

