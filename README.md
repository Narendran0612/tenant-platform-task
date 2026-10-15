# Tenant Platform

A small demo API for registering and managing tenant records, packaged with Docker Compose and a Jenkins service.

> **Implementation status:** This README describes the code currently shown in `backend/app.py`. The API stores tenants in an in-memory Python dictionary. Its registration and deletion endpoints do **not** currently invoke Jenkins, provision tenant containers, or configure subdomains. The Compose environment variables that point to Jenkins do not by themselves implement that integration.

## Repository layout

```text
.
├── backend/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── test_jenkins.py
│   └── trigger_jenkins.py
├── frontend/
├── tenant-app/
├── jenkins/
├── proxy/
└── docker-compose.yml
```

The `jenkins/` and `proxy/` directories may be empty in the current checkout. Add and test their configuration before describing Jenkins provisioning or subdomain routing as operational.

## Prerequisites

- Docker Desktop with Docker Compose v2
- Git, if cloning the repository
- Ports required by `docker-compose.yml` available on the host (the shown configuration maps the backend to port `5000` and Jenkins UI to port `8081`)

## Clone and start

```powershell
git clone https://github.com/Narendran0612/tenant-platform-task.git
cd tenant-platform-task
docker compose config
docker compose up --build -d
docker compose ps
```

Review `docker compose config` before startup. Do not commit `.env` files, passwords, API tokens, Jenkins secrets, or private keys. If a required local `.env` file is missing, create it from a safe `.env.example` after checking the actual application requirements; never copy real credentials into the repository.

View logs:

```powershell
docker compose logs --tail=100 backend
docker compose logs --tail=100 jenkins
```

Stop the services:

```powershell
docker compose down
```

This command retains named volumes unless `-v` is added. Avoid `docker compose down -v` if you want to preserve Jenkins state.

## API

The API is implemented with FastAPI in `backend/app.py`. If the Compose configuration maps host port `5000` to container port `5000`, the base URL is `http://localhost:5000`.

Interactive API documentation: `http://localhost:5000/docs`

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Basic service status |
| `GET` | `/health` | Health response |
| `POST` | `/tenants` | Register a tenant record |
| `GET` | `/tenants` | List registered tenant records |
| `GET` | `/tenants/{tenant_name}` | Retrieve one tenant record |
| `DELETE` | `/tenants/{tenant_name}` | Delete one tenant record |

### Example requests (PowerShell)

Check service health:

```powershell
Invoke-RestMethod http://localhost:5000/health
```

Register a tenant:

```powershell
$body = @{ name = "acme" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri http://localhost:5000/tenants `
  -ContentType "application/json" `
  -Body $body
```

List tenants:

```powershell
Invoke-RestMethod http://localhost:5000/tenants
```

Get one tenant:

```powershell
Invoke-RestMethod http://localhost:5000/tenants/acme
```

Delete a tenant:

```powershell
Invoke-RestMethod -Method Delete `
  -Uri http://localhost:5000/tenants/acme
```

### Current API behavior

- Tenant names are stripped of surrounding whitespace and converted to lowercase.
- An empty name returns HTTP `400`.
- Registering an already-registered name returns HTTP `409`.
- Getting or deleting an unknown tenant returns HTTP `404`.
- A newly registered record contains `name`, `created_at` (UTC ISO-8601 timestamp), and `status: "registered"`.
- Tenant records are kept in memory and are lost when the backend process restarts.
- The current API does not validate tenant names against a DNS-safe hostname pattern.

## Verification

Run these checks after startup:

```powershell
Invoke-RestMethod http://localhost:5000/
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/tenants
```

Then perform the register, retrieve, and delete examples above. Verify that a second registration of the same name returns `409`, and retrieving a deleted or unknown tenant returns `404`.

If any command fails, inspect `docker compose ps` and the backend logs before changing configuration.

## Jenkins and proxy status

The Compose file shown for this project defines a Jenkins service and passes `JENKINS_URL` / `JENKINS_JOB` environment variables to the backend. In the current `backend/app.py`, those variables are not read and neither tenant endpoint triggers a Jenkins build. A Jenkins job named `tenant-deployment` or `my-first-pipeline` must be configured separately and integration code must explicitly invoke it before automatic provisioning can be claimed.

Likewise, a `proxy/` directory alone does not provide subdomain routing. A working implementation needs a reverse-proxy configuration, a network path to the tenant services, DNS or local hostname mappings, and (for public use) TLS certificates. Do not use a sample proxy configuration in production without testing it against the actual tenant service names and network.

## Security and limitations

- Do not expose Jenkins to the public internet without authentication, authorization, and appropriate network restrictions.
- Keep credentials in Jenkins Credentials or an untracked local environment file, not in source code.
- The current in-memory registry is for demonstration only; use persistent storage and concurrency-safe operations for a real deployment.
- Do not claim tenant isolation, automatic provisioning, automatic deletion cleanup, HTTPS, or production readiness until those features are implemented and verified.
