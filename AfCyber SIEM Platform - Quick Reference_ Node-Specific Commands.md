# AfCyber SIEM Platform - Quick Reference: Node-Specific Commands

## 🎯 **Node Identification**

### 🖥️ **YOUR CLIENT MACHINE** 
- Your laptop/desktop (Windows/Linux/macOS)
- Used for: Downloading files, accessing web interfaces, SSH connections

### 🏢 **PROXMOX HOST** 
- Server at 172.16.0.43:8006
- Used for: VM creation, resource management, ISO storage

### 🛡️ **AFCYBER SIEM VM** 
- Ubuntu VM created on Proxmox (will get IP like 192.168.1.100)
- Used for: Running AfCyber SIEM services, Docker containers

---

## 📋 **Step-by-Step Node Actions for AfCyber SIEM**

### **Phase 1: Preparation**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 1 | 🖥️ CLIENT | Download AfCyber SIEM repo | `git clone https://github.com/ativoj/AfCyberSiem-platform.git` |
| 2 | 🖥️ CLIENT | Access Proxmox | Browser → `https://172.16.0.43:8006` |
| 3 | 🏢 PROXMOX | Download ISO | Web interface → Download Ubuntu 22.04 ISO |
| 4 | 🏢 PROXMOX | Create AfCyber SIEM VM | Web interface → Create VM (32 vCPU, 64GB RAM, 1TB) |

### **Phase 2: OS Installation**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 5 | 🏢 PROXMOX | Start AfCyber SIEM VM | Web interface → Start VM → Console |
| 6 | 🛡️ AFCYBER SIEM VM | Install Ubuntu | Console → Follow Ubuntu installation wizard |
| 7 | 🛡️ AFCYBER SIEM VM | Initial setup | `sudo apt update && sudo apt upgrade -y` |
| 8 | 🛡️ AFCYBER SIEM VM | Get IP address | `ip addr show` (note the IP) |

### **Phase 3: SSH Connection**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 9 | 🖥️ CLIENT | SSH to AfCyber SIEM VM | `ssh ubuntu@<AFCYBER_SIEM_VM_IP>` |
| 10 | 🛡️ AFCYBER SIEM VM | Clone AfCyber SIEM repo | `git clone https://github.com/ativoj/AfCyberSiem-platform.git` |

### **Phase 4: Docker Installation**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 11 | 🛡️ AFCYBER SIEM VM | Install Docker | `curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh` |
| 12 | 🛡️ AFCYBER SIEM VM | Add user to docker | `sudo usermod -aG docker ubuntu` |
| 13 | 🛡️ AFCYBER SIEM VM | Install Compose | `sudo curl -L "..." -o /usr/local/bin/docker-compose` |
| 14 | 🖥️ CLIENT | Reconnect SSH | `ssh ubuntu@<AFCYBER_SIEM_VM_IP>` (after logout/login) |

### **Phase 5: AfCyber SIEM Deployment**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 15 | 🛡️ AFCYBER SIEM VM | Navigate to Docker dir | `cd ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/` |
| 16 | 🛡️ AFCYBER SIEM VM | Create .env file | `cat > .env << 'EOF'` (with AfCyber SIEM configuration) |
| 17 | 🛡️ AFCYBER SIEM VM | Pull images | `docker-compose pull` |
| 18 | 🛡️ AFCYBER SIEM VM | Start AfCyber SIEM services | `docker-compose up -d` |
| 19 | 🛡️ AFCYBER SIEM VM | Check status | `docker-compose ps` |

### **Phase 6: Security & Access**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 20 | 🛡️ AFCYBER SIEM VM | Configure firewall | `sudo ufw allow 22,443,3000,9000,9001,8080` |
| 21 | 🛡️ AFCYBER SIEM VM | Enable firewall | `sudo ufw --force enable` |
| 22 | 🖥️ CLIENT | Access AfCyber SIEM Wazuh | Browser → `https://<AFCYBER_SIEM_VM_IP>:443` |
| 23 | 🖥️ CLIENT | Access AfCyber SIEM Grafana | Browser → `http://<AFCYBER_SIEM_VM_IP>:3000` |
| 24 | 🖥️ CLIENT | Access AfCyber SIEM Graylog | Browser → `http://<AFCYBER_SIEM_VM_IP>:9000` |

### **Phase 7: Monitoring Setup**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 25 | 🛡️ AFCYBER SIEM VM | Create monitor script | `cat > ~/monitor_afcyber_siem.sh << 'EOF'` |
| 26 | 🛡️ AFCYBER SIEM VM | Create backup script | `cat > ~/backup_afcyber_siem.sh << 'EOF'` |
| 27 | 🛡️ AFCYBER SIEM VM | Test monitoring | `./monitor_afcyber_siem.sh` |

### **Phase 8: Agent Installation (Optional)**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 28 | 🖥️ OTHER LINUX | Install Wazuh agent | `sudo apt install wazuh-agent` |
| 29 | 🖥️ OTHER LINUX | Configure agent for AfCyber SIEM | `sudo sed -i "s/MANAGER_IP/<AFCYBER_SIEM_VM_IP>/" /var/ossec/etc/ossec.conf` |
| 30 | 💻 WINDOWS | Install agent for AfCyber SIEM | Download MSI and install with AfCyber SIEM VM IP |

---

## 🚨 **Critical Node Warnings for AfCyber SIEM**

### ⚠️ **DO NOT confuse these nodes:**
- **DON'T** run Docker commands on your CLIENT MACHINE
- **DON'T** try to access AfCyber SIEM web interfaces from AFCYBER SIEM VM console
- **DON'T** install AfCyber SIEM services on PROXMOX HOST directly

### ✅ **Remember:**
- **CLIENT MACHINE**: For downloading, browsing, SSH connections
- **PROXMOX HOST**: For VM management only
- **AFCYBER SIEM VM**: For all AfCyber SIEM installation and configuration

---

## 🔍 **Quick Troubleshooting by Node**

### 🖥️ **CLIENT MACHINE Issues:**
- Can't access Proxmox web interface → Check network connectivity
- Can't SSH to AfCyber SIEM VM → Check VM IP address and firewall
- Can't access AfCyber SIEM web interfaces → Check AfCyber SIEM VM firewall and services

### 🏢 **PROXMOX HOST Issues:**
- Can't create AfCyber SIEM VM → Check available resources
- AfCyber SIEM VM won't start → Check storage and memory allocation
- Console not working → Try different browser or VNC viewer

### 🛡️ **AFCYBER SIEM VM Issues:**
- Docker commands fail → Check if user is in docker group
- AfCyber SIEM services won't start → Check system resources and logs
- AfCyber SIEM web interfaces not accessible → Check firewall and service status

---

## 🎯 **AfCyber SIEM Service URLs**

Once deployed, access your AfCyber SIEM platform at:

| Service | URL | Purpose |
|---------|-----|---------|
| **AfCyber SIEM - Wazuh** | `https://<AFCYBER_SIEM_VM_IP>:443` | Main security monitoring |
| **AfCyber SIEM - Grafana** | `http://<AFCYBER_SIEM_VM_IP>:3000` | Dashboards and visualization |
| **AfCyber SIEM - Graylog** | `http://<AFCYBER_SIEM_VM_IP>:9000` | Log management and search |
| **AfCyber SIEM - TheHive** | `http://<AFCYBER_SIEM_VM_IP>:9001` | Incident response |
| **AfCyber SIEM - OpenCTI** | `http://<AFCYBER_SIEM_VM_IP>:8080` | Threat intelligence |

---

## 🔧 **AfCyber SIEM Management Commands**

### **On AFCYBER SIEM VM (via SSH):**
```bash
# Monitor AfCyber SIEM status
./monitor_afcyber_siem.sh

# Backup AfCyber SIEM
./backup_afcyber_siem.sh

# Check AfCyber SIEM services
cd ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/
docker-compose ps

# View AfCyber SIEM logs
docker-compose logs <service_name>

# Restart AfCyber SIEM services
docker-compose restart

# Stop AfCyber SIEM services
docker-compose stop

# Start AfCyber SIEM services
docker-compose start
```

---

## 🚀 **Quick Deployment Option**

### **Automated AfCyber SIEM Deployment:**
```bash
# On AFCYBER SIEM VM (via SSH)
wget https://raw.githubusercontent.com/ativoj/AfCyberSiem-platform/main/quick_deploy_afcyber_siem.sh
chmod +x quick_deploy_afcyber_siem.sh
./quick_deploy_afcyber_siem.sh
```

---

**💡 Pro Tip: Always verify which node you're working on by checking the command prompt:**
- CLIENT: `user@client-machine:~$`
- AFCYBER SIEM VM: `ubuntu@afcyber-siem-platform:~$`
- PROXMOX: `root@proxmox-host:~#`

**🎉 Your AfCyber SIEM Platform will be ready for enterprise security monitoring!**

