# AfCyber SIEM Template Creation - Automation Guide

## 🎯 **Overview**

This guide provides automated solutions for creating an Ubuntu 24.04.2 template optimized for AfCyber SIEM deployment on your Proxmox server at 172.16.0.43:8006.

## 🚀 **Automation Options**

### **Option 1: Bash Script Automation (Recommended)**
Semi-automated approach with manual Ubuntu installation step.

### **Option 2: Terraform Automation (Advanced)**
Fully automated approach using Infrastructure as Code.

---

## 🔧 **Option 1: Bash Script Automation**

### **Features:**
- ✅ Automated ISO download
- ✅ Automated VM creation with exact specifications
- ✅ Guided Ubuntu installation process
- ✅ Automated template conversion
- ✅ Cloud-init configuration

### **Usage:**
```bash
# Download and run the script
wget https://raw.githubusercontent.com/ativoj/AfCyberSiem-platform/main/create_afcyber_siem_template.sh
chmod +x create_afcyber_siem_template.sh
./create_afcyber_siem_template.sh
```

### **What It Does:**
1. **Downloads Ubuntu 24.04.2 ISO** to Proxmox storage
2. **Creates VM** with exact specifications:
   - VM ID: 9000
   - Name: ubuntu-24.04.2-afcyber-template
   - CPU: 2 cores
   - Memory: 4096 MB
   - Disk: 32 GB
   - Network: VirtIO on vmbr0
3. **Starts VM** for manual Ubuntu installation
4. **Waits** for installation completion
5. **Configures** cloud-init settings
6. **Converts** VM to template

### **Manual Steps Required:**
- Ubuntu installation (guided by script)
- Basic system configuration

---

## 🏗️ **Option 2: Terraform Automation**

### **Features:**
- ✅ Fully automated Infrastructure as Code
- ✅ Version controlled configuration
- ✅ Repeatable deployments
- ✅ Cloud-init integration
- ✅ Complete hands-off operation

### **Prerequisites:**
```bash
# Install Terraform (script will do this automatically)
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform
```

### **Usage:**
```bash
# Download Terraform configuration
wget https://raw.githubusercontent.com/ativoj/AfCyberSiem-platform/main/afcyber_siem_template.tf
wget https://raw.githubusercontent.com/ativoj/AfCyberSiem-platform/main/afcyber_siem_template.tfvars.example
wget https://raw.githubusercontent.com/ativoj/AfCyberSiem-platform/main/terraform_create_afcyber_template.sh

# Run automated Terraform deployment
chmod +x terraform_create_afcyber_template.sh
./terraform_create_afcyber_template.sh
```

### **Configuration:**
Edit `afcyber_siem_template.tfvars`:
```hcl
proxmox_api_url = "https://172.16.0.43:8006/api2/json"
proxmox_api_token_id = "your-token-id"
proxmox_api_token_secret = "your-token-secret"
proxmox_node = "your-node-name"
```

---

## 📋 **Template Specifications**

### **VM Configuration:**
| Setting | Value |
|---------|-------|
| **VM ID** | 9000 |
| **Name** | ubuntu-24.04.2-afcyber-template |
| **OS** | Ubuntu 24.04.2 LTS |
| **Machine Type** | q35 |
| **BIOS** | OVMF (UEFI) |
| **CPU** | 2 cores, host type |
| **Memory** | 4096 MB |
| **Disk** | 32 GB, SCSI, local-lvm |
| **Network** | VirtIO, bridge vmbr0 |
| **Agent** | QEMU Guest Agent enabled |

### **Software Included:**
- ✅ Ubuntu 24.04.2 LTS (minimal installation)
- ✅ QEMU Guest Agent
- ✅ Cloud-init
- ✅ OpenSSH Server
- ✅ Essential system tools (curl, wget, git, vim, htop)

### **User Configuration:**
- **Username**: ubuntu
- **Password**: ubuntu (change after cloning)
- **SSH**: Enabled
- **Sudo**: Passwordless sudo access

---

## 🔑 **Proxmox API Token Setup**

### **Create API Token:**
1. Access Proxmox web interface: `https://172.16.0.43:8006`
2. Go to **Datacenter** → **Permissions** → **API Tokens**
3. Click **"Add"**
4. Configure:
   - **User**: root@pam
   - **Token ID**: afcyber-template
   - **Privilege Separation**: Unchecked
5. **Copy** the Token ID and Secret

### **Required Permissions:**
- VM.Allocate
- VM.Clone
- VM.Config.CDROM
- VM.Config.CPU
- VM.Config.Disk
- VM.Config.HWType
- VM.Config.Memory
- VM.Config.Network
- VM.Config.Options
- VM.Monitor
- VM.PowerMgmt
- Datastore.AllocateSpace
- Datastore.AllocateTemplate

---

## 🎯 **Template Usage After Creation**

### **Clone Template for AfCyber SIEM:**

#### **Via Proxmox Web Interface:**
1. Right-click template → **"Clone"**
2. Configure production settings:
   - **VM ID**: 100
   - **Name**: afcyber-siem-platform
   - **CPU**: 32 cores
   - **Memory**: 65536 MB (64GB)
   - **Disk**: Resize to 1000 GB

#### **Via Terraform:**
```hcl
resource "proxmox_vm_qemu" "afcyber_siem" {
  name        = "afcyber-siem-platform"
  vmid        = 100
  target_node = var.proxmox_node
  clone       = "ubuntu-24.04.2-afcyber-template"
  
  cores   = 32
  memory  = 65536
  
  disk {
    slot    = 0
    size    = "1000G"
    type    = "scsi"
    storage = "local-lvm"
  }
}
```

#### **Via API:**
```bash
curl -k -X POST \
  -H "Authorization: PVEAPIToken=${TOKEN_ID}=${TOKEN_SECRET}" \
  -d "newid=100" \
  -d "name=afcyber-siem-platform" \
  "https://172.16.0.43:8006/api2/json/nodes/${NODE}/qemu/9000/clone"
```

---

## 🔍 **Verification Steps**

### **After Template Creation:**
```bash
# Check template exists
curl -k -H "Authorization: PVEAPIToken=${TOKEN_ID}=${TOKEN_SECRET}" \
  "https://172.16.0.43:8006/api2/json/nodes/${NODE}/qemu/9000/config"

# Verify template status
curl -k -H "Authorization: PVEAPIToken=${TOKEN_ID}=${TOKEN_SECRET}" \
  "https://172.16.0.43:8006/api2/json/nodes/${NODE}/qemu/9000/status/current"
```

### **Template Should Show:**
- ✅ Status: Template
- ✅ OS: Ubuntu 24.04.2
- ✅ CPU: 2 cores
- ✅ Memory: 4096 MB
- ✅ Disk: 32 GB
- ✅ Network: VirtIO

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **ISO Download Fails:**
```bash
# Manual ISO download
cd /var/lib/vz/template/iso/
wget https://releases.ubuntu.com/24.04.2/ubuntu-24.04.2-live-server-amd64.iso
```

#### **API Authentication Fails:**
- Verify token ID and secret
- Check token permissions
- Ensure token is not expired

#### **VM Creation Fails:**
- Check available resources
- Verify storage exists
- Confirm network bridge exists

#### **Template Conversion Fails:**
- Ensure VM is stopped
- Check VM is not running
- Verify sufficient permissions

---

## 📈 **Performance Optimization**

### **Template Best Practices:**
- ✅ Minimal package installation
- ✅ Cloud-init ready
- ✅ QEMU Guest Agent enabled
- ✅ Optimized for quick cloning
- ✅ Standard user configuration

### **Clone Optimization:**
- Use linked clones for faster deployment
- Resize disks after cloning
- Configure cloud-init for automated setup
- Use templates for consistent deployments

---

## 🎉 **Success Indicators**

### **Template Creation Complete When:**
- ✅ VM ID 9000 shows as "Template" in Proxmox
- ✅ Ubuntu 24.04.2 fully installed and configured
- ✅ QEMU Guest Agent running
- ✅ Cloud-init configured
- ✅ SSH access enabled
- ✅ Ready for cloning

### **Ready for AfCyber SIEM Deployment:**
- ✅ Template can be cloned successfully
- ✅ Cloned VMs boot properly
- ✅ Network connectivity works
- ✅ SSH access functional
- ✅ System resources adequate

---

**🎯 Your AfCyber SIEM template will be ready for rapid deployment of security monitoring infrastructure!**

