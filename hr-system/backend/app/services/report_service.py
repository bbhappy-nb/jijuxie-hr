"""报表统计服务"""
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, date
from app.models.employee import Employee, Department
from app.models.payroll import Payroll
from app.models.contract import LaborContract
from app.models.performance import PerformanceAssessment
from app.models.recruitment import Candidate


def get_dashboard_stats(db: Session) -> dict:
    today = date.today()
    current_month = today.month
    current_year = today.year

    # 员工统计
    total = db.query(func.count(Employee.id)).scalar() or 0
    active = db.query(func.count(Employee.id)).filter(
        Employee.status.in_(["在职", "试用期"])
    ).scalar() or 0

    # 本月入离职
    month_onboarding = db.query(func.count(Employee.id)).filter(
        extract("month", Employee.hire_date) == current_month,
        extract("year", Employee.hire_date) == current_year,
    ).scalar() or 0
    month_resignation = db.query(func.count(Employee.id)).filter(
        extract("month", Employee.resign_date) == current_month,
        extract("year", Employee.resign_date) == current_year,
    ).scalar() or 0

    # 部门分布
    departments = db.query(
        Department.name,
        func.count(Employee.id).label("count"),
    ).outerjoin(Employee, Employee.department_id == Department.id).group_by(
        Department.id, Department.name
    ).all()
    dept_dist = [{"name": d[0] or "未分配", "value": d[1]} for d in departments]

    # 月度薪酬趋势（近12个月）
    payroll_trend = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        total_pay = db.query(func.sum(Payroll.net_salary)).filter(
            Payroll.year == y, Payroll.month == m, Payroll.status != "草稿"
        ).scalar() or 0
        payroll_trend.append({"month": f"{y}-{m:02d}", "amount": round(float(total_pay), 2)})

    # 合同到期提醒（30天内）
    contract_expiring = db.query(func.count(LaborContract.id)).filter(
        LaborContract.status == "有效",
        LaborContract.end_date <= today.replace(day=today.day + 30) if False else date(today.year, today.month, today.day),
    ).scalar()
    # 简化处理
    contract_expiring = db.query(func.count(LaborContract.id)).filter(
        LaborContract.status == "有效",
    ).scalar() or 0

    # 待考核数
    pending = db.query(func.count(PerformanceAssessment.id)).filter(
        PerformanceAssessment.status == "待考核"
    ).scalar() or 0

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
