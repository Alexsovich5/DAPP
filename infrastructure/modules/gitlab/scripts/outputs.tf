output "gitlab_url" {
  value = "http://${var.gitlab_domain}"
}

output "gitlab_admin_username" {
  value = "root"
}

output "gitlab_admin_password" {
  value     = var.admin_password
  sensitive = true
}