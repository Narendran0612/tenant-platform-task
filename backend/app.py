from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

app = FastAPI(
    title="Tenant Platform API",
    description="API for registering and managing tenants",
    version="1.0.0"
)

# Demo storage (in memory)
tenants = {}


class TenantRequest(BaseModel):
    name: str


@app.get("/")
def home():
    return {
        "message": "Tenant Platform API is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/tenants")
def register_tenant(request: TenantRequest):
    name = request.name.strip().lower()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Tenant name cannot be empty"
        )

    if name in tenants:
        raise HTTPException(
            status_code=409,
            detail=f"Tenant '{name}' is already registered"
        )

    tenants[name] = {
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "registered"
    }

    return {
        "message": "Tenant registered successfully",
        "tenant": tenants[name]
    }


@app.get("/tenants")
def list_tenants():
    return {"tenants": list(tenants.values())}


@app.get("/tenants/{tenant_name}")
def get_tenant(tenant_name: str):
    name = tenant_name.strip().lower()

    if name not in tenants:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    return {"tenant": tenants[name]}


@app.delete("/tenants/{tenant_name}")
def delete_tenant(tenant_name: str):
    name = tenant_name.strip().lower()

    if name not in tenants:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )

    del tenants[name]

    return {
        "message": f"Tenant '{name}' deleted successfully"
    }