# SIEM Platform PowerShell Deployment Module
# Common functions and utilities for SIEM platform deployment

# Global Variables
$Global:SIEMConfig = @{
    ProxmoxAPI = ""
    ProxmoxUser = ""
    ProxmoxPassword = ""
    ProxmoxNode = ""
    DeploymentMode = ""
    Environment = ""
    LogFile = ""
    StartTime = Get-Date
}

# Logging Functions
function Write-SIEMLog {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("INFO", "WARN", "ERROR", "SUCCESS")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Color coding for console output
    switch ($Level) {
        "INFO"    { Write-Host $logEntry -ForegroundColor White }
        "WARN"    { Write-Host $logEntry -ForegroundColor Yellow }
        "ERROR"   { Write-Host $logEntry -ForegroundColor Red }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
    }
    
    # Write to log file if specified
    if ($Global:SIEMConfig.LogFile) {
        Add-Content -Path $Global:SIEMConfig.LogFile -Value $logEntry
    }
}

function Initialize-SIEMDeployment {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ConfigFile
    )
    
    Write-SIEMLog "Initializing SIEM Platform deployment..." -Level "INFO"
    
    # Load configuration
    if (Test-Path $ConfigFile) {
        $config = Get-Content $ConfigFile | ConvertFrom-Json
        $Global:SIEMConfig.ProxmoxAPI = $config.proxmox.api_url
        $Global:SIEMConfig.ProxmoxUser = $config.proxmox.username
        $Global:SIEMConfig.ProxmoxPassword = $config.proxmox.password
        $Global:SIEMConfig.ProxmoxNode = $config.proxmox.node
        $Global:SIEMConfig.DeploymentMode = $config.deployment.mode
        $Global:SIEMConfig.Environment = $config.deployment.environment
        
        Write-SIEMLog "Configuration loaded successfully" -Level "SUCCESS"
    } else {
        Write-SIEMLog "Configuration file not found: $ConfigFile" -Level "ERROR"
        throw "Configuration file not found"
    }
    
    # Create log file
    $logDir = "logs"
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $Global:SIEMConfig.LogFile = "$logDir\siem-deployment-$timestamp.log"
    
    Write-SIEMLog "Log file created: $($Global:SIEMConfig.LogFile)" -Level "INFO"
}

function Test-Prerequisites {
    Write-SIEMLog "Checking deployment prerequisites..." -Level "INFO"
    
    $prerequisites = @()
    
    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 5) {
        $prerequisites += "PowerShell 5.0 or higher is required"
    }
    
    # Check required modules
    $requiredModules = @("Posh-SSH", "PowerCLI")
    foreach ($module in $requiredModules) {
        if (!(Get-Module -ListAvailable -Name $module)) {
            $prerequisites += "PowerShell module '$module' is required"
        }
    }
    
    # Check Terraform
    try {
        $terraformVersion = terraform --version 2>$null
        if (!$terraformVersion) {
            $prerequisites += "Terraform is required and must be in PATH"
        }
    } catch {
        $prerequisites += "Terraform is required and must be in PATH"
    }
    
    # Check Ansible
    try {
        $ansibleVersion = ansible --version 2>$null
        if (!$ansibleVersion) {
            $prerequisites += "Ansible is required and must be in PATH"
        }
    } catch {
        $prerequisites += "Ansible is required and must be in PATH"
    }
    
    if ($prerequisites.Count -gt 0) {
        Write-SIEMLog "Prerequisites check failed:" -Level "ERROR"
        foreach ($prereq in $prerequisites) {
            Write-SIEMLog "  - $prereq" -Level "ERROR"
        }
        throw "Prerequisites not met"
    }
    
    Write-SIEMLog "All prerequisites met" -Level "SUCCESS"
}

function Test-ProxmoxConnection {
    Write-SIEMLog "Testing Proxmox connection..." -Level "INFO"
    
    try {
        # Test API connectivity
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $authBody = @{
            username = $Global:SIEMConfig.ProxmoxUser
            password = $Global:SIEMConfig.ProxmoxPassword
        } | ConvertTo-Json
        
        $authResponse = Invoke-RestMethod -Uri "$($Global:SIEMConfig.ProxmoxAPI)/access/ticket" -Method POST -Body $authBody -Headers $headers -SkipCertificateCheck
        
        if ($authResponse.data.ticket) {
            Write-SIEMLog "Proxmox connection successful" -Level "SUCCESS"
            return $true
        } else {
            Write-SIEMLog "Proxmox authentication failed" -Level "ERROR"
            return $false
        }
    } catch {
        Write-SIEMLog "Proxmox connection failed: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Invoke-TerraformDeployment {
    param(
        [Parameter(Mandatory=$true)]
        [string]$TerraformDir,
        
        [Parameter(Mandatory=$false)]
        [hashtable]$Variables = @{}
    )
    
    Write-SIEMLog "Starting Terraform deployment..." -Level "INFO"
    
    Push-Location $TerraformDir
    
    try {
        # Initialize Terraform
        Write-SIEMLog "Initializing Terraform..." -Level "INFO"
        $initResult = terraform init
        if ($LASTEXITCODE -ne 0) {
            throw "Terraform init failed"
        }
        
        # Create terraform.tfvars file
        $tfvarsContent = @()
        foreach ($key in $Variables.Keys) {
            $value = $Variables[$key]
            if ($value -is [string]) {
                $tfvarsContent += "$key = `"$value`""
            } else {
                $tfvarsContent += "$key = $value"
            }
        }
        
        $tfvarsContent | Out-File -FilePath "terraform.tfvars" -Encoding UTF8
        
        # Plan deployment
        Write-SIEMLog "Planning Terraform deployment..." -Level "INFO"
        $planResult = terraform plan -out=tfplan
        if ($LASTEXITCODE -ne 0) {
            throw "Terraform plan failed"
        }
        
        # Apply deployment
        Write-SIEMLog "Applying Terraform deployment..." -Level "INFO"
        $applyResult = terraform apply -auto-approve tfplan
        if ($LASTEXITCODE -ne 0) {
            throw "Terraform apply failed"
        }
        
        # Get outputs
        $outputs = terraform output -json | ConvertFrom-Json
        
        Write-SIEMLog "Terraform deployment completed successfully" -Level "SUCCESS"
        return $outputs
        
    } catch {
        Write-SIEMLog "Terraform deployment failed: $($_.Exception.Message)" -Level "ERROR"
        throw
    } finally {
        Pop-Location
    }
}

function Invoke-AnsiblePlaybook {
    param(
        [Parameter(Mandatory=$true)]
        [string]$PlaybookPath,
        
        [Parameter(Mandatory=$true)]
        [string]$InventoryPath,
        
        [Parameter(Mandatory=$false)]
        [hashtable]$ExtraVars = @{}
    )
    
    Write-SIEMLog "Running Ansible playbook: $PlaybookPath" -Level "INFO"
    
    try {
        # Build ansible-playbook command
        $ansibleCmd = "ansible-playbook"
        $ansibleArgs = @(
            "-i", $InventoryPath,
            $PlaybookPath,
            "-v"
        )
        
        # Add extra variables
        if ($ExtraVars.Count -gt 0) {
            $extraVarsJson = $ExtraVars | ConvertTo-Json -Compress
            $ansibleArgs += "--extra-vars", $extraVarsJson
        }
        
        # Execute playbook
        $process = Start-Process -FilePath $ansibleCmd -ArgumentList $ansibleArgs -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-SIEMLog "Ansible playbook completed successfully" -Level "SUCCESS"
        } else {
            throw "Ansible playbook failed with exit code $($process.ExitCode)"
        }
        
    } catch {
        Write-SIEMLog "Ansible playbook failed: $($_.Exception.Message)" -Level "ERROR"
        throw
    }
}

function Wait-ForService {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ServiceUrl,
        
        [Parameter(Mandatory=$false)]
        [int]$TimeoutSeconds = 300,
        
        [Parameter(Mandatory=$false)]
        [int]$IntervalSeconds = 10
    )
    
    Write-SIEMLog "Waiting for service to be ready: $ServiceUrl" -Level "INFO"
    
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    
    while ((Get-Date) -lt $timeout) {
        try {
            $response = Invoke-WebRequest -Uri $ServiceUrl -TimeoutSec 5 -SkipCertificateCheck
            if ($response.StatusCode -eq 200) {
                Write-SIEMLog "Service is ready: $ServiceUrl" -Level "SUCCESS"
                return $true
            }
        } catch {
            # Service not ready yet, continue waiting
        }
        
        Start-Sleep -Seconds $IntervalSeconds
    }
    
    Write-SIEMLog "Timeout waiting for service: $ServiceUrl" -Level "ERROR"
    return $false
}

function Get-DeploymentSummary {
    $duration = (Get-Date) - $Global:SIEMConfig.StartTime
    
    $summary = @"
=== SIEM Platform Deployment Summary ===

Deployment Mode: $($Global:SIEMConfig.DeploymentMode)
Environment: $($Global:SIEMConfig.Environment)
Start Time: $($Global:SIEMConfig.StartTime)
Duration: $($duration.ToString("hh\:mm\:ss"))

Log File: $($Global:SIEMConfig.LogFile)

=== Next Steps ===
1. Verify all services are running
2. Configure initial users and permissions
3. Import threat intelligence feeds
4. Set up monitoring and alerting
5. Configure backup schedules

For support and documentation, visit:
https://github.com/siem-platform/docs
"@

    Write-SIEMLog $summary -Level "INFO"
    return $summary
}

function Install-RequiredModules {
    Write-SIEMLog "Installing required PowerShell modules..." -Level "INFO"
    
    $modules = @("Posh-SSH", "PowerCLI")
    
    foreach ($module in $modules) {
        if (!(Get-Module -ListAvailable -Name $module)) {
            Write-SIEMLog "Installing module: $module" -Level "INFO"
            try {
                Install-Module -Name $module -Force -AllowClobber -Scope CurrentUser
                Write-SIEMLog "Module installed successfully: $module" -Level "SUCCESS"
            } catch {
                Write-SIEMLog "Failed to install module: $module - $($_.Exception.Message)" -Level "ERROR"
                throw
            }
        } else {
            Write-SIEMLog "Module already installed: $module" -Level "INFO"
        }
    }
}

# Export functions
Export-ModuleMember -Function *

