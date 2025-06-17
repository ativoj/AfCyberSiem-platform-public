# SIEM Platform PowerShell Deployment Package
# Main deployment orchestrator script

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("single-node", "multi-tenant")]
    [string]$DeploymentMode,
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile,
    
    [Parameter(Mandatory=$false)]
    [int]$TenantCount = 5,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipPrerequisites,
    
    [Parameter(Mandatory=$false)]
    [switch]$DestroyExisting,
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

# Display help information
if ($Help) {
    $helpText = @"
SIEM Platform PowerShell Deployment Package
===========================================

This script deploys a complete open-source SIEM platform on Proxmox infrastructure.

USAGE:
    .\Deploy-SIEM.ps1 -DeploymentMode <mode> [options]

PARAMETERS:
    -DeploymentMode     Required. Deployment mode: 'single-node' or 'multi-tenant'
    -ConfigFile         Optional. Path to configuration file
    -TenantCount        Optional. Number of tenants for multi-tenant deployment (default: 5)
    -SkipPrerequisites  Optional. Skip prerequisite checks
    -DestroyExisting    Optional. Destroy existing deployment before creating new one
    -WhatIf             Optional. Show what would be deployed without actually deploying
    -Help               Optional. Show this help message

EXAMPLES:
    # Deploy single-node SIEM
    .\Deploy-SIEM.ps1 -DeploymentMode single-node

    # Deploy multi-tenant SIEM with 10 tenants
    .\Deploy-SIEM.ps1 -DeploymentMode multi-tenant -TenantCount 10

    # Preview multi-tenant deployment
    .\Deploy-SIEM.ps1 -DeploymentMode multi-tenant -WhatIf

    # Destroy and redeploy single-node
    .\Deploy-SIEM.ps1 -DeploymentMode single-node -DestroyExisting

CONFIGURATION:
    Configuration files are located in:
    - single-node\config\single-node-config.json
    - multi-tenant\config\multi-tenant-config.json

    Edit these files to customize your deployment settings.

REQUIREMENTS:
    - PowerShell 5.0 or higher
    - Terraform installed and in PATH
    - Ansible installed and in PATH
    - SSH key pair for VM access
    - Proxmox VE cluster with API access

SUPPORT:
    For documentation and support, visit:
    https://github.com/siem-platform/docs
"@
    
    Write-Host $helpText
    exit 0
}

# Set default config file if not provided
if (!$ConfigFile) {
    switch ($DeploymentMode) {
        "single-node" { $ConfigFile = "single-node\config\single-node-config.json" }
        "multi-tenant" { $ConfigFile = "multi-tenant\config\multi-tenant-config.json" }
    }
}

# Validate config file exists
if (!(Test-Path $ConfigFile)) {
    Write-Host "Configuration file not found: $ConfigFile" -ForegroundColor Red
    Write-Host "Please create the configuration file or specify a different path." -ForegroundColor Red
    exit 1
}

# Display deployment banner
$banner = @"
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SIEM Platform Deployment Package                         ║
║                                                                              ║
║  World's Best Open-Source SIEM Platform                                     ║
║  Powered by: Wazuh, Graylog, TheHive, OpenCTI, MISP, Velociraptor          ║
║  Infrastructure: Proxmox SDDC with Terraform & Ansible                      ║
║                                                                              ║
║  Mode: $($DeploymentMode.PadRight(66)) ║
║  Config: $($ConfigFile.PadRight(64)) ║
╚══════════════════════════════════════════════════════════════════════════════╝
"@

Write-Host $banner -ForegroundColor Cyan

# Execute deployment based on mode
try {
    switch ($DeploymentMode) {
        "single-node" {
            Write-Host "Starting single-node deployment..." -ForegroundColor Green
            
            $scriptPath = "$PSScriptRoot\single-node\Deploy-SingleNode.ps1"
            $arguments = @(
                "-ConfigFile", $ConfigFile
            )
            
            if ($SkipPrerequisites) { $arguments += "-SkipPrerequisites" }
            if ($DestroyExisting) { $arguments += "-DestroyExisting" }
            if ($WhatIf) { $arguments += "-WhatIf" }
            
            & $scriptPath @arguments
        }
        
        "multi-tenant" {
            Write-Host "Starting multi-tenant deployment..." -ForegroundColor Green
            
            $scriptPath = "$PSScriptRoot\multi-tenant\Deploy-MultiTenant.ps1"
            $arguments = @(
                "-ConfigFile", $ConfigFile,
                "-TenantCount", $TenantCount
            )
            
            if ($SkipPrerequisites) { $arguments += "-SkipPrerequisites" }
            if ($DestroyExisting) { $arguments += "-DestroyExisting" }
            if ($WhatIf) { $arguments += "-WhatIf" }
            
            & $scriptPath @arguments
        }
    }
    
    Write-Host "`nDeployment completed successfully!" -ForegroundColor Green
    Write-Host "Check the generated access information files for login details." -ForegroundColor Yellow
    
} catch {
    Write-Host "`nDeployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check the log files for detailed error information." -ForegroundColor Yellow
    exit 1
}

