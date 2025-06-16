# AfCyber SIEM Platform - Node-Specific Deployment Instructions

## 🎯 **Node Overview**

This deployment involves three different systems:

1. **🖥️ YOUR CLIENT MACHINE** - Your laptop/desktop (Windows/Linux/macOS)
2. **🏢 PROXMOX HOST** - Server at 172.16.0.43:8006
3. **🛡️ AFCYBER SIEM VM** - Ubuntu VM that will be created on Proxmox

---

## 📋 **Prerequisites Check**

### 🖥️ **[YOUR CLIENT MACHINE]** - Initial Setup

#### Step 1: Verify Client Machine Requirements
```bash
# On YOUR CLIENT MACHINE (Windows/Linux/macOS)
# Check if you have these tools installed:

# Git (required)
git --version

# SSH client (usually pre-installed)
ssh -V

# Web browser (for Proxmox web interface)
# Any modern browser (Chrome, Firefox, Safari, Edge)
```

#### Step 2: Download AfCyber SIEM Repository to Client Machine
```bash
# On YOUR CLIENT MACHINE
# Open terminal/command prompt and run:

cd ~/Desktop  # or your preferred directory
git clone https://github.com/ativoj/AfCyberSiem-platform.git
cd AfCyberSiem-platform

# Verify AfCyber SIEM download
ls -la
# You should see folders like:
# 01_Architecture_Diagrams/
# 02_IaC_Terraform_Proxmox/
# 03_Ansible_Playbooks/
# etc.
```

### 🏢 **[PROXMOX HOST]** - Verify Proxmox Access

#### Step 3: Access Proxmox Web Interface
```bash
# On YOUR CLIENT MACHINE
# Open web browser and navigate to:
https://172.16.0.43:8006

# Login with your Proxmox credentials
# Username: root
# Password: [your-proxmox-password]
# Realm: Linux PAM standard authentication
```

#### Step 4: Check Proxmox Resources for AfCyber SIEM
```bash
# On PROXMOX WEB INTERFACE (via your browser)
# 1. Click on your Proxmox node name in the left panel
# 2. Click "Summary" tab
# 3. Verify available resources for AfCyber SIEM:
#    - CPU: 32+ cores available
#    - Memory: 64+ GB available  
#    - Storage: 1+ TB available

# Note: If resources are insufficient, you may need to:
# - Stop other VMs temporarily
# - Add more hardware
# - Reduce AfCyber SIEM VM specifications
```

---

## 💾 **VM Creation and OS Installation**

### 🏢 **[PROXMOX WEB INTERFACE]** - Create AfCyber SIEM VM

#### Step 5: Download Ubuntu ISO to Proxmox
```bash
# Option A: Via Proxmox Web Interface
# 1. In Proxmox web interface, click on your node
# 2. Go to "local (node-name)" storage
# 3. Click "ISO Images" tab
# 4. Click "Download from URL"
# 5. URL: https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso
# 6. Wait for download to complete

# Option B: Via Proxmox Host SSH (if you have SSH access)
# SSH to 172.16.0.43 as root, then:
cd /var/lib/vz/template/iso/
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso
```

#### Step 6: Create AfCyber SIEM VM
```bash
# On PROXMOX WEB INTERFACE (via your browser)
# 1. Click "Create VM" button (top right)
# 2. Fill in AfCyber SIEM VM configuration:

# General Tab:
VM ID: 100
Name: afcyber-siem-platform
Resource Pool: (leave default)

# OS Tab:
Use CD/DVD disc image file (iso): Yes
Storage: local
ISO image: ubuntu-22.04.3-live-server-amd64.iso
Type: Linux
Version: 6.x - 2.6 Kernel

# System Tab:
Graphic card: Default
Machine: q35
BIOS: OVMF (UEFI)
Add EFI Disk: Yes (checked)
EFI Storage: local-lvm
Pre-Enroll keys: No (unchecked)
SCSI Controller: VirtIO SCSI single
Qemu Agent: Yes (checked)

# Hard Disk Tab:
Bus/Device: SCSI 0
Storage: local-lvm (or your preferred storage)
Disk size (GiB): 1000
Cache: Write back
Discard: No (unchecked)

# CPU Tab:
Sockets: 1
Cores: 32
Type: host
Enable NUMA: No (unchecked)

# Memory Tab:
Memory (MiB): 65536 (64GB)
Minimum memory (MiB): (leave default)
Ballooning Device: No (unchecked)

# Network Tab:
Bridge: vmbr0
VLAN Tag: (leave empty unless you use VLANs)
Model: VirtIO (paravirtualized)
MAC address: auto
Firewall: No (unchecked for now)

# Confirm Tab:
# Review AfCyber SIEM VM settings and click "Finish"
```

### 🛡️ **[AFCYBER SIEM VM CONSOLE]** - Install Ubuntu

#### Step 7: Install Ubuntu on AfCyber SIEM VM
```bash
# On PROXMOX WEB INTERFACE
# 1. Select your new AfCyber SIEM VM (ID: 100, afcyber-siem-platform)
# 2. Click "Start" button
# 3. Click "Console" tab to access VM console

# On AFCYBER SIEM VM CONSOLE (via Proxmox console)
# Follow Ubuntu installation wizard:

# Language: English
# Keyboard: [Your keyboard layout]
# Network: Configure network (should auto-detect)
# Proxy: (leave empty unless you use proxy)
# Mirror: (use default Ubuntu mirror)

# Storage configuration:
# - Use entire disk
# - Set up this disk as an LVM group: Yes
# - Encrypt the LVM group: No (for simplicity)

# Profile setup:
Your name: AfCyber SIEM Administrator
Your server's name: afcyber-siem-platform
Pick a username: ubuntu
Choose a password: [CREATE-STRONG-PASSWORD]
Confirm your password: [REPEAT-PASSWORD]

# SSH Setup:
Install OpenSSH server: Yes (IMPORTANT!)
Import SSH identity: No

# Featured Server Snaps:
# Don't select any additional snaps for now

# Installation will begin - wait for completion (10-15 minutes)
# When prompted, remove installation medium and reboot
```

#### Step 8: Initial AfCyber SIEM VM Configuration
```bash
# On AFCYBER SIEM VM CONSOLE (after reboot)
# Login with the ubuntu user you created

# Get AfCyber SIEM VM IP address
ip addr show
# Note the IP address (e.g., 192.168.1.100) - you'll need this for SSH

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git vim htop net-tools qemu-guest-agent

# Enable qemu-guest-agent
sudo systemctl enable qemu-guest-agent
sudo systemctl start qemu-guest-agent

# Test internet connectivity
ping -c 3 google.com
```

---

## 🔗 **SSH Connection Setup**

### 🖥️ **[YOUR CLIENT MACHINE]** - Connect to AfCyber SIEM VM

#### Step 9: SSH to AfCyber SIEM VM
```bash
# On YOUR CLIENT MACHINE
# Replace <AFCYBER_SIEM_VM_IP> with the IP address you noted in Step 8

ssh ubuntu@<AFCYBER_SIEM_VM_IP>
# Example: ssh ubuntu@192.168.1.100

# If prompted about host authenticity, type "yes"
# Enter the password you created during Ubuntu installation

# You should now be connected to the AfCyber SIEM VM via SSH
# The prompt should show: ubuntu@afcyber-siem-platform:~$
```

---

## 📥 **AfCyber SIEM Platform Installation**

### 🛡️ **[AFCYBER SIEM VM via SSH]** - Download and Install

#### Step 10: Download AfCyber SIEM Platform on VM
```bash
# On AFCYBER SIEM VM (via SSH from your client machine)
# You should see prompt: ubuntu@afcyber-siem-platform:~$

# Clone the AfCyber SIEM repository
git clone https://github.com/ativoj/AfCyberSiem-platform.git
cd AfCyberSiem-platform

# Verify AfCyber SIEM download
ls -la
# You should see the same folders as on your client machine
```

#### Step 11: Install Docker for AfCyber SIEM
```bash
# On AFCYBER SIEM VM (via SSH)
# Current directory: ~/AfCyberSiem-platform

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clean up
rm get-docker.sh

# Logout and login again for group changes
exit
```

#### Step 12: Reconnect and Verify Docker
```bash
# On YOUR CLIENT MACHINE
# Reconnect to AfCyber SIEM VM
ssh ubuntu@<AFCYBER_SIEM_VM_IP>

# On AFCYBER SIEM VM (via SSH)
# Verify Docker installation
docker --version
docker-compose --version

# Test Docker (should work without sudo)
docker run hello-world
```

### 🛡️ **[AFCYBER SIEM VM via SSH]** - Deploy AfCyber SIEM Services

#### Step 13: Configure AfCyber SIEM Environment
```bash
# On AFCYBER SIEM VM (via SSH)
# Navigate to Docker deployment directory
cd ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/

# Create AfCyber SIEM environment configuration
cat > .env << 'EOF'
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

# AfCyber SIEM - Cortex Configuration
CORTEX_KEY=afcyber-cortex-api-key
JOB_DIRECTORY=/tmp/afcyber-cortex-jobs
EOF

# Verify AfCyber SIEM environment file
cat .env
```

#### Step 14: Deploy AfCyber SIEM Platform
```bash
# On AFCYBER SIEM VM (via SSH)
# Current directory: ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/

# Pull AfCyber SIEM Docker images (this will take 10-20 minutes)
docker-compose pull

# Start AfCyber SIEM services
docker-compose up -d

# Check AfCyber SIEM deployment status
docker-compose ps

# Monitor AfCyber SIEM logs (optional - Ctrl+C to exit)
docker-compose logs -f
```

#### Step 15: Wait for AfCyber SIEM Services to Initialize
```bash
# On AFCYBER SIEM VM (via SSH)
# AfCyber SIEM services need time to fully initialize (5-10 minutes)

# Monitor AfCyber SIEM service status
watch docker-compose ps
# Press Ctrl+C when all services show "Up" status

# Check system resources
htop
# Press 'q' to quit htop

# Get AfCyber SIEM VM IP for web access
hostname -I
# Note this IP address for accessing AfCyber SIEM web interfaces
```

---

## 🔒 **Security Configuration**

### 🛡️ **[AFCYBER SIEM VM via SSH]** - Configure Firewall

#### Step 16: Configure UFW Firewall for AfCyber SIEM
```bash
# On AFCYBER SIEM VM (via SSH)

# Install and configure UFW
sudo apt install -y ufw

# Allow SSH (IMPORTANT - don't lock yourself out!)
sudo ufw allow 22

# Allow AfCyber SIEM web interfaces
sudo ufw allow 443   # Wazuh Dashboard
sudo ufw allow 3000  # Grafana
sudo ufw allow 9000  # Graylog
sudo ufw allow 9001  # TheHive
sudo ufw allow 8080  # OpenCTI
sudo ufw allow 514   # Syslog
sudo ufw allow 1514  # Wazuh agents

# Enable firewall
sudo ufw --force enable

# Check firewall status
sudo ufw status
```

---

## 🌐 **Access and Verification**

### 🖥️ **[YOUR CLIENT MACHINE]** - Access AfCyber SIEM Web Interfaces

#### Step 17: Access AfCyber SIEM Web Interfaces
```bash
# On YOUR CLIENT MACHINE
# Open web browser and access these AfCyber SIEM URLs:
# Replace <AFCYBER_SIEM_VM_IP> with the IP address from Step 15

# AfCyber SIEM - Wazuh Dashboard (Main SIEM interface)
https://<AFCYBER_SIEM_VM_IP>:443
# Username: admin
# Password: AfCyberSecretPassword
# Accept SSL certificate warning

# AfCyber SIEM - Grafana (Dashboards and visualization)
http://<AFCYBER_SIEM_VM_IP>:3000
# Username: admin
# Password: admin
# You'll be prompted to change password on first login

# AfCyber SIEM - Graylog (Log management)
http://<AFCYBER_SIEM_VM_IP>:9000
# Username: admin
# Password: admin

# AfCyber SIEM - TheHive (Case management)
http://<AFCYBER_SIEM_VM_IP>:9001
# First-time setup required

# AfCyber SIEM - OpenCTI (Threat intelligence)
http://<AFCYBER_SIEM_VM_IP>:8080
# Username: admin@afcyber-siem.local
# Password: AfCyberChangeMe
```

### 🛡️ **[AFCYBER SIEM VM via SSH]** - Verify Deployment

#### Step 18: Check AfCyber SIEM Service Status
```bash
# On AFCYBER SIEM VM (via SSH)

# Check all AfCyber SIEM containers are running
docker-compose ps

# Check system resources
free -h
df -h

# Check AfCyber SIEM service logs for any errors
docker-compose logs wazuh-manager | tail -20
docker-compose logs graylog | tail -20
docker-compose logs grafana | tail -20

# Test internal connectivity
curl -k https://localhost:443
curl http://localhost:3000
curl http://localhost:9000
```

---

## 📊 **Post-Deployment Configuration**

### 🖥️ **[YOUR CLIENT MACHINE]** - Configure AfCyber SIEM Dashboards

#### Step 19: Import AfCyber SIEM Dashboards
```bash
# On YOUR CLIENT MACHINE
# Navigate to the repository you downloaded in Step 2
cd ~/Desktop/AfCyberSiem-platform/06_Runbooks_and_UX/dashboards/

# You'll find AfCyber SIEM dashboard JSON files:
ls -la *.json
# - executive_dashboard.json
# - soc_operations_dashboard.json  
# - threat_hunting_dashboard.json

# Import these into AfCyber SIEM Grafana:
# 1. Access Grafana at http://<AFCYBER_SIEM_VM_IP>:3000
# 2. Go to "+" menu → Import
# 3. Upload each JSON file
```

### 🛡️ **[AFCYBER SIEM VM via SSH]** - Create Management Scripts

#### Step 20: Create AfCyber SIEM Monitoring Scripts
```bash
# On AFCYBER SIEM VM (via SSH)
# Create AfCyber SIEM monitoring script
cat > ~/monitor_afcyber_siem.sh << 'EOF'
#!/bin/bash
echo "=== AfCyber SIEM Platform Status ==="
echo "Date: $(date)"
echo "Server IP: $(hostname -I | awk '{print $1}')"
echo "Uptime: $(uptime -p)"
echo ""
echo "Memory Usage:"
free -h | grep -E "(Mem|Swap)"
echo ""
echo "Disk Usage:"
df -h / | tail -1
echo ""
echo "AfCyber SIEM Docker Containers:"
cd ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/
docker-compose ps
echo ""
echo "AfCyber SIEM Service URLs:"
IP=$(hostname -I | awk '{print $1}')
echo "- Wazuh Dashboard: https://$IP:443"
echo "- Grafana: http://$IP:3000"
echo "- Graylog: http://$IP:9000"
echo "- TheHive: http://$IP:9001"
echo "- OpenCTI: http://$IP:8080"
echo "================================="
EOF

# Make script executable
chmod +x ~/monitor_afcyber_siem.sh

# Test the AfCyber SIEM script
./monitor_afcyber_siem.sh
```

#### Step 21: Create AfCyber SIEM Backup Script
```bash
# On AFCYBER SIEM VM (via SSH)
# Create AfCyber SIEM backup script
cat > ~/backup_afcyber_siem.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/tmp/afcyber-siem-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Creating AfCyber SIEM backup in $BACKUP_DIR..."

# Stop AfCyber SIEM services
cd ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/
docker-compose stop

# Backup AfCyber SIEM Docker volumes
sudo tar -czf $BACKUP_DIR/afcyber-siem-docker-volumes.tar.gz /var/lib/docker/volumes/

# Backup AfCyber SIEM configurations
cp -r ~/AfCyberSiem-platform $BACKUP_DIR/

# Restart AfCyber SIEM services
docker-compose start

echo "AfCyber SIEM backup completed: $BACKUP_DIR"
ls -lh $BACKUP_DIR/
EOF

# Make script executable
chmod +x ~/backup_afcyber_siem.sh
```

---

## 🎯 **Agent Installation (Optional)**

### 🖥️ **[CLIENT MACHINES TO MONITOR]** - Install Wazuh Agents for AfCyber SIEM

#### Step 22: Install Wazuh Agent on Linux Clients for AfCyber SIEM
```bash
# On ANY LINUX MACHINE you want to monitor with AfCyber SIEM
# (NOT on the AfCyber SIEM VM itself)

# Add Wazuh repository
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | sudo apt-key add -
echo "deb https://packages.wazuh.com/4.x/apt/ stable main" | sudo tee /etc/apt/sources.list.d/wazuh.list

# Install agent
sudo apt update
sudo apt install -y wazuh-agent

# Configure agent to connect to AfCyber SIEM (replace <AFCYBER_SIEM_VM_IP> with your AfCyber SIEM VM IP)
sudo sed -i "s/MANAGER_IP/<AFCYBER_SIEM_VM_IP>/" /var/ossec/etc/ossec.conf

# Start agent
sudo systemctl enable wazuh-agent
sudo systemctl start wazuh-agent

# Check agent status
sudo systemctl status wazuh-agent
```

#### Step 23: Install Wazuh Agent on Windows Clients for AfCyber SIEM
```powershell
# On WINDOWS MACHINES you want to monitor with AfCyber SIEM
# Run PowerShell as Administrator

# Download and install Wazuh agent
Invoke-WebRequest -Uri "https://packages.wazuh.com/4.x/windows/wazuh-agent-4.7.0-1.msi" -OutFile "wazuh-agent.msi"

# Install with AfCyber SIEM VM IP (replace <AFCYBER_SIEM_VM_IP>)
msiexec /i wazuh-agent.msi /q WAZUH_MANAGER="<AFCYBER_SIEM_VM_IP>"

# Start service
Start-Service WazuhSvc
```

---

## ✅ **Final Verification**

### 🖥️ **[YOUR CLIENT MACHINE]** - Final AfCyber SIEM Testing

#### Step 24: Complete AfCyber SIEM System Test
```bash
# On YOUR CLIENT MACHINE
# Test all AfCyber SIEM web interfaces are accessible:

# 1. AfCyber SIEM - Wazuh Dashboard: https://<AFCYBER_SIEM_VM_IP>:443
#    - Should show Wazuh dashboard
#    - Check if agents appear (if you installed any)

# 2. AfCyber SIEM - Grafana: http://<AFCYBER_SIEM_VM_IP>:3000
#    - Should show Grafana login
#    - Import dashboards if not done already

# 3. AfCyber SIEM - Graylog: http://<AFCYBER_SIEM_VM_IP>:9000
#    - Should show Graylog interface
#    - Check for incoming logs

# 4. AfCyber SIEM - TheHive: http://<AFCYBER_SIEM_VM_IP>:9001
#    - Should show TheHive setup page
#    - Complete initial configuration

# 5. AfCyber SIEM - OpenCTI: http://<AFCYBER_SIEM_VM_IP>:8080
#    - Should show OpenCTI login
#    - Login with admin@afcyber-siem.local / AfCyberChangeMe
```

### 🛡️ **[AFCYBER SIEM VM via SSH]** - Final Status Check

#### Step 25: Final AfCyber SIEM System Status
```bash
# On AFCYBER SIEM VM (via SSH)
# Run final AfCyber SIEM status check
./monitor_afcyber_siem.sh

# Check all AfCyber SIEM services are healthy
cd ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/
docker-compose ps

# Check system performance
htop
# Press 'q' to quit

# Check disk usage
df -h

# Save important AfCyber SIEM information
echo "AfCyber SIEM Platform Deployment Complete!" > ~/afcyber_siem_deployment_complete.txt
echo "Date: $(date)" >> ~/afcyber_siem_deployment_complete.txt
echo "AfCyber SIEM VM IP: $(hostname -I | awk '{print $1}')" >> ~/afcyber_siem_deployment_complete.txt
echo "AfCyber SIEM Access URLs:" >> ~/afcyber_siem_deployment_complete.txt
echo "- Wazuh: https://$(hostname -I | awk '{print $1}'):443" >> ~/afcyber_siem_deployment_complete.txt
echo "- Grafana: http://$(hostname -I | awk '{print $1}'):3000" >> ~/afcyber_siem_deployment_complete.txt
echo "- Graylog: http://$(hostname -I | awk '{print $1}'):9000" >> ~/afcyber_siem_deployment_complete.txt
echo "- TheHive: http://$(hostname -I | awk '{print $1}'):9001" >> ~/afcyber_siem_deployment_complete.txt
echo "- OpenCTI: http://$(hostname -I | awk '{print $1}'):8080" >> ~/afcyber_siem_deployment_complete.txt

cat ~/afcyber_siem_deployment_complete.txt
```

---

## 📋 **Node-Specific Command Summary**

### 🖥️ **Commands for YOUR CLIENT MACHINE:**
- Download AfCyber SIEM repository: `git clone https://github.com/ativoj/AfCyberSiem-platform.git`
- Access Proxmox web interface: Browser → `https://172.16.0.43:8006`
- SSH to AfCyber SIEM VM: `ssh ubuntu@<AFCYBER_SIEM_VM_IP>`
- Access AfCyber SIEM web interfaces: Browser → Various URLs

### 🏢 **Actions on PROXMOX WEB INTERFACE:**
- Download Ubuntu ISO
- Create AfCyber SIEM VM with specified configuration
- Start VM and access console
- Monitor AfCyber SIEM VM performance

### 🛡️ **Commands for AFCYBER SIEM VM (via SSH):**
- All installation commands: `git clone`, `docker-compose up -d`, etc.
- System configuration: `sudo ufw allow`, firewall setup
- AfCyber SIEM monitoring scripts: `./monitor_afcyber_siem.sh`, `./backup_afcyber_siem.sh`
- Service management: `docker-compose ps`, `docker-compose logs`

### 🖥️ **Commands for CLIENT MACHINES TO MONITOR:**
- Install Wazuh agents on systems you want to monitor with AfCyber SIEM
- Configure agents to point to AfCyber SIEM VM IP

---

**🎉 Deployment Complete! Your AfCyber SIEM Platform is now running on your Proxmox server at 172.16.0.43:8006**

