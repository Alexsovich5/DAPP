resource "null_resource" "docker_install" {
  provisioner "file" {
    source      = "${path.module}/../../scripts/setups_docker.sh"
    destination = "/tmp/setups_docker.sh"

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
      "cp /tmp/setups_docker.sh /tmp/scripts/",
      "chmod +x /tmp/setups_docker.sh",
      "sudo /tmp/setups_docker.sh"
    ]

    connection {
      type        = "ssh"
      user        = var.user
      host        = var.vm_ip
      private_key = file(pathexpand(var.ssh_private_key))
    }
  }
}
