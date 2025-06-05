resource "null_resource" "gitlab_install" {
  provisioner "file" {
    source      = "${path.module}/../../scripts/setups_gitlab.sh"
    destination = "/tmp/setups_gitlab.sh"

    connection {
      type        = "ssh"
      user        = var.user
      host        = var.vm_ip
      private_key = file(pathexpand(var.ssh_private_key))
    }
  }

  provisioner "remote-exec" {
    inline = [
      "mkdir -p /tmp/scripts",
      "cp /tmp/setups_gitlab.sh /tmp/scripts/",
      "chmod +x /tmp/setups_gitlab.sh",
      "sudo GITLAB_DOMAIN=${var.gitlab_domain} ADMIN_PASSWORD=${var.admin_password} /tmp/setups_gitlab.sh"
    ]

    connection {
      type        = "ssh"
      user        = var.user
      host        = var.vm_ip
      private_key = file(pathexpand(var.ssh_private_key))
    }
  }
}
