# SIEM Platform Multi-Tenant Deployment Script
# This script deploys a multi-tenant SIEM platform across multiple Proxmox VMs

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "config\multi-tenant-config.json",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipPrerequisites,
    
    [Parameter(Mandatory=$false)]
    [switch]$DestroyExisting,
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf,
    
    [Parameter(Mandatory=$false)]
    [int]$TenantCount = 5
)

# Import common module
Import-Module "$PSScriptRoot\..\common\SIEMDeployment.psm1" -Force

# Main deployment function
function Deploy-MultiTenantSIEM {
    param(
        [string]$ConfigPath,
        [int]$Tenants
    )
    
    try {
        Write-SIEMLog "=== SIEM Platform Multi-Tenant Deployment ===" -Level "INFO"
        Write-SIEMLog "Starting deployment for $Tenants tenants..." -Level "INFO"
        
        # Initialize deployment
        Initialize-SIEMDeployment -ConfigFile $ConfigPath
        
        # Check prerequisites
        if (!$SkipPrerequisites) {
            Test-Prerequisites
            Install-RequiredModules
        }
        
        # Test Proxmox connection
        if (!(Test-ProxmoxConnection)) {
            throw "Cannot connect to Proxmox server"
        }
        
        # Load configuration
        $config = Get-Content $ConfigPath | ConvertFrom-Json
        
        # Destroy existing deployment if requested
        if ($DestroyExisting) {
            Write-SIEMLog "Destroying existing deployment..." -Level "WARN"
            Invoke-TerraformDestroy -TerraformDir "..\terraform"
        }
        
        # Prepare Terraform variables
        $terraformVars = @{
            "proxmox_api_url" = $config.proxmox.api_url
            "proxmox_user" = $config.proxmox.username
            "proxmox_password" = $config.proxmox.password
            "proxmox_node" = $config.proxmox.node
            "deployment_mode" = "multi-tenant"
            "environment" = $config.deployment.environment
            "ssh_public_key" = $config.deployment.ssh_public_key
            "tenant_count" = $Tenants
            "node_count" = $config.cluster.node_count
            "ceph_pool" = $config.proxmox.ceph_pool
            "network_bridge" = $config.proxmox.network_bridge
            "enable_ha" = $config.features.enable_ha
        }
        
        if ($WhatIf) {
            Write-SIEMLog "WhatIf mode - would deploy with the following configuration:" -Level "INFO"
            $terraformVars | ConvertTo-Json -Depth 3 | Write-Host
            return
        }
        
        # Deploy infrastructure with Terraform
        Write-SIEMLog "Deploying multi-tenant infrastructure..." -Level "INFO"
        $terraformOutputs = Invoke-TerraformDeployment -TerraformDir "..\terraform" -Variables $terraformVars
        
        # Extract deployment information
        $multiTenantInfo = $terraformOutputs.multi_tenant_info.value
        $loadBalancerIP = $multiTenantInfo.load_balancer.ssh_host
        
        Write-SIEMLog "Infrastructure deployed successfully. Load Balancer IP: $loadBalancerIP" -Level "SUCCESS"
        
        # Generate Ansible inventory for multi-tenant deployment
        $inventoryContent = Generate-MultiTenantInventory -DeploymentInfo $multiTenantInfo -Config $config
        
        $inventoryPath = "inventory\multi-tenant-hosts"
        $inventoryContent | Out-File -FilePath $inventoryPath -Encoding UTF8
        
        # Wait for all VMs to be ready
        Write-SIEMLog "Waiting for all VMs to be ready..." -Level "INFO"
        Wait-ForMultiTenantVMs -DeploymentInfo $multiTenantInfo
        
        # Deploy each tenant
        for ($i = 1; $i -le $Tenants; $i++) {
            Write-SIEMLog "Deploying tenant $i..." -Level "INFO"
            Deploy-Tenant -TenantId $i -Config $config -InventoryPath $inventoryPath
        }
        
        # Configure load balancer
        Write-SIEMLog "Configuring load balancer..." -Level "INFO"
        Configure-LoadBalancer -LoadBalancerIP $loadBalancerIP -Config $config -TenantCount $Tenants
        
        # Configure monitoring and alerting
        if ($config.features.enable_monitoring) {
            Write-SIEMLog "Setting up monitoring..." -Level "INFO"
            Setup-Monitoring -Config $config -DeploymentInfo $multiTenantInfo
        }
        
        # Generate tenant access information
        $accessInfo = Generate-TenantAccessInfo -DeploymentInfo $multiTenantInfo -Config $config -TenantCount $Tenants
        
        Write-SIEMLog $accessInfo -Level "INFO"
        
        # Save access information to file
        $accessInfo | Out-File -FilePath "multi-tenant-access-info.txt" -Encoding UTF8
        
        # Display deployment summary
        Get-DeploymentSummary
        
        Write-SIEMLog "Multi-tenant SIEM deployment completed successfully!" -Level "SUCCESS"
        
    } catch {
        Write-SIEMLog "Deployment failed: $($_.Exception.Message)" -Level "ERROR"
        Write-SIEMLog "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
        throw
    }
}

function Generate-MultiTenantInventory {
    param(
        [object]$DeploymentInfo,
        [object]$Config
    )
    
    $inventory = @"
[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=$($Config.deployment.ssh_private_key)
ansible_ssh_common_args='-o StrictHostKeyChecking=no'

"@
    
    # Add Wazuh managers
    $inventory += "[wazuh_managers]`n"
    foreach ($manager in $DeploymentInfo.wazuh_managers) {
        $inventory += "wazuh-manager-tenant-$($manager.tenant) ansible_host=$($manager.ip) tenant_id=$($manager.tenant)`n"
    }
    $inventory += "`n"
    
    # Add Wazuh indexers
    $inventory += "[wazuh_indexers]`n"
    foreach ($indexer in $DeploymentInfo.wazuh_indexers) {
        $inventory += "wazuh-indexer-tenant-$($indexer.tenant) ansible_host=$($indexer.ip) tenant_id=$($indexer.tenant)`n"
    }
    $inventory += "`n"
    
    # Add Graylog servers
    $inventory += "[graylog_servers]`n"
    foreach ($graylog in $DeploymentInfo.graylogs) {
        $inventory += "graylog-tenant-$($graylog.tenant) ansible_host=$($graylog.ip) tenant_id=$($graylog.tenant)`n"
    }
    $inventory += "`n"
    
    # Add load balancer
    $inventory += "[load_balancers]`n"
    $inventory += "siem-load-balancer ansible_host=$($DeploymentInfo.load_balancer.ssh_host)`n"
    $inventory += "`n"
    
    # Add logical groupings
    $inventory += @"
[wazuh:children]
wazuh_managers
wazuh_indexers

[log_management:children]
graylog_servers

[multi_tenant:children]
wazuh
log_management

[siem_platform:children]
multi_tenant
load_balancers
"@
    
    return $inventory
}

function Wait-ForMultiTenantVMs {
    param(
        [object]$DeploymentInfo
    )
    
    $allIPs = @()
    
    # Collect all IP addresses
    foreach ($manager in $DeploymentInfo.wazuh_managers) {
        $allIPs += $manager.ip
    }
    foreach ($indexer in $DeploymentInfo.wazuh_indexers) {
        $allIPs += $indexer.ip
    }
    foreach ($graylog in $DeploymentInfo.graylogs) {
        $allIPs += $graylog.ip
    }
    $allIPs += $DeploymentInfo.load_balancer.ssh_host
    
    # Wait for all VMs to be ready
    foreach ($ip in $allIPs) {
        Write-SIEMLog "Waiting for VM at $ip to be ready..." -Level "INFO"
        if (!(Wait-ForSSH -IPAddress $ip -TimeoutSeconds 300)) {
            throw "VM at $ip failed to become ready"
        }
    }
    
    Write-SIEMLog "All VMs are ready" -Level "SUCCESS"
}

function Deploy-Tenant {
    param(
        [int]$TenantId,
        [object]$Config,
        [string]$InventoryPath
    )
    
    # Prepare tenant-specific variables
    $tenantVars = @{
        "tenant_id" = $TenantId
        "deployment_mode" = "multi-tenant"
        "environment" = $Config.deployment.environment
        "wazuh_admin_password" = "$($Config.passwords.wazuh_admin)_tenant$TenantId"
        "graylog_admin_password" = "$($Config.passwords.graylog_admin)_tenant$TenantId"
        "grafana_admin_password" = "$($Config.passwords.grafana_admin)_tenant$TenantId"
        "thehive_admin_password" = "$($Config.passwords.thehive_admin)_tenant$TenantId"
    }
    
    # Deploy Wazuh components for this tenant
    Invoke-AnsiblePlaybook -PlaybookPath "..\ansible\playbooks\wazuh-manager.yml" -InventoryPath $InventoryPath -ExtraVars $tenantVars
    Invoke-AnsiblePlaybook -PlaybookPath "..\ansible\playbooks\wazuh-indexer.yml" -InventoryPath $InventoryPath -ExtraVars $tenantVars
    
    # Deploy Graylog for this tenant
    Invoke-AnsiblePlaybook -PlaybookPath "..\ansible\playbooks\graylog.yml" -InventoryPath $InventoryPath -ExtraVars $tenantVars
    
    # Deploy other components as needed
    # Invoke-AnsiblePlaybook -PlaybookPath "..\ansible\playbooks\thehive.yml" -InventoryPath $InventoryPath -ExtraVars $tenantVars
    
    Write-SIEMLog "Tenant $TenantId deployed successfully" -Level "SUCCESS"
}

function Configure-LoadBalancer {
    param(
        [string]$LoadBalancerIP,
        [object]$Config,
        [int]$TenantCount
    )
    
    # Configure HAProxy or Nginx for load balancing
    $lbVars = @{
        "tenant_count" = $TenantCount
        "ssl_enabled" = $Config.security.ssl_enabled
        "certificate_path" = $Config.security.certificate_path
    }
    
    Invoke-AnsiblePlaybook -PlaybookPath "..\ansible\playbooks\load-balancer.yml" -InventoryPath "inventory\multi-tenant-hosts" -ExtraVars $lbVars
    
    Write-SIEMLog "Load balancer configured successfully" -Level "SUCCESS"
}

function Setup-Monitoring {
    param(
        [object]$Config,
        [object]$DeploymentInfo
    )
    
    # Deploy monitoring stack (Prometheus, Grafana, etc.)
    $monitoringVars = @{
        "enable_monitoring" = $true
        "retention_days" = $Config.features.log_retention_days
    }
    
    Invoke-AnsiblePlaybook -PlaybookPath "..\ansible\playbooks\monitoring.yml" -InventoryPath "inventory\multi-tenant-hosts" -ExtraVars $monitoringVars
    
    Write-SIEMLog "Monitoring configured successfully" -Level "SUCCESS"
}

function Generate-TenantAccessInfo {
    param(
        [object]$DeploymentInfo,
        [object]$Config,
        [int]$TenantCount
    )
    
    $accessInfo = @"
=== SIEM Platform Multi-Tenant Access Information ===

Load Balancer: $($DeploymentInfo.load_balancer.ssh_host)

Tenant Access URLs:
"@
    
    for ($i = 1; $i -le $TenantCount; $i++) {
        $accessInfo += @"

Tenant $i:
- Wazuh Dashboard: https://$($DeploymentInfo.load_balancer.ssh_host)/tenant$i/wazuh
- Graylog: https://$($DeploymentInfo.load_balancer.ssh_host)/tenant$i/graylog
- Grafana: https://$($DeploymentInfo.load_balancer.ssh_host)/tenant$i/grafana
- TheHive: https://$($DeploymentInfo.load_balancer.ssh_host)/tenant$i/thehive

Credentials:
- Wazuh: admin / $($Config.passwords.wazuh_admin)_tenant$i
- Graylog: admin / $($Config.passwords.graylog_admin)_tenant$i
- Grafana: admin / $($Config.passwords.grafana_admin)_tenant$i
- TheHive: admin@thehive.local / $($Config.passwords.thehive_admin)_tenant$i
"@
    }
    
    $accessInfo += @"

=== Management Access ===
- SSH to Load Balancer: ssh ubuntu@$($DeploymentInfo.load_balancer.ssh_host) -i $($Config.deployment.ssh_private_key)
- Proxmox Web UI: $($Config.proxmox.api_url)

=== Important Notes ===
1. Each tenant is completely isolated with dedicated resources
2. Change default passwords immediately after first login
3. Configure SSL certificates for production use
4. Set up regular backups for each tenant
5. Review firewall rules and network access policies
6. Monitor resource usage and scale as needed
"@
    
    return $accessInfo
}

function Wait-ForSSH {
    param(
        [string]$IPAddress,
        [int]$TimeoutSeconds = 300
    )
    
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    
    while ((Get-Date) -lt $timeout) {
        try {
            $testConnection = Test-NetConnection -ComputerName $IPAddress -Port 22 -InformationLevel Quiet
            if ($testConnection) {
                return $true
            }
        } catch {
            # Continue waiting
        }
        
        Start-Sleep -Seconds 10
    }
    
    return $false
}

function Invoke-TerraformDestroy {
    param(
        [string]$TerraformDir
    )
    
    Push-Location $TerraformDir
    
    try {
        $destroyResult = terraform destroy -auto-approve
        if ($LASTEXITCODE -ne 0) {
            throw "Terraform destroy failed"
        }
        
        Write-SIEMLog "Existing infrastructure destroyed" -Level "SUCCESS"
        
    } catch {
        Write-SIEMLog "Failed to destroy infrastructure: $($_.Exception.Message)" -Level "ERROR"
        throw
    } finally {
        Pop-Location
    }
}

# Main execution
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Deploy-MultiTenantSIEM -ConfigPath $ConfigFile -Tenants $TenantCount
    } catch {
        Write-Host "Deployment failed. Check the log file for details." -ForegroundColor Red
        exit 1
    }
}

