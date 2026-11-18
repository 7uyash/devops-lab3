output "load_balancer_url" {
  description = "URL of the nginx load balancer"
  value       = "http://localhost:${var.lb_port}"
}

output "app_containers" {
  description = "Application containers and their IP addresses"
  value = {
    for c in docker_container.app : c.name => c.network_data[0].ip_address
  }
}

output "app_count" {
  value = var.app_count
}
