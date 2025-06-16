# AfCyber SIEM Platform - Single-Node Deployment Guide for Proxmox 172.16.0.43:8006

## 🎯 **Deployment Overview**

This guide will walk you through deploying the complete **AfCyber SIEM Platform** on your Proxmox server at `172.16.0.43:8006` using the single-node architecture.

### 📋 **What You'll Deploy**
- **Complete AfCyber SIEM Stack** on a single VM
- **All Services**: Wazuh, Graylog, TheHive, OpenCTI, MISP, Grafana
- **Resource Requirements**: 32 vCPU, 64GB RAM, 1TB SSD
- **Capacity**: 10,000 events/second, 1,000 endpoints

---

## 🔧 **Prerequisites**

### 1. **Proxmox Server Requirements**
- ✅ Proxmox VE 7.0+ (preferably 8.0+)
- ✅ Available resources: 32+ vCPU, 64+ GB RAM, 1+ TB storage
- ✅ Internet connectivity for package downloads
- ✅ Administrative access to Proxmox web interface

### 2. **Client Machine Requirements**
- ✅ Windows/Linux/macOS with internet access
- ✅ SSH client (PuTTY, OpenSSH, or built-in terminal)
- ✅ Web browser for Proxmox management
- ✅ Git client (optional, for cloning repository)

### 3. **Network Information Needed**
- ✅ Proxmox management IP: `172.16.0.43`
- ✅ Available IP range for VM deployment
- ✅ Gateway and DNS server information
- ✅ VLAN configuration (if applicable)

---

## 📥 **Step 1: Download and Prepare Files**

### Option A: Download from GitHub (Recommended)
```bash
# Clone the AfCyber SIEM repository
git clone https://github.com/ativoj/AfCyberSiem-platform.git
cd AfCyberSiem-platform
```

### Option B: Download ZIP Package
1. Go to: https://github.com/ativoj/AfCyberSiem-platform
2. Click **"Code"** → **"Download ZIP"**
3. Extract the ZIP file to your working directory

### Verify Files
```bash
# Check AfCyber SIEM repository structure
ls -la
# You should see:
# 01_Architecture_Diagrams/
# 02_IaC_Terraform_Proxmox/
# 03_Ansible_Playbooks/
# 04_Docker_Helm_Packaging/
# docs/
```

---

## 🌐 **Step 2: Access Proxmox Web Interface**

### 1. **Connect to Proxmox**
1. Open web browser
2. Navigate to: `https://172.16.0.43:8006`
3. Accept SSL certificate warning (if self-signed)
4. Login with your Proxmox credentials

### 2. **Verify Resources**
1. Click on your Proxmox node name
2. Check **Summary** tab for available:
   - **CPU**: Ensure 32+ cores available
   - **Memory**: Ensure 64+ GB available
   - **Storage**: Ensure 1+ TB available

### 3. **Check Network Configuration**
1. Go to **Datacenter** → **Network**
2. Note your bridge name (usually `vmbr0`)
3. Verify internet connectivity from Proxmox node

---

## 💾 **Step 3: Prepare VM Template (Optional but Recommended)**

### 1. **Download Ubuntu 22.04 LTS ISO**
```bash
# On Proxmox node via SSH or shell
cd /var/lib/vz/template/iso/
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso
```

### 2. **Create VM Template**
1. In Proxmox web interface, click **"Create VM"**
2. **General Tab**:
   - **VM ID**: 9000 (for template)
   - **Name**: ubuntu-22.04-afcyber-template
3. **OS Tab**:
   - **ISO Image**: ubuntu-22.04.3-live-server-amd64.iso
4. **System Tab**:
   - **Machine**: q35
   - **BIOS**: OVMF (UEFI)
   - **Add EFI Disk**: Yes
5. **Hard Disk Tab**:
   - **Bus/Device**: SCSI 0
   - **Storage**: local-lvm
   - **Disk size**: 32 GB (for template)
6. **CPU Tab**:
   - **Cores**: 2 (for template)
7. **Memory Tab**:
   - **Memory**: 4096 MB (for template)
8. **Network Tab**:
   - **Bridge**: vmbr0
   - **Model**: VirtIO

### 3. **Install Ubuntu Template**
1. Start the VM and install Ubuntu 22.04 LTS
2. During installation:
   - **Username**: ubuntu
   - **Enable SSH server**: Yes
   - **Install minimal system**: Yes
3. After installation, update the system:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y qemu-guest-agent cloud-init
sudo systemctl enable qemu-guest-agent
sudo shutdown -h now
```
4. Convert to template: Right-click VM → **"Convert to template"**

---

## 🚀 **Step 4: Deploy AfCyber SIEM VM**

### Method A: Manual VM Creation (Recommended for beginners)

#### 1. **Create AfCyber SIEM VM**
1. In Proxmox, click **"Create VM"**
2. **General Tab**:
   - **VM ID**: 100
   - **Name**: afcyber-siem-platform
3. **OS Tab**:
   - **ISO Image**: ubuntu-22.04.3-live-server-amd64.iso
4. **System Tab**:
   - **Machine**: q35
   - **BIOS**: OVMF (UEFI)
   - **Add EFI Disk**: Yes
5. **Hard Disk Tab**:
   - **Bus/Device**: SCSI 0
   - **Storage**: local-lvm (or your preferred storage)
   - **Disk size**: 1000 GB (1TB)
   - **Cache**: Write back
6. **CPU Tab**:
   - **Sockets**: 1
   - **Cores**: 32
   - **Type**: host
7. **Memory Tab**:
   - **Memory**: 65536 MB (64GB)
   - **Ballooning Device**: Disabled
8. **Network Tab**:
   - **Bridge**: vmbr0
   - **Model**: VirtIO
   - **Firewall**: Disabled (for now)

#### 2. **Install Ubuntu on AfCyber SIEM VM**
1. Start the VM: Click **"Start"**
2. Open console: Click **"Console"**
3. Install Ubuntu 22.04 LTS:
   - **Username**: ubuntu
   - **Password**: (choose a strong password)
   - **Server name**: afcyber-siem-platform
   - **Enable SSH server**: Yes
   - **Install OpenSSH server**: Yes

#### 3. **Initial VM Configuration**
```bash
# After Ubuntu installation, login and run:
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git vim htop net-tools qemu-guest-agent

# Enable qemu-guest-agent
sudo systemctl enable qemu-guest-agent
sudo systemctl start qemu-guest-agent

# Get VM IP address
ip addr show
# Note the IP address for SSH access
```

### Method B: Terraform Deployment (Advanced)

#### 1. **Install Terraform on Your Client Machine**
```bash
# On Ubuntu/Debian
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# On Windows (using Chocolatey)
choco install terraform

# On macOS (using Homebrew)
brew install terraform
```

#### 2. **Configure Terraform Variables**
```bash
cd 02_IaC_Terraform_Proxmox/
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
# Proxmox Configuration
proxmox_api_url = "https://172.16.0.43:8006/api2/json"
proxmox_api_token_id = "your-token-id"
proxmox_api_token_secret = "your-token-secret"
proxmox_node = "your-node-name"

# AfCyber SIEM Single-Node Configuration
single_node_enabled = true
single_node_vm_id = 100
single_node_name = "afcyber-siem-platform"
single_node_cores = 32
single_node_memory = 65536
single_node_disk_size = "1000G"

# Network Configuration
network_bridge = "vmbr0"
```

#### 3. **Create Proxmox API Token**
1. In Proxmox web interface: **Datacenter** → **Permissions** → **API Tokens**
2. Click **"Add"**
3. **User**: root@pam
4. **Token ID**: afcyber-terraform
5. **Privilege Separation**: Unchecked
6. Copy the **Token ID** and **Secret**

#### 4. **Deploy with Terraform**
```bash
# Initialize Terraform
terraform init

# Plan AfCyber SIEM deployment
terraform plan -var-file="terraform.tfvars"

# Apply AfCyber SIEM deployment
terraform apply -var-file="terraform.tfvars"
```

---

## ⚙️ **Step 5: Configure AfCyber SIEM Services**

### 1. **SSH into the AfCyber SIEM VM**
```bash
# Replace with your VM's IP address
ssh ubuntu@<AFCYBER_SIEM_VM_IP>
```

### 2. **Download AfCyber SIEM Installation Scripts**
```bash
# On the AfCyber SIEM VM
git clone https://github.com/ativoj/AfCyberSiem-platform.git
cd AfCyberSiem-platform
```

### 3. **Run Ansible Installation**

#### Option A: Automated Installation (Recommended)
```bash
# Install Ansible
sudo apt update
sudo apt install -y ansible

# Navigate to Ansible directory
cd 03_Ansible_Playbooks/

# Update inventory with localhost
cat > inventory/hosts.yml << EOF
all:
  hosts:
    afcyber-siem-node:
      ansible_host: localhost
      ansible_connection: local
      ansible_user: ubuntu
      ansible_become: yes
EOF

# Run complete AfCyber SIEM installation
ansible-playbook -i inventory/hosts.yml playbooks/site.yml
```

#### Option B: Manual Service Installation

##### Install Docker and Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
exit
# SSH back in
ssh ubuntu@<AFCYBER_SIEM_VM_IP>
```

##### Deploy with Docker Compose
```bash
cd AfCyberSiem-platform/04_Docker_Helm_Packaging/

# Create environment file for AfCyber SIEM
cat > .env << EOF
# AfCyber SIEM - Wazuh Configuration
WAZUH_API_USERNAME=afcyber-admin
WAZUH_API_PASSWORD=AfCyber$3cr37P450r.*-
INDEXER_USERNAME=admin
INDEXER_PASSWORD=AfCyberSecretPassword

# AfCyber SIEM - Graylog Configuration
GRAYLOG_PASSWORD_SECRET=afcyberpasswordpepper
GRAYLOG_ROOT_PASSWORD_SHA2=8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918

# AfCyber SIEM - OpenCTI Configuration
OPENCTI_ADMIN_EMAIL=admin@afcyber-siem.local
OPENCTI_ADMIN_PASSWORD=AfCyberChangeMe
OPENCTI_ADMIN_TOKEN=AfCyberChangeMe
EOF

# Deploy AfCyber SIEM stack
docker-compose up -d

# Check AfCyber SIEM deployment status
docker-compose ps
```

---

## 🔍 **Step 6: Verify AfCyber SIEM Deployment**

### 1. **Check Service Status**
```bash
# Check Docker containers
docker-compose ps

# Check system resources
htop
df -h
```

### 2. **Access AfCyber SIEM Web Interfaces**

Replace `<AFCYBER_SIEM_VM_IP>` with your AfCyber SIEM VM's IP address:

#### **AfCyber SIEM - Grafana Dashboard**
- **URL**: `http://<AFCYBER_SIEM_VM_IP>:3000`
- **Username**: admin
- **Password**: admin
- **Purpose**: Main dashboard and visualization

#### **AfCyber SIEM - Graylog Web Interface**
- **URL**: `http://<AFCYBER_SIEM_VM_IP>:9000`
- **Username**: admin
- **Password**: admin
- **Purpose**: Log search and analysis

#### **AfCyber SIEM - TheHive Case Management**
- **URL**: `http://<AFCYBER_SIEM_VM_IP>:9001`
- **Setup**: First-time configuration required
- **Purpose**: Incident response and case management

#### **AfCyber SIEM - Wazuh Dashboard**
- **URL**: `https://<AFCYBER_SIEM_VM_IP>:443`
- **Username**: admin
- **Password**: AfCyberSecretPassword
- **Purpose**: Agent management and security monitoring

### 3. **Test Connectivity**
```bash
# Test internal connectivity
curl -k https://localhost:443
curl http://localhost:3000
curl http://localhost:9000

# Check AfCyber SIEM logs
docker-compose logs wazuh-manager
docker-compose logs graylog
```

---

## 🛡️ **Step 7: Security Configuration**

### 1. **Configure Firewall**
```bash
# Install UFW
sudo apt install -y ufw

# Allow SSH
sudo ufw allow 22

# Allow AfCyber SIEM web interfaces
sudo ufw allow 443   # Wazuh
sudo ufw allow 3000  # Grafana
sudo ufw allow 9000  # Graylog
sudo ufw allow 9001  # TheHive

# Enable firewall
sudo ufw enable
```

### 2. **Change Default Passwords**
1. **Grafana**: Login and change admin password
2. **Graylog**: Change admin password in web interface
3. **Wazuh**: Update password in configuration
4. **TheHive**: Set up during first login

### 3. **Configure SSL Certificates**
```bash
# Generate self-signed certificates for AfCyber SIEM (for testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/afcyber-siem.key \
  -out /etc/ssl/certs/afcyber-siem.crt \
  -subj "/C=US/ST=State/L=City/O=AfCyber/CN=afcyber-siem.local"
```

---

## 📊 **Step 8: Initial Configuration**

### 1. **Configure Wazuh Agents for AfCyber SIEM**
```bash
# On client machines you want to monitor
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo apt-key add -
echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list
sudo apt update
sudo apt install -y wazuh-agent

# Configure agent to connect to AfCyber SIEM
sudo sed -i "s/MANAGER_IP/<AFCYBER_SIEM_VM_IP>/" /var/ossec/etc/ossec.conf
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent
```

### 2. **Configure Log Sources**
1. **Syslog**: Configure devices to send logs to `<AFCYBER_SIEM_VM_IP>:514`
2. **Windows Events**: Install Wazuh agent on Windows machines
3. **Network Devices**: Configure SNMP and syslog forwarding

### 3. **Set Up AfCyber SIEM Dashboards**
1. Import dashboard configurations from `06_Runbooks_and_UX/dashboards/`
2. Configure data sources in Grafana
3. Set up alerting rules

---

## 🔧 **Step 9: Troubleshooting**

### Common Issues and Solutions

#### **AfCyber SIEM Services Not Starting**
```bash
# Check Docker logs
docker-compose logs <service_name>

# Restart AfCyber SIEM services
docker-compose restart

# Check system resources
free -h
df -h
```

#### **AfCyber SIEM Web Interfaces Not Accessible**
```bash
# Check if ports are listening
sudo netstat -tlnp | grep -E '(443|3000|9000|9001)'

# Check firewall
sudo ufw status

# Check Docker networks
docker network ls
```

#### **Performance Issues**
```bash
# Monitor system resources
htop
iotop
docker stats

# Adjust memory limits in docker-compose.yml
# Restart AfCyber SIEM services with more resources
```

---

## 📈 **Step 10: Monitoring and Maintenance**

### 1. **Set Up AfCyber SIEM Monitoring**
```bash
# Create AfCyber SIEM monitoring script
cat > /home/ubuntu/monitor_afcyber_siem.sh << 'EOF'
#!/bin/bash
echo "=== AfCyber SIEM Platform Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Memory Usage: $(free -h | grep Mem)"
echo "Disk Usage: $(df -h / | tail -1)"
echo "AfCyber SIEM Docker Containers:"
docker-compose ps
echo "=========================="
EOF

chmod +x /home/ubuntu/monitor_afcyber_siem.sh

# Add to crontab for regular monitoring
(crontab -l 2>/dev/null; echo "*/15 * * * * /home/ubuntu/monitor_afcyber_siem.sh >> /var/log/afcyber_siem_monitor.log") | crontab -
```

### 2. **Backup Configuration**
```bash
# Create AfCyber SIEM backup script
cat > /home/ubuntu/backup_afcyber_siem.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/afcyber-siem-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup Docker volumes
docker-compose stop
tar -czf $BACKUP_DIR/afcyber-siem-docker-volumes.tar.gz /var/lib/docker/volumes/
docker-compose start

# Backup configurations
cp -r /home/ubuntu/AfCyberSiem-platform $BACKUP_DIR/
echo "AfCyber SIEM backup completed: $BACKUP_DIR"
EOF

chmod +x /home/ubuntu/backup_afcyber_siem.sh
```

### 3. **Update Procedures**
```bash
# Regular AfCyber SIEM updates
sudo apt update && sudo apt upgrade -y
docker-compose pull
docker-compose up -d
```

---

## ✅ **AfCyber SIEM Deployment Checklist**

- [ ] Proxmox server accessible at 172.16.0.43:8006
- [ ] VM created with 32 vCPU, 64GB RAM, 1TB storage
- [ ] Ubuntu 22.04 LTS installed and updated
- [ ] Docker and Docker Compose installed
- [ ] AfCyber SIEM platform deployed with docker-compose
- [ ] All AfCyber SIEM web interfaces accessible
- [ ] Default passwords changed
- [ ] Firewall configured
- [ ] SSL certificates configured
- [ ] Wazuh agents installed on monitored systems
- [ ] Log sources configured
- [ ] AfCyber SIEM dashboards imported and configured
- [ ] Monitoring and backup scripts created
- [ ] Documentation reviewed and customized

---

## 🆘 **Support and Next Steps**

### **If You Need Help**
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs <service>`
3. Visit: https://github.com/ativoj/AfCyberSiem-platform/issues
4. Check documentation: `docs/index.html` in the repository

### **Next Steps**
1. **Add More Agents**: Install Wazuh agents on all systems you want to monitor
2. **Configure Alerting**: Set up email/Slack notifications
3. **Customize Dashboards**: Modify dashboards for your specific needs
4. **Integrate External Tools**: Configure ServiceNow, PagerDuty, etc.
5. **Scale Up**: Consider multi-tenant deployment for larger environments

### **Performance Optimization**
- Monitor resource usage and adjust as needed
- Consider SSD storage for better performance
- Implement log rotation and retention policies
- Set up automated backups

---

**🎉 Congratulations! Your AfCyber SIEM Platform is now deployed and ready for production use!**

