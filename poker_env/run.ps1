# PowerShell script to run poker bot test
# Usage: .\run.ps1 (defaults to 5 rounds)

# Detect container runtime (docker or podman)
$ContainerCmd = $null

if (Get-Command docker -ErrorAction SilentlyContinue) {
    $ContainerCmd = "docker"
    Write-Host "Detected Docker" -ForegroundColor Green
} elseif (Get-Command podman -ErrorAction SilentlyContinue) {
    $ContainerCmd = "podman"
    Write-Host "Detected Podman" -ForegroundColor Green
} else {
    Write-Host "Error: Neither Docker nor Podman is installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker or Podman first. See install_docker.md or install_podman.md for instructions." -ForegroundColor Yellow
    exit 1
}

# Default to 5 rounds for testing
$TotalRounds = 5

# Get script directory and set paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppPath = Join-Path $ScriptDir "app"
$MountPath = Join-Path $AppPath "players"

# Create timestamp for output directory
$Timestamp = Get-Date -Format "HHmmss"
$BaseOutputDir = ".\output"
$OutputDir = Join-Path $BaseOutputDir $Timestamp

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$SuccessCount = 0
$FailCount = 0

# Run all rounds sequentially
for ($i = 1; $i -le $TotalRounds; $i++) {
    $LogFile = Join-Path $OutputDir "round_$i.log"
    
    & $ContainerCmd run --rm --name="pokerengine_test_$i" `
        -v "${AppPath}:/app" `
        -v "${MountPath}:/app/players" `
        pokerengine *> $LogFile
}

# Check results
foreach ($i in 1..$TotalRounds) {
    $LogFile = Join-Path $OutputDir "round_$i.log"
    
    if (Test-Path $LogFile) {
        $LogContent = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
        
        if ($LogContent) {
            # Check if log file contains error indicators
            if ($LogContent -notmatch "error|failed|exception") {
                # Check if it contains game results
                if ($LogContent -match "winner|game|stack") {
                    $SuccessCount++
                } else {
                    $FailCount++
                }
            } else {
                $FailCount++
            }
        } else {
            $FailCount++
        }
    } else {
        $FailCount++
    }
}

# Display results
if ($FailCount -eq 0) {
    Write-Host "SUCCESS:" -ForegroundColor Green
    exit 0
} else {
    Write-Host "FAILED:" -ForegroundColor Red
    Write-Host "Check log files in $OutputDir\ for error details." -ForegroundColor Yellow
    exit 1
}
