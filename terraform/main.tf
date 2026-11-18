locals {
  app_names = [for i in range(var.app_count) : "${var.environment}-app-${i + 1}"]
  labels = {
    project    = "devops-lab3"
    managed_by = "terraform"
  }
}

# ---------- network ----------
resource "docker_network" "app_net" {
  name   = "${var.environment}-net"
  driver = "bridge"
  ipam_config {
    subnet = "172.30.0.0/24"
  }
}

# ---------- image built from the repo ----------
resource "docker_image" "app" {
  name = "shoplite:${var.app_version}"
  build {
    context = "${path.module}/../app"
  }
  triggers = {
    code_hash = filesha1("${path.module}/../app/app.py")
  }
  keep_locally = true
}

resource "docker_image" "nginx" {
  name         = "nginx:1.27-alpine"
  keep_locally = true
}

# ---------- application tier (scales with var.app_count) ----------
resource "docker_container" "app" {
  count    = var.app_count
  name     = local.app_names[count.index]
  image    = docker_image.app.image_id
  restart  = "unless-stopped"
  memory   = var.memory_mb
  hostname = local.app_names[count.index]

  env = [
    "APP_INSTANCE=${local.app_names[count.index]}",
    "APP_VERSION=${var.app_version}",
  ]

  networks_advanced {
    name    = docker_network.app_net.id
    aliases = [local.app_names[count.index]]
  }

  healthcheck {
    test     = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
    interval = "10s"
    timeout  = "3s"
    retries  = 3
  }

  dynamic "labels" {
    for_each = local.labels
    content {
      label = labels.key
      value = labels.value
    }
  }
}

# ---------- load balancer ----------
resource "docker_container" "lb" {
  name    = "${var.environment}-lb"
  image   = docker_image.nginx.image_id
  restart = "unless-stopped"

  ports {
    internal = 80
    external = var.lb_port
  }

  upload {
    file = "/etc/nginx/conf.d/default.conf"
    content = templatefile("${path.module}/nginx.conf.tftpl", {
      backends = local.app_names
    })
  }

  networks_advanced {
    name = docker_network.app_net.id
  }

  depends_on = [docker_container.app]

  dynamic "labels" {
    for_each = local.labels
    content {
      label = labels.key
      value = labels.value
    }
  }
}
