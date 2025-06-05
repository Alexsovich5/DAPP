output "gitlab_url" {
  description = "URL to access GitLab web interface"
  value       = "http://localhost:${var.gitlab_port}"
}

output "gitlab_ssh" {
  description = "SSH connection string for GitLab repositories"
  value       = "ssh://git@localhost:${var.gitlab_ssh_port}"
}

output "sonarqube_url" {
  description = "URL to access SonarQube web interface"
  value       = "http://localhost:${var.sonarqube_port}"
}

output "gitlab_admin_username" {
  description = "GitLab admin username"
  value       = "root"
}

output "gitlab_admin_password" {
  description = "GitLab admin password"
  value       = var.admin_password
  sensitive   = true
}

output "sonarqube_admin_username" {
  description = "SonarQube admin username"
  value       = "admin"
}

output "sonarqube_admin_password" {
  description = "SonarQube admin password"
  value       = var.admin_password
  sensitive   = true
}

output "hosts_file_entries" {
  description = "Add these entries to your /etc/hosts file for domain name resolution"
  value       = "127.0.0.1 ${var.gitlab_domain} ${var.sonarqube_domain}"
}

output "service_urls" {
  description = "URLs for accessing the services"
  value = {
    gitlab     = "http://${var.gitlab_domain}:${var.gitlab_port}"
    gitlab_ssh = "ssh://git@${var.gitlab_domain}:${var.gitlab_ssh_port}"
    sonarqube  = "http://${var.sonarqube_domain}:${var.sonarqube_port}"
  }
}

output "network_info" {
  description = "Docker network information"
  value = {
    network_name = docker_network.cicd_network.name
    network_id   = docker_network.cicd_network.id
  }
}
