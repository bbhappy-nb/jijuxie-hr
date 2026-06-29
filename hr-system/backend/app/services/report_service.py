"""报表统计服务"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.models.employee import Employee, Department
from app.models.payroll import Payroll
from app.models.contract import LaborContract
from app.models.performance import PerformanceAssessment


def get_dashboard_stats(db: Session) -> dict:
    today = date.today()

    # 员工统计
    total = db.query(func.count(Employee.id)).scalar() or 0
    active = db.query(func.count(Employee.id)).filter(
        Employee.status.in_(["在职", "试用期"])
    ).scalar() or 0

    # 本月入离职 - 使用 SQLite 兼容方式
    month_onboarding = 0
    month_resignation = 0
    employees = db.query(Employee).all()
    for emp in employees:
        if emp.hire_date and emp.hire_date.year == today.year and emp.hire_date.month == today.month:
            month_onboarding += 1
        if emp.resign_date and emp.resign_date.year == today.year and emp.resign_date.month == today.month:
            month_resignation += 1

    # 部门分布
    try:
        departments = db.query(
            Department.name,
            func.count(Employee.id).label("count"),
        ).outerjoin(Employee, Employee.department_id == Department.id).group_by(
            Department.id, Department.name
        ).all()
        dept_dist = [{"name": d[0] or "未分配", "value": d[1]} for d in departments]
    except Exception:
        dept_dist = []

    # 月度薪酬趋势（近12个月）
    payroll_trend = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        try:
            total_pay = db.query(func.sum(Payroll.net_salary)).filter(
                Payroll.year == y, Payroll.month == m, Payroll.status != "草稿"
            ).scalar() or 0
        except Exception:
            total_pay = 0
        payroll_trend.append({"month": f"{y}-{m:02d}", "amount": round(float(total_pay), 2)})

    # 合同到期提醒
    try:
        contract_expiring = db.query(func.count(LaborContract.id)).filter(
            LaborContract.status == "有效",
        ).scalar() or 0
    except Exception:
        contract_expiring = 0

    # 待考核数
    try:
        pending = db.query(func.count(PerformanceAssessment.id)).filter(
            PerformanceAssessment.status == "待考核"
        ).scalar() or 0
    except Exception:
        pending = 0

    return {
        "total_employees": total,
        "active_employees": active,
        "month_onboarding": month_onboarding,
        "month_resignation": month_resignation,
        "department_distribution": dept_dist,
        "monthly_payroll_trend": payroll_trend,
        "contract_expiring": contract_expiring,
        "pending_assessments": pending,
    }
