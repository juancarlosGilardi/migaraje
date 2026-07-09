from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import alerts, auth, catalog, documents, drivers, plan, services, vehicles

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(plan.router)
app.include_router(catalog.router)
app.include_router(services.router)
app.include_router(drivers.router)
app.include_router(documents.router)
app.include_router(alerts.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": "0.1.0"}
