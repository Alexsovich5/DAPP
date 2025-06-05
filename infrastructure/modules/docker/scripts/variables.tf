variable "vm_ip" {
  description = "IP address of the VM"
  type        = string
}

variable "ssh_private_key" {
  description = "Path to SSH private key file"
  type        = string
}

variable "user" {
  description = "Username for SSH connection"
  type        = string
  default     = "debian"
}
