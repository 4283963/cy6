from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .api import api_router
from .config import get_settings

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="智能鱼缸控制系统 API",
    description="金鱼与白子孔雀鱼混养缸智能控制后端系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["系统"])
def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "fish-tank-controller"}


@app.get("/", tags=["系统"])
def root():
    return {
        "name": "智能鱼缸控制系统",
        "version": "1.0.0",
        "docs": "/docs",
    }
