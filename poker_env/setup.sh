#!/bin/bash

# Detect container runtime (docker or podman)
if command -v docker >/dev/null 2>&1; then
    CONTAINER_CMD="docker"
    echo "Detected Docker"
elif command -v podman >/dev/null 2>&1; then
    CONTAINER_CMD="podman"
    echo "Detected Podman"
else
    echo "Error: Neither Docker nor Podman is installed or not in PATH"
    echo "Please install Docker or Podman first. See install_docker.md or install_podman.md for instructions."
    exit 1
fi

# Load the container image
$CONTAINER_CMD load -i pokerengine.tar