variable "vm_ip" {
  description = "IP address of the VM"
  type        = string
}

variable "ssh_private_key" {
  description = "Path to SSH private key file"
  type        = string
}

variable "gitlab_domain" {
  description = "Domain for GitLab access"
  type        = string
}

variable "admin_password" {
  description = "Password for GitLab admin user"
  type        = string
  sensitive   = true
}

variable "user" {
  description = "Username for SSH connection"
  type        = string
  default     = "debian"
}
