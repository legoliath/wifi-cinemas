from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router, ws_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🎬 WiFi Cinémas API starting...")
    yield

app = FastAPI(title="WiFi Cinémas API", description="Professional WiFi management for film sets", version="0.1.0", lifespan=lifespan, docs_url="/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"] if settings.app_env == "development" else settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(api_router)
app.include_router(ws_router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "wifi-cinemas-api", "version": "0.1.0"}
