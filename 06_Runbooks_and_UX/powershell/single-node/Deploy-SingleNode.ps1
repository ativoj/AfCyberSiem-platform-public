# SIEM Platform Single-Node Deployment Script
# This script deploys a complete SIEM platform on a single Proxmox VM

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "config\single-node-config.json",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipPrerequisites,
    
    [Parameter(Mandatory=$false)]
    [switch]$DestroyExisting,
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf
)

# Import common module
Import-Module "$PSScriptRoot\..\common\SIEMDeployment.psm1" -Force

# Main deployment function
function Deploy-SingleNodeSIEM {
    param(
        [string]$ConfigPath
    )
    
    try {
        Write-SIEMLog "=== SIEM Platform Single-Node Deployment ===" -Level "INFO"
        Write-SIEMLog "Starting deployment process..." -Level "INFO"
        
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
            "deployment_mode" = "single-node"
            "environment" = $config.deployment.environment
            "ssh_public_key" = $config.deployment.ssh_public_key
            "single_node_resources" = @{
                cores = $config.resources.cores
                memory = $config.resources.memory
                disk = $config.resources.disk
            }
            "storage_pool" = $config.proxmox.storage_pool
            "network_bridge" = $config.proxmox.network_bridge
        }
        
        if ($WhatIf) {
            Write-SIEMLog "WhatIf mode - would deploy with the following configuration:" -Level "INFO"
            $terraformVars | ConvertTo-Json -Depth 3 | Write-Host
            return
        }
        
        # Deploy infrastructure with Terraform
        Write-SIEMLog "Deploying infrastructure..." -Level "INFO"
        $terraformOutputs = Invoke-TerraformDeployment -TerraformDir "..\terraform" -Variables $terraformVars
        
        # Extract VM information
        $vmInfo = $terraformOutputs.single_node_info.value
        $vmIP = $vmInfo.ssh_host
        
        Write-SIEMLog "VM deployed successfully. IP: $vmIP" -Level "SUCCESS"
        
        # Wait for VM to be ready
        Write-SIEMLog "Waiting for VM to be ready..." -Level "INFO"
        Wait-ForSSH -IPAddress $vmIP -TimeoutSeconds 300
        
        # Generate Ansible inventory
        $inventoryContent = @"
[siem_single_node]
siem-single-node ansible_host=$vmIP

[siem_single_node:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=$($config.deployment.ssh_private_key)
ansible_ssh_common_args='-o StrictHostKeyChecking=no'

[siem_platform:children]
siem_single_node
"@
        
        $inventoryPath = "inventory\single-node-hosts"
        $inventoryContent | Out-File -FilePath $inventoryPath -Encoding UTF8
        
        # Prepare Ansible variables
        $ansibleVars = @{
            "deployment_mode" = "single-node"
            "environment" = $config.deployment.environment
            "wazuh_admin_password" = $config.passwords.wazuh_admin
            "graylog_admin_password" = $config.passwords.graylog_admin
            "grafana_admin_password" = $config.passwords.grafana_admin
            "thehive_admin_password" = $config.passwords.thehive_admin
        }
        
        # Run Ansible playbooks
        Write-SIEMLog "Configuring SIEM components..." -Level "INFO"
        
        # Deploy single-node configuration
        Invoke-AnsiblePlaybook -PlaybookPath "..\ansible\playbooks\single-node-deploy.yml" -InventoryPath $inventoryPath -ExtraVars $ansibleVars
        
        # Wait for services to be ready
        Write-SIEMLog "Waiting for services to start..." -Level "INFO"
        
        $services = @(
            @{ Name = "Wazuh Dashboard"; Url = "https://$vmIP" },
            @{ Name = "Graylog"; Url = "http://$vmIP:9000" },
            @{ Name = "Grafana"; Url = "http://$vmIP:3000" },
            @{ Name = "TheHive"; Url = "http://$vmIP:9000" }
        )
        
        foreach ($service in $services) {
            if (Wait-ForService -ServiceUrl $service.Url -TimeoutSeconds 180) {
                Write-SIEMLog "$($service.Name) is ready at $($service.Url)" -Level "SUCCESS"
            } else {
                Write-SIEMLog "$($service.Name) failed to start at $($service.Url)" -Level "WARN"
            }
        }
        
        # Generate access information
        $accessInfo = @"
=== SIEM Platform Access Information ===

VM Information:
- IP Address: $vmIP
- SSH Access: ssh ubuntu@$vmIP -i $($config.deployment.ssh_private_key)

Service URLs:
- Wazuh Dashboard: https://$vmIP
- Graylog: http://$vmIP:9000
- Grafana: http://$vmIP:3000
- TheHive: http://$vmIP:9000

Default Credentials:
- Wazuh: admin / $($config.passwords.wazuh_admin)
- Graylog: admin / $($config.passwords.graylog_admin)
- Grafana: admin / $($config.passwords.grafana_admin)
- TheHive: admin@thehive.local / $($config.passwords.thehive_admin)

=== Important Notes ===
1. Change default passwords immediately after first login
2. Configure SSL certificates for production use
3. Set up regular backups
4. Review firewall rules and network access
"@
        
        Write-SIEMLog $accessInfo -Level "INFO"
        
        # Save access information to file
        $accessInfo | Out-File -FilePath "single-node-access-info.txt" -Encoding UTF8
        
        # Display deployment summary
        Get-DeploymentSummary
        
        Write-SIEMLog "Single-node SIEM deployment completed successfully!" -Level "SUCCESS"
        
    } catch {
        Write-SIEMLog "Deployment failed: $($_.Exception.Message)" -Level "ERROR"
        Write-SIEMLog "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
        throw
    }
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
        Deploy-SingleNodeSIEM -ConfigPath $ConfigFile
    } catch {
        Write-Host "Deployment failed. Check the log file for details." -ForegroundColor Red
        exit 1
    }
}

