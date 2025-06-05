# Create a Docker network for all services
resource "docker_network" "cicd_network" {
  name = "dinner1-cicd-network"
}

# Create required directories
resource "local_file" "ensure_directories" {
  for_each = toset([
    "${path.cwd}/gitlab-logs",
    "${path.cwd}/gitlab-data",
    "${path.cwd}/gitlab-runner-config"
  ])
  filename = "${each.value}/.keep"
  content  = ""

  lifecycle {
    ignore_changes = [content]
  }
}

# Run GitLab Docker Compose
resource "null_resource" "gitlab_docker_compose" {
  depends_on = [local_file.ensure_directories, docker_network.cicd_network]

  triggers = {
    docker_compose_sha = filesha256("${path.cwd}/docker-compose.gitlab.yml")
  }

  provisioner "local-exec" {
    command = "docker-compose -f docker-compose.gitlab.yml up -d"
    environment = {
      ADMIN_PASSWORD      = var.admin_password
      GITLAB_DOMAIN       = var.gitlab_domain
      GITLAB_PORT         = var.gitlab_port
      GITLAB_SSH_PORT     = var.gitlab_ssh_port
      GITLAB_RUNNER_TOKEN = var.gitlab_runner_token
    }
  }

  provisioner "local-exec" {
    when    = destroy
    command = "docker-compose -f docker-compose.gitlab.yml down -v"
  }
}

# Run SonarQube Docker Compose
resource "null_resource" "sonarqube_docker_compose" {
  depends_on = [docker_network.cicd_network]

  triggers = {
    docker_compose_sha = filesha256("${path.cwd}/docker-compose.sonarqube.yml")
  }

  provisioner "local-exec" {
    command = "docker-compose -f docker-compose.sonarqube.yml up -d"
    environment = {
      SONARQUBE_DOMAIN = var.sonarqube_domain
      SONARQUBE_PORT   = var.sonarqube_port
    }
  }

  provisioner "local-exec" {
    when    = destroy
    command = "docker-compose -f docker-compose.sonarqube.yml down -v"
  }
}
