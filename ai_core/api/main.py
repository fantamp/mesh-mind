from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from ai_core.api.routers import ingest, chat
from ai_core.storage.db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title="Mesh Mind AI Core API",
    description="API Gateway for Mesh Mind AI Platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(chat.router, prefix="/api", tags=["Chat & QA"])

@app.get("/")
async def root():
    return {"message": "Mesh Mind AI Core API is running"}

@app.get("/api/")
async def api_root():
    return {"message": "Mesh Mind AI Core API is running"}
