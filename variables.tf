variable "admin_password" {
  description = "Password for admin users"
  default     = "Dinner1CI4dm1n!"
  sensitive   = true
}

variable "gitlab_domain" {
  description = "Domain for GitLab access"
  default     = "gitlab.local"
}

variable "sonarqube_domain" {
  description = "Domain for SonarQube access"
  default     = "sonarqube.local"
}

variable "gitlab_port" {
  description = "Port for GitLab web access"
  default     = 8080
}

variable "gitlab_ssh_port" {
  description = "Port for GitLab SSH access"
  default     = 2222
}

variable "sonarqube_port" {
  description = "Port for SonarQube web access"
  default     = 9000
}

variable "gitlab_runner_token" {
  description = "GitLab Runner registration token (obtain from GitLab Admin UI after first deploy)"
  type        = string
  default     = ""
  sensitive   = true
}
