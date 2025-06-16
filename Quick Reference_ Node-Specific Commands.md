# Quick Reference: Node-Specific Commands

## 🎯 **Node Identification**

### 🖥️ **YOUR CLIENT MACHINE** 
- Your laptop/desktop (Windows/Linux/macOS)
- Used for: Downloading files, accessing web interfaces, SSH connections

### 🏢 **PROXMOX HOST** 
- Server at 172.16.0.43:8006
- Used for: VM creation, resource management, ISO storage

### 🛡️ **SIEM VM** 
- Ubuntu VM created on Proxmox (will get IP like 192.168.1.100)
- Used for: Running SIEM services, Docker containers

---

## 📋 **Step-by-Step Node Actions**

### **Phase 1: Preparation**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 1 | 🖥️ CLIENT | Download repo | `git clone https://github.com/ativoj/AfCyberSiem-platform.git` |
| 2 | 🖥️ CLIENT | Access Proxmox | Browser → `https://172.16.0.43:8006` |
| 3 | 🏢 PROXMOX | Download ISO | Web interface → Download Ubuntu 22.04 ISO |
| 4 | 🏢 PROXMOX | Create VM | Web interface → Create VM (32 vCPU, 64GB RAM, 1TB) |

### **Phase 2: OS Installation**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 5 | 🏢 PROXMOX | Start VM | Web interface → Start VM → Console |
| 6 | 🛡️ SIEM VM | Install Ubuntu | Console → Follow Ubuntu installation wizard |
| 7 | 🛡️ SIEM VM | Initial setup | `sudo apt update && sudo apt upgrade -y` |
| 8 | 🛡️ SIEM VM | Get IP address | `ip addr show` (note the IP) |

### **Phase 3: SSH Connection**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 9 | 🖥️ CLIENT | SSH to SIEM VM | `ssh ubuntu@<SIEM_VM_IP>` |
| 10 | 🛡️ SIEM VM | Clone repo | `git clone https://github.com/ativoj/AfCyberSiem-platform.git` |

### **Phase 4: Docker Installation**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 11 | 🛡️ SIEM VM | Install Docker | `curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh` |
| 12 | 🛡️ SIEM VM | Add user to docker | `sudo usermod -aG docker ubuntu` |
| 13 | 🛡️ SIEM VM | Install Compose | `sudo curl -L "..." -o /usr/local/bin/docker-compose` |
| 14 | 🖥️ CLIENT | Reconnect SSH | `ssh ubuntu@<SIEM_VM_IP>` (after logout/login) |

### **Phase 5: SIEM Deployment**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 15 | 🛡️ SIEM VM | Navigate to Docker dir | `cd ~/AfCyberSiem-platform/04_Docker_Helm_Packaging/` |
| 16 | 🛡️ SIEM VM | Create .env file | `cat > .env << 'EOF'` (with configuration) |
| 17 | 🛡️ SIEM VM | Pull images | `docker-compose pull` |
| 18 | 🛡️ SIEM VM | Start services | `docker-compose up -d` |
| 19 | 🛡️ SIEM VM | Check status | `docker-compose ps` |

### **Phase 6: Security & Access**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 20 | 🛡️ SIEM VM | Configure firewall | `sudo ufw allow 22,443,3000,9000,9001,8080` |
| 21 | 🛡️ SIEM VM | Enable firewall | `sudo ufw --force enable` |
| 22 | 🖥️ CLIENT | Access Wazuh | Browser → `https://<SIEM_VM_IP>:443` |
| 23 | 🖥️ CLIENT | Access Grafana | Browser → `http://<SIEM_VM_IP>:3000` |
| 24 | 🖥️ CLIENT | Access Graylog | Browser → `http://<SIEM_VM_IP>:9000` |

### **Phase 7: Monitoring Setup**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 25 | 🛡️ SIEM VM | Create monitor script | `cat > ~/monitor_siem.sh << 'EOF'` |
| 26 | 🛡️ SIEM VM | Create backup script | `cat > ~/backup_siem.sh << 'EOF'` |
| 27 | 🛡️ SIEM VM | Test monitoring | `./monitor_siem.sh` |

### **Phase 8: Agent Installation (Optional)**

| Step | Node | Action | Command/Description |
|------|------|--------|-------------------|
| 28 | 🖥️ OTHER LINUX | Install Wazuh agent | `sudo apt install wazuh-agent` |
| 29 | 🖥️ OTHER LINUX | Configure agent | `sudo sed -i "s/MANAGER_IP/<SIEM_VM_IP>/" /var/ossec/etc/ossec.conf` |
| 30 | 💻 WINDOWS | Install agent | Download MSI and install with SIEM VM IP |

---

## 🚨 **Critical Node Warnings**

### ⚠️ **DO NOT confuse these nodes:**
- **DON'T** run Docker commands on your CLIENT MACHINE
- **DON'T** try to access web interfaces from SIEM VM console
- **DON'T** install SIEM services on PROXMOX HOST directly

### ✅ **Remember:**
- **CLIENT MACHINE**: For downloading, browsing, SSH connections
- **PROXMOX HOST**: For VM management only
- **SIEM VM**: For all SIEM installation and configuration

---

## 🔍 **Quick Troubleshooting by Node**

### 🖥️ **CLIENT MACHINE Issues:**
- Can't access Proxmox web interface → Check network connectivity
- Can't SSH to SIEM VM → Check VM IP address and firewall
- Can't access SIEM web interfaces → Check SIEM VM firewall and services

### 🏢 **PROXMOX HOST Issues:**
- Can't create VM → Check available resources
- VM won't start → Check storage and memory allocation
- Console not working → Try different browser or VNC viewer

### 🛡️ **SIEM VM Issues:**
- Docker commands fail → Check if user is in docker group
- Services won't start → Check system resources and logs
- Web interfaces not accessible → Check firewall and service status

---

**💡 Pro Tip: Always verify which node you're working on by checking the command prompt:**
- CLIENT: `user@client-machine:~$`
- SIEM VM: `ubuntu@siem-platform:~$`
- PROXMOX: `root@proxmox-host:~#`

