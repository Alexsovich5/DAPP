resource "null_resource" "sonarqube_install" {
  provisioner "file" {
    source      = "${path.module}/../../scripts/setups_sonarcube.sh"
    destination = "/tmp/setups_sonarcube.sh"

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
      "cp /tmp/setups_sonarcube.sh /tmp/scripts/",
      "chmod +x /tmp/setups_sonarcube.sh",
      "sudo SONARQUBE_DOMAIN=${var.sonarqube_domain} ADMIN_PASSWORD=${var.admin_password} /tmp/setups_sonarcube.sh"
    ]

    connection {
      type        = "ssh"
      user        = var.user
      host        = var.vm_ip
      private_key = file(pathexpand(var.ssh_private_key))
    }
  }
}
