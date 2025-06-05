output "sonarqube_url" {
  value = "http://${var.sonarqube_domain}"
}

output "sonarqube_admin_username" {
  value = "admin"
}

output "sonarqube_admin_password" {
  value     = var.admin_password
  sensitive = true
}