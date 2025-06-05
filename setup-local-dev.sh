#!/bin/bash
set -e

echo "Installing development environment dependencies for macOS..."

# Check for Homebrew and install if not found
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew already installed."
fi

# Update Homebrew
echo "Updating Homebrew..."
brew update

# Install Terraform
if ! command -v terraform &> /dev/null; then
    echo "Installing Terraform..."
    brew install terraform
else
    echo "Terraform already installed."
fi

# Install Docker Desktop (Manual Step Reminder)
echo ""
echo "--------------------------------------------------------------------------------"
echo "IMPORTANT: Docker Desktop for macOS is required."
echo "If you haven't installed it, please download and install it from:"
echo "https://www.docker.com/products/docker-desktop/"
echo "Ensure Docker Desktop is running before proceeding with Terraform commands."
echo "--------------------------------------------------------------------------------"
echo ""

# The Libvirt/QEMU installation below is for Linux-based virtualization.
# On macOS, Docker Desktop provides the necessary environment for running
# the Docker containers defined in your Terraform configuration.
# Therefore, the following sections related to Libvirt/QEMU are commented out.
#
# # Install Libvirt/QEMU
# echo "Installing Libvirt and QEMU..."
# sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst virt-manager
#
# # Enable Libvirt service
# sudo systemctl enable libvirtd
# sudo systemctl start libvirtd
#
# # Add current user to libvirt group
# sudo usermod -aG libvirt $USER
# sudo usermod -aG kvm $USER

echo "Setup script complete for macOS!"
echo "Please ensure Docker Desktop is installed and running."
echo "You can now open this project in VS Code and use the Task Explorer to run Terraform commands (init, plan, apply)."