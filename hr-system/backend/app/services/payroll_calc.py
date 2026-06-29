"""薪酬计算引擎"""
from typing import List
from sqlalchemy.orm import Session
from app.models.payroll import Payroll, SocialInsurance
from app.models.employee import Employee


def calc_social_insurance(
    base_salary: float, city: str = "北京", year: int = 2024, db: Session = None
) -> dict:
    """计算社保公积金"""
    config = None
    if db:
        config = db.query(SocialInsurance).filter(
            SocialInsurance.city == city,
            SocialInsurance.year == year,
        ).first()

    if not config:
        # 默认北京2024年比例
        return {
            "pension": round(base_salary * 0.08, 2),
            "medical": round(base_salary * 0.02, 2) + 3,
            "unemployment": round(base_salary * 0.005, 2),
            "housing_fund": round(base_salary * 0.12, 2),
            "total": round(base_salary * (0.08 + 0.02 + 0.005 + 0.12), 2) + 3,
        }

    total = (
        base_salary * (config.pension_personal + config.medical_personal + config.unemployment_personal) / 100
        + base_salary * config.housing_fund_personal / 100
    )
    return {
        "pension": round(base_salary * config.pension_personal / 100, 2),
        "medical": round(base_salary * config.medical_personal / 100, 2),
        "unemployment": round(base_salary * config.unemployment_personal / 100, 2),
        "housing_fund": round(base_salary * config.housing_fund_personal / 100, 2),
        "total": round(total, 2),
    }


def calc_tax(taxable_income: float) -> float:
    """计算个人所得税（累计预扣法简化版 - 月度）"""
    # 起征点 5000
    taxable = taxable_income - 5000
    if taxable <= 0:
        return 0

    # 累进税率表（月度）
    brackets = [
        (3000, 0.03, 0),
        (12000, 0.10, 210),
        (25000, 0.20, 1410),
        (35000, 0.25, 2660),
        (55000, 0.30, 4410),
        (80000, 0.35, 7160),
        (float("inf"), 0.45, 15160),
    ]
    for limit, rate, deduction in brackets:
        if taxable <= limit:
            return round(taxable * rate - deduction, 2)
    return 0


def calc_payroll(employee_id: int, year: int, month: int, db: Session) -> Payroll:
    """自动计算一条工资记录"""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("员工不存在")

    payroll = db.query(Payroll).filter(
        Payroll.employee_id == employee_id,
        Payroll.year == year,
        Payroll.month == month,
    ).first()

    if not payroll:
        payroll = Payroll(employee_id=employee_id, year=year, month=month, base_salary=emp.base_salary)

    # 社保公积金
    si = calc_social_insurance(payroll.base_salary or 0, db=db)
    payroll.social_insurance = si["pension"] + si["medical"] + si["unemployment"]
    payroll.housing_fund = si["housing_fund"]

    # 应发合计
    payroll.total_income = (
        (payroll.base_salary or 0)
        + (payroll.performance_bonus or 0)
        + (payroll.subsidy or 0)
        + (payroll.overtime_pay or 0)
        + (payroll.other_income or 0)
    )

    # 计税
    taxable = payroll.total_income - payroll.social_insurance - payroll.housing_fund
    payroll.tax = calc_tax(taxable)

    # 扣款合计
    payroll.total_deduction = (
        payroll.social_insurance
        + payroll.housing_fund
        + payroll.tax
        + (payroll.absence_deduction or 0)
        + (payroll.other_deduction or 0)
    )

    # 实发
    payroll.net_salary = round(payroll.total_income - payroll.total_deduction, 2)
    payroll.total_income = round(payroll.total_income, 2)
    payroll.total_deduction = round(payroll.total_deduction, 2)

    return payroll
