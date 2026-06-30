"""
薪酬计算引擎 v2
- 社保公积金: 强制执行基数上下限
- 个税: 累计预扣法 (2019新税法)
- 动态薪资项: PayrollItem 参与汇总
- 绩效联动: 自动从评估结果计算绩效奖金
"""
from sqlalchemy.orm import Session
from app.models.payroll import Payroll, SocialInsurance, PayrollItem, PerformanceBonusLink
from app.models.employee import Employee
from app.models.performance import PerformanceAssessment, PerformancePlan
from app.services.tax_calc import calc_cumulative_tax


def clamp_to_bounds(value: float, minimum: float, maximum: float) -> float:
    """将值限制在 [minimum, maximum] 范围内"""
    if minimum and value < minimum:
        return minimum
    if maximum and value > maximum:
        return maximum
    return value


def calc_social_insurance(
    base_salary: float, city: str = "北京", year: int = 2024, db: Session = None
) -> dict:
    """计算社保公积金（强制执行基数上下限）"""
    result = {"pension": 0, "medical": 0, "unemployment": 0, "housing_fund": 0, "total": 0,
              "details": {}}

    config = None
    if db:
        config = db.query(SocialInsurance).filter(
            SocialInsurance.city == city,
            SocialInsurance.year == year,
        ).first()

    if not config:
        # 默认北京2024年比例
        result["pension"] = round(base_salary * 0.08, 2)
        result["medical"] = round(base_salary * 0.02 + 3, 2)
        result["unemployment"] = round(base_salary * 0.005, 2)
        result["housing_fund"] = round(base_salary * 0.12, 2)
        result["total"] = round(sum([result["pension"], result["medical"],
                                      result["unemployment"], result["housing_fund"]]), 2)
        return result

    # 社保: 各项分别封顶保底
    pension_base = clamp_to_bounds(base_salary, config.pension_base_min or 0, config.pension_base_max or 0)
    medical_base = clamp_to_bounds(base_salary, config.medical_base_min or 0, config.medical_base_max or 0)
    hf_base = clamp_to_bounds(base_salary, config.housing_fund_min or 0, config.housing_fund_max or 0)

    # 失业/工伤/生育通常共用医保基数
    unemployment_base = medical_base

    result["pension"] = round(pension_base * (config.pension_personal or 0) / 100, 2)
    result["medical"] = round(medical_base * (config.medical_personal or 0) / 100, 2)
    result["unemployment"] = round(unemployment_base * (config.unemployment_personal or 0) / 100, 2)
    result["housing_fund"] = round(hf_base * (config.housing_fund_personal or 0) / 100, 2)
    result["total"] = round(sum([result["pension"], result["medical"],
                                  result["unemployment"], result["housing_fund"]]), 2)

    result["details"] = {
        "pension_base": pension_base,
        "medical_base": medical_base,
        "housing_fund_base": hf_base,
    }

    return result


def calc_performance_bonus_from_assessment(assessment_id: int, db: Session) -> float:
    """根据绩效评估结果计算绩效奖金系数和金额"""
    assessment = db.query(PerformanceAssessment).filter(
        PerformanceAssessment.id == assessment_id
    ).first()
    if not assessment or not assessment.grade:
        return 0.0

    # 获取方案的奖金系数映射
    plan = db.query(PerformancePlan).filter(
        PerformancePlan.id == assessment.plan_id
    ).first()

    if not plan or not plan.bonus_coefficients:
        return 0.0

    # 解析 "S:1.5,A:1.2,B:1.0,C:0.8,D:0.5"
    coeff_map = {}
    for pair in plan.bonus_coefficients.split(","):
        if ":" in pair:
            grade, coeff = pair.strip().split(":")
            coeff_map[grade.strip()] = float(coeff)

    grade = assessment.grade.strip()
    return coeff_map.get(grade, 0.0)


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
        payroll = Payroll(
            employee_id=employee_id,
            year=year,
            month=month,
            base_salary=emp.base_salary or 0,
        )

    # 1. 社保公积金 (含基数封顶保底)
    si = calc_social_insurance(payroll.base_salary or 0, db=db)
    payroll.social_insurance = si["pension"] + si["medical"] + si["unemployment"]
    payroll.housing_fund = si["housing_fund"]

    # 2. 汇总动态薪资项
    dynamic_income = 0.0
    dynamic_deduction = 0.0
    if payroll.id:
        items = db.query(PayrollItem).filter(PayrollItem.payroll_id == payroll.id).all()
    else:
        items = []
    for item in items:
        if item.type == "income":
            dynamic_income += (item.amount or 0)
        elif item.type == "deduction":
            dynamic_deduction += (item.amount or 0)

    # 3. 应发合计 = 固定收入项 + 动态收入项
    payroll.total_income = round(
        (payroll.base_salary or 0)
        + (payroll.performance_bonus or 0)
        + (payroll.subsidy or 0)
        + (payroll.overtime_pay or 0)
        + (payroll.other_income or 0)
        + dynamic_income,
        2,
    )

    # 4. 应纳税所得额 = 应发合计 - 社保 - 公积金 - 专项附加扣除
    special_deduction = payroll.special_deduction or 0
    current_taxable = payroll.total_income - payroll.social_insurance - payroll.housing_fund - special_deduction

    # 5. 累计预扣法计算个税
    payroll.tax = calc_cumulative_tax(employee_id, year, month, current_taxable, db)

    # 6. 扣款合计
    payroll.total_deduction = round(
        payroll.social_insurance
        + payroll.housing_fund
        + payroll.tax
        + (payroll.absence_deduction or 0)
        + (payroll.other_deduction or 0)
        + dynamic_deduction,
        2,
    )

    # 7. 实发
    payroll.net_salary = round(payroll.total_income - payroll.total_deduction, 2)

    return payroll


def link_assessment_to_payroll(payroll_id: int, assessment_id: int, db: Session) -> dict:
    """将绩效评估结果关联到工资条，自动计算绩效奖金"""
    payroll = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not payroll:
        raise ValueError("工资条不存在")

    assessment = db.query(PerformanceAssessment).filter(
        PerformanceAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise ValueError("评估记录不存在")

    # 检查是否已关联
    existing = db.query(PerformanceBonusLink).filter(
        PerformanceBonusLink.payroll_id == payroll_id,
        PerformanceBonusLink.assessment_id == assessment_id,
    ).first()
    if existing:
        return {"coefficient": existing.coefficient, "bonus_amount": existing.bonus_amount}

    # 计算奖金系数
    coeff = calc_performance_bonus_from_assessment(assessment_id, db)

    # 计算奖金 = 基本工资 × 系数
    bonus = round((payroll.base_salary or 0) * coeff, 2)

    # 创建联动记录
    link = PerformanceBonusLink(
        payroll_id=payroll_id,
        assessment_id=assessment_id,
        coefficient=coeff,
        bonus_amount=bonus,
    )
    db.add(link)

    # 更新工资条的绩效奖金
    payroll.performance_bonus = bonus

    # 重新计算整条工资
    calc_payroll(payroll.employee_id, payroll.year, payroll.month, db)

    return {"coefficient": coeff, "bonus_amount": bonus, "grade": assessment.grade}
