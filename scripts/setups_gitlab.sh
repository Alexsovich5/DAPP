#!/bin/bash
set -e

GITLAB_CONTAINER_NAME="gitlab" # As defined in main.tf
GITLAB_DOMAIN=${GITLAB_DOMAIN:-gitlab.local} # Should match var.gitlab_domain
ADMIN_PASSWORD=${ADMIN_PASSWORD:-Dinner1CI4dm1n!} # Should match var.gitlab_root_password

echo "--------------------------------------------------------------------------------"
echo "GitLab Post-Setup Information (macOS / Docker Desktop)"
echo "--------------------------------------------------------------------------------"
echo ""
echo "GitLab and the GitLab Runner are deployed via Terraform using Docker."
echo "The initial root password is set by Terraform (var.gitlab_root_password)."
echo "The GitLab Runner registration token must be provided as a Terraform variable (var.gitlab_runner_registration_token)."
echo ""
echo "Access GitLab at: http://${GITLAB_DOMAIN} (or http://localhost if port 80 is mapped to localhost)"
echo "Username: root"
echo "Password: ${ADMIN_PASSWORD}"
echo ""

echo "Checking if GitLab container '${GITLAB_CONTAINER_NAME}' is running..."
if ! docker ps --filter "name=${GITLAB_CONTAINER_NAME}" --filter "status=running" --format "{{.Names}}" | grep -q "^${GITLAB_CONTAINER_NAME}$"; then
    echo "Error: GitLab container '${GITLAB_CONTAINER_NAME}' is not running."
    echo "Please ensure you have run 'terraform apply' successfully."
    exit 1
fi
echo "GitLab container is running."
echo ""

echo "To enable shared runners (if not already enabled by default or omnibus config):"
echo "1. Wait for GitLab to be fully initialized after 'terraform apply'."
echo "2. Execute the following command in your terminal:"
echo "   docker exec ${GITLAB_CONTAINER_NAME} gitlab-rails runner "Gitlab::CurrentSettings.current_application_settings.update_attribute(:shared_runners_enabled, true)""
echo ""

echo "Local Domain Resolution (/${GITLAB_DOMAIN}):"
echo "To access GitLab via http://${GITLAB_DOMAIN}, you might need to add an entry to your /etc/hosts file on macOS."
echo "1. Open Terminal and run: sudo nano /etc/hosts"
echo "2. Add the line: 127.0.0.1 ${GITLAB_DOMAIN}"
echo "3. Save the file (Ctrl+O, Enter, then Ctrl+X)."
echo "   Alternatively, access GitLab via http://localhost (if port 80 is mapped directly)."
echo ""
echo "GitLab post-setup guidance complete."