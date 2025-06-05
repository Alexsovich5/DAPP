#!/bin/bash
set -e

SONARQUBE_CONTAINER_NAME="sonarqube" # As defined in main.tf
SONARQUBE_DOMAIN=${SONARQUBE_DOMAIN:-sonarqube.local} # Should match var.sonarqube_domain
ADMIN_PASSWORD=${ADMIN_PASSWORD:-Dinner1CI4dm1n!} # Default admin password to change FROM is 'admin'
NEW_ADMIN_PASSWORD=${NEW_ADMIN_PASSWORD:-Dinner1CI4dm1n!} # Should match var.sonarqube_admin_password if you intend to set it via API

echo "--------------------------------------------------------------------------------"
echo "SonarQube Post-Setup Information (macOS / Docker Desktop)"
echo "--------------------------------------------------------------------------------"
echo ""
echo "SonarQube and its PostgreSQL database are deployed via Terraform using Docker."
echo "Access SonarQube at: http://${SONARQUBE_DOMAIN}:9000 or http://localhost:9000"
echo "Default initial admin username: admin"
echo "Default initial admin password: admin"
echo ""

echo "Checking if SonarQube container '${SONARQUBE_CONTAINER_NAME}' is running..."
if ! docker ps --filter "name=${SONARQUBE_CONTAINER_NAME}" --filter "status=running" --format "{{.Names}}" | grep -q "^${SONARQUBE_CONTAINER_NAME}$"; then
    echo "Error: SonarQube container '${SONARQUBE_CONTAINER_NAME}' is not running."
    echo "Please ensure you have run 'terraform apply' successfully."
    exit 1
fi
echo "SonarQube container is running."
echo ""

echo "Waiting for SonarQube to be operational... (this might take a few minutes)"
MAX_ATTEMPTS=30
SLEEP_DURATION=10
attempt_num=1
until curl -s -I -u admin:admin "http://localhost:9000/api/system/status" | grep -q "HTTP/1.1 200"; do
    if [ ${attempt_num} -eq ${MAX_ATTEMPTS} ]; then
        echo "Error: SonarQube did not become operational after ${MAX_ATTEMPTS} attempts."
        echo "Please check the container logs: docker logs ${SONARQUBE_CONTAINER_NAME}"
        exit 1
    fi
    echo "Attempt ${attempt_num}/${MAX_ATTEMPTS}: SonarQube not ready yet, sleeping for ${SLEEP_DURATION}s..."
    sleep ${SLEEP_DURATION}
    attempt_num=$((attempt_num+1))
done
echo "SonarQube is operational."
echo ""

echo "To change the default SonarQube admin password (admin/admin) to '${NEW_ADMIN_PASSWORD}':"
echo "1. Execute the following command in your terminal:"
echo "   curl -u admin:admin -X POST \"http://localhost:9000/api/users/change_password?login=admin&previousPassword=admin&password=${NEW_ADMIN_PASSWORD}\""
echo "   (Ensure you replace '${NEW_ADMIN_PASSWORD}' if you chose a different one.)"
echo ""

# Note: The quality gate setup from the original script is complex and involves multiple API calls.
# It's better to guide the user to do this via the SonarQube UI or a dedicated script if full automation is needed.
echo "To set up Quality Gates:"
echo "1. Log in to SonarQube (http://localhost:9000) as admin."
echo "2. Navigate to 'Quality Gates' and configure them as required."
echo "   The original script attempted to create a gate named 'Dinner1 Standard Gate' with specific conditions."
echo "   You can replicate this manually or adapt the curl commands from the original script if needed."
echo "   Example for creating a quality gate (adapt as necessary):"
echo "   curl -u admin:${NEW_ADMIN_PASSWORD} -X POST \"http://localhost:9000/api/qualitygates/create?name=MyCustomGate\""
echo ""

echo "Local Domain Resolution (/${SONARQUBE_DOMAIN}):"
echo "To access SonarQube via http://${SONARQUBE_DOMAIN}:9000, you might need to add an entry to your /etc/hosts file on macOS."
echo "1. Open Terminal and run: sudo nano /etc/hosts"
echo "2. Add the line: 127.0.0.1 ${SONARQUBE_DOMAIN}"
echo "3. Save the file (Ctrl+O, Enter, then Ctrl+X)."
echo "   Alternatively, access SonarQube via http://localhost:9000."
echo ""

echo "SonarQube post-setup guidance complete."