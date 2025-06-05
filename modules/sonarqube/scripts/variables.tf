variable "vm_ip" {
  description = "IP address of the VM"
  type        = string
}

variable "ssh_private_key" {
  description = "Path to SSH private key file"
  type        = string
}

variable "sonarqube_domain" {
  description = "Domain for SonarQube access"
  type        = string
}

variable "admin_password" {
  description = "Password for SonarQube admin user"
  type        = string
  sensitive   = true
}

variable "user" {
  description = "Username for SSH connection"
  type        = string
  default     = "debian"
}
