"""仪表盘路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.employee import User
from app.models.payroll import Payroll
from app.models.performance import PerformanceAssessment
from app.auth import get_current_user
from app.services.report_service import get_dashboard_stats
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """首页仪表盘数据"""
    return get_dashboard_stats(db)


@router.get("/extended")
def extended_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """扩展仪表盘：薪酬+绩效合并 KPI"""
    now = datetime.now()
    year, month = now.year, now.month

    # 当月薪酬
    payroll_stats = db.query(
        func.count(Payroll.id), func.sum(Payroll.net_salary)
    ).filter(Payroll.year == year, Payroll.month == month).first()

    # 待确认/待发放
    pending_confirm = db.query(func.count(Payroll.id)).filter(
        Payroll.year == year, Payroll.month == month, Payroll.status == "草稿"
    ).scalar() or 0

    pending_pay = db.query(func.count(Payroll.id)).filter(
        Payroll.year == year, Payroll.month == month, Payroll.status == "已确认"
    ).scalar() or 0

    # 当月绩效
    total_assessments = db.query(func.count(PerformanceAssessment.id)).filter(
        PerformanceAssessment.status.in_(["待考核", "已完成", "已确认"])
    ).scalar() or 0

    completed = db.query(func.count(PerformanceAssessment.id)).filter(
        PerformanceAssessment.status.in_(["已完成", "已确认"])
    ).scalar() or 0

    completion_rate = round(completed / max(total_assessments, 1) * 100, 1)

    return {
        "year": year, "month": month,
        "payroll_headcount": payroll_stats[0] or 0,
        "total_net_salary": round(float(payroll_stats[1] or 0), 2),
        "pending_confirm": pending_confirm,
        "pending_pay": pending_pay,
        "total_assessments": total_assessments,
        "completion_rate": completion_rate,
    }
