# PowerShell script to load container image
# Usage: .\setup.ps1

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

# Load the container image
& $ContainerCmd load -i pokerengine.tar

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to load container image" -ForegroundColor Red
    exit 1
}

Write-Host "Container image loaded successfully" -ForegroundColor Green
