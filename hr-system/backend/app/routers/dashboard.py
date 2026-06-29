"""仪表盘路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.employee import User
from app.auth import get_current_user
from app.services.report_service import get_dashboard_stats

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """首页仪表盘数据"""
    return get_dashboard_stats(db)
