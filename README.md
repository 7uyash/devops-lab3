# DevOps Lab 3 — Monitoring, Logging & DevSecOps

Suyash Sahu — Roll No. 2301010476 — K R Mangalam University

An automated, observable and secure workflow built around **ShopLite**, a small Flask web shop (`app/`) that exposes
Prometheus metrics, writes structured access logs and uses feature flags. Every task runs end-to-end on GitHub Actions.

| # | Task | Files | Workflow |
|---|------|-------|----------|
| 1 | Configuration management with **Ansible** | `ansible/` (inventory, `site.yml`, `flags.yml`, templates, group vars) | `ansible.yml` |
| 2 | Infrastructure as Code with **Terraform** | `terraform/` (Docker provider: network, N app containers, nginx load balancer) | `terraform.yml` |
| 3 | Centralized logging with **ELK** | `elk/` (Filebeat → Logstash grok pipeline → Elasticsearch → Kibana dashboard) | `elk.yml` |
| 4 | **DevSecOps** pipeline | Gitleaks, Bandit, pip-audit, pytest, Trivy (image + IaC), SBOM, SARIF, security gate | `devsecops.yml` |
| 5 | Monitoring with **Prometheus & Grafana** | `monitoring/` (scrape config, alert rules, provisioned Grafana dashboard) | `monitoring.yml` |
| 6 | **Feature flags**, **load testing** (Locust) and **Selenium** | `app/flags.json`, `tests/load/`, `tests/selenium/`, `tests/unit/` | `testing.yml` |

## Application — `app/`
- `GET /`, `/api/products`, `/api/products/<id>`, `/checkout`, `/flags`, `/health`, `/metrics`
- `/api/slow` and `/api/error` produce slow requests and 500 errors for the monitoring and logging demos
- Metrics: `http_requests_total`, `http_request_duration_seconds`, `shop_orders_total`, `feature_flag_enabled`
- Feature flags in `flags.json` are re-read on every request (toggle without redeploy), can be overridden with
  `FLAG_<NAME>=true` and support percentage rollouts: `{"enabled": true, "rollout": 50}`
- Docker image runs as a non-root user with a health check

## Running locally
```bash
# Ansible (targets: two Ubuntu containers)
cd ansible && ansible-playbook site.yml
# Terraform
cd terraform && terraform init && terraform apply -var app_count=4
# ELK / Monitoring
docker compose -f elk/docker-compose.yml up -d        # Kibana  -> http://localhost:5601
docker compose -f monitoring/docker-compose.yml up -d # Grafana -> http://localhost:3000
# Tests
pytest tests/unit
locust -f tests/load/locustfile.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000
pytest tests/selenium
```

## Security practices used in the pipeline
- Read-only `GITHUB_TOKEN` by default; only the scan job gets `security-events: write`
- Third-party actions in the DevSecOps workflow are pinned to full commit SHAs
- Secrets scanning of the whole git history, SAST, dependency audit, container and IaC scanning
- Build fails on fixable HIGH/CRITICAL vulnerabilities (security gate); SBOM published as an artifact
- Dependabot keeps pip packages, the base image and GitHub Actions up to date
- `security/demo/` holds intentionally vulnerable samples to show what the scanners detect (not part of the gate)
