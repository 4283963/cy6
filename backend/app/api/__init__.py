from fastapi import APIRouter
from .sensor import router as sensor_router
from .command import router as command_router
from .dashboard import router as dashboard_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(sensor_router, prefix="/sensor", tags=["传感器数据"])
api_router.include_router(command_router, prefix="/commands", tags=["控制指令"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["仪表盘"])

__all__ = ["api_router"]
