variable "environment" {
  description = "Environment name used as a prefix for all resources"
  type        = string
  default     = "lab3"
}

variable "app_count" {
  description = "Number of application containers behind the load balancer"
  type        = number
  default     = 2

  validation {
    condition     = var.app_count >= 1 && var.app_count <= 10
    error_message = "app_count must be between 1 and 10."
  }
}

variable "app_version" {
  description = "Version string passed to the application"
  type        = string
  default     = "1.0.0"
}

variable "lb_port" {
  description = "Host port of the nginx load balancer"
  type        = number
  default     = 8080
}

variable "memory_mb" {
  description = "Memory limit for each application container"
  type        = number
  default     = 256
}
