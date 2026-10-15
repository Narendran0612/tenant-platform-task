# Design: Tenant Platform

## 1. Purpose and current scope

This repository contains a FastAPI service for basic tenant-record lifecycle operations, Docker Compose configuration, and a Jenkins service. The intended broader design is to provision an isolated tenant application and route a tenant-specific hostname to it.

**Important implementation boundary:** the currently inspected `backend/app.py` only manages an in-memory dictionary. It does not call Jenkins, start tenant containers, persist records, or change proxy configuration. The sections below distinguish what is implemented from the intended extension.

## 2. Current architecture

```text
Client
  |
  | HTTP requests
  v
FastAPI backend (backend/app.py)
  |
  +-- in-memory dictionary: tenants
  |
  +-- Docker Compose also starts Jenkins
      (no invocation from app.py is currently implemented)
```

### Components

- **Backend API:** `GET /`, `GET /health`, `POST /tenants`, `GET /tenants`, `GET /tenants/{name}`, and `DELETE /tenants/{name}`.
- **In-memory registry:** stores each tenant's normalized name, creation timestamp, and `registered` status for the lifetime of the backend process.
- **Jenkins:** a service defined in Compose. The Compose environment includes `JENKINS_URL` and `JENKINS_JOB`, but the inspected API module does not consume these values.
- **Tenant app / frontend:** directories exist in the repository; their deployment relationship should be documented only after inspecting their source and Compose configuration.
- **Proxy:** a directory exists, but no proxy configuration was present in the earlier file listing. Hostname-based routing is therefore not yet established by the evidence inspected.

## 3. Tenant lifecycle: current behavior

### Registration

1. Client sends `POST /tenants` with JSON such as `{"name":"acme"}`.
2. API strips whitespace and lowercases the name.
3. Empty names return `400`; duplicates return `409`.
4. API stores an in-memory record with a UTC timestamp and `status: "registered"`.
5. API returns a success message and the record.

No Jenkins build or tenant application deployment is triggered by this current endpoint.

### Lookup

- `GET /tenants` returns the records currently in memory.
- `GET /tenants/{tenant_name}` normalizes the supplied name and returns its record, or `404` if absent.

### Deletion

1. Client sends `DELETE /tenants/{tenant_name}`.
2. API normalizes the name.
3. If it does not exist, the API returns `404`.
4. Otherwise, it removes the record from memory and returns a success message.

No Jenkins cleanup, container removal, DNS change, or proxy update is triggered by this current endpoint.

## 4. Intended Jenkins integration

A future provisioning integration can have the backend validate a tenant request and trigger an authenticated Jenkins job with a constrained tenant identifier and an explicit action such as `provision` or `delete`.

Suggested high-level flow:

```text
POST /tenants
  -> validate DNS-safe tenant identifier
  -> persist lifecycle state as pending
  -> trigger Jenkins provision action
  -> Jenkins deploys tenant service
  -> configure/verify proxy route
  -> health-check tenant
  -> persist status as live (only after successful checks)

DELETE /tenants/{name}
  -> persist deletion-pending state
  -> trigger Jenkins delete action
  -> remove proxy route and tenant resources
  -> verify cleanup
  -> mark deleted / remove record according to retention policy
```

This is a **target design**, not current behavior. It requires implementation of the Jenkins client, credential handling, persistent state, failure/retry handling, and tests. Never pass arbitrary shell text from a tenant name into a pipeline. Validate tenant identifiers against a strict allowlist, use Jenkins credentials for authentication, and make operations idempotent.

### Jenkins job naming

The Compose environment visible during inspection referenced `JENKINS_JOB=tenant-deployment`. Reviewers mentioned `my-first-pipeline`. Confirm the actual Jenkins job name and the job's configuration/console output before documenting either as the active job. Environment variables alone do not prove a job is invoked.

## 5. Intended subdomain routing

A typical target mapping is:

- `acme.example.com` -> Acme tenant service
- `globex.example.com` -> Globex tenant service

A reverse proxy (for example, NGINX) can inspect the HTTP `Host` header and route each known hostname to its corresponding tenant service. A safe implementation should use an explicit, controlled mapping rather than blindly turning arbitrary hostnames into upstream destinations.

Required pieces for a real deployment:

1. DNS records or a wildcard DNS record point tenant hostnames at the proxy.
2. The proxy and tenant services share a Docker network or another reachable network.
3. Provisioning creates or updates the hostname-to-service mapping.
4. TLS certificates cover the tenant hostnames (wildcard certificates require suitable DNS and certificate validation).
5. Deletion removes the mapping and tenant service, then verifies that the hostname no longer routes.
6. Unknown hostnames receive a default rejection response.

For local-only testing, hosts-file entries can map test names to `127.0.0.1`; this does not create public DNS records or production HTTPS.

No working subdomain routing should be claimed until the actual proxy file, DNS/hosts setup, network connectivity, and end-to-end hostname tests are present.

## 6. Reliability and security considerations

- **Persistence:** replace the in-memory dictionary with a database so records survive restarts.
- **Concurrency:** enforce uniqueness in persistent storage; in-memory checks are not safe across multiple workers.
- **Lifecycle state:** use explicit states such as `pending`, `provisioning`, `live`, `deleting`, and `failed`, with timestamps and failure details.
- **Retries and idempotency:** repeated requests or Jenkins retries must not create duplicate resources.
- **Credentials:** keep Jenkins API tokens in Jenkins Credentials or a secure secret store; never commit `.env` files or tokens.
- **Authorization:** protect tenant creation/deletion endpoints and Jenkins.
- **Input validation:** restrict tenant names to a DNS-safe pattern and prevent command injection.
- **Network isolation:** avoid exposing tenant services directly if all traffic should pass through the proxy.
- **Observability:** record correlation IDs and lifecycle events without logging secrets.
- **Testing:** cover API status codes, Jenkins success/failure, proxy routing, tenant health checks, and deletion cleanup.

## 7. Verification plan

Before presenting this as a complete automated provisioning system, verify all of the following:

- API health endpoint responds successfully.
- Register/list/get/delete API tests pass.
- Backend registration triggers the expected Jenkins job with the correct action and tenant parameter.
- Jenkins logs show the deployment/cleanup steps and return a reliable result.
- Each tenant hostname routes only to the matching tenant.
- Unknown hostnames are rejected.
- Failed builds do not mark tenants live.
- Deletion removes the route and tenant resources.
- A clean-machine clone can follow the README from prerequisites through verification.
