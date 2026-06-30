"""
个人所得税计算引擎 — 2019年新税法累计预扣法 (累计预扣法)

年度累计应纳税额 = (累计收入 - 累计免税收入 - 累计减除费用 - 累计专项扣除
                     - 累计专项附加扣除 - 累计其他扣除) × 税率 - 速算扣除数 - 已预缴税额

专项附加扣除标准 (月度):
  - 子女教育: 2000元/每个子女
  - 继续教育: 400元 (或 300元/3600元定额)
  - 大病医疗: 据实扣除 (年度限额80000元)
  - 住房贷款利息: 1000元
  - 住房租金: 1500/1100/800元 (按城市)
  - 赡养老人: 3000元 (独生子女)
  - 婴幼儿照护: 2000元/每个婴幼儿
"""
from sqlalchemy.orm import Session
from app.models.payroll import Payroll, SpecialDeduction

# 年度累计预扣税率表 (2019+)
# (累计应纳税所得额上限, 税率, 速算扣除数)
ANNUAL_BRACKETS = [
    (36000, 0.03, 0),
    (144000, 0.10, 2520),
    (300000, 0.20, 16920),
    (420000, 0.25, 31920),
    (660000, 0.30, 52920),
    (960000, 0.35, 85920),
    (float("inf"), 0.45, 181920),
]

# 月度起征点
MONTHLY_THRESHOLD = 5000

# 专项附加扣除标准 (元/月)
DEDUCTION_STANDARDS = {
    "子女教育": 2000,
    "继续教育": 400,
    "大病医疗": 0,       # 据实扣除，非固定月额
    "住房贷款利息": 1000,
    "住房租金": 1500,     # 默认一线城市
    "赡养老人": 3000,
    "婴幼儿照护": 2000,
}


def get_cumulative_data(employee_id: int, year: int, month: int, db: Session) -> dict:
    """
    查询当年1月至当月所有已确认/已发放的工资记录
    返回累计收入、累计社保、累计公积金、累计专项扣除、已缴个税
    """
    previous = db.query(Payroll).filter(
        Payroll.employee_id == employee_id,
        Payroll.year == year,
        Payroll.month <= month,
        Payroll.status.in_(["已确认", "已发放"]),
    ).all()

    cumulative_income = sum((p.total_income or 0) for p in previous)
    cumulative_si = sum((p.social_insurance or 0) for p in previous)
    cumulative_hf = sum((p.housing_fund or 0) for p in previous)
    cumulative_special = sum((p.special_deduction or 0) for p in previous)
    cumulative_tax_paid = sum((p.tax or 0) for p in previous)

    return {
        "cumulative_income": cumulative_income,
        "cumulative_si": cumulative_si,
        "cumulative_hf": cumulative_hf,
        "cumulative_special": cumulative_special,
        "cumulative_tax_paid": cumulative_tax_paid,
        "month_count": month,
    }


def get_special_deductions_total(employee_id: int, year: int, month: int, db: Session) -> float:
    """
    查询员工某年度的月度专项附加扣除总额
    """
    deductions = db.query(SpecialDeduction).filter(
        SpecialDeduction.employee_id == employee_id,
        SpecialDeduction.year == year,
    ).all()

    total = 0.0
    for d in deductions:
        std = DEDUCTION_STANDARDS.get(d.deduction_type, 0)
        if d.deduction_type == "大病医疗":
            # 大病医疗据实扣除
            total += (d.amount or 0) / 12
        else:
            # 使用配置值或标准值
            total += (d.amount or 0) if d.amount else std

    return round(total, 2)


def calc_cumulative_tax(employee_id: int, year: int, month: int,
                         current_taxable: float, db: Session) -> float:
    """
    累计预扣法计算当月应缴个税

    Args:
        employee_id: 员工ID
        year: 年份
        month: 当前月份
        current_taxable: 当月应纳税所得额 (收入 - 社保 - 公积金 - 其他扣除)
        db: 数据库会话

    Returns:
        当月应缴个税
    """
    # 1. 获取累计数据
    cum = get_cumulative_data(employee_id, year, month, db)

    # 2. 累计减除费用 = 5000 × 当月月份数
    cumulative_threshold = MONTHLY_THRESHOLD * month

    # 3. 累计专项附加扣除
    monthly_special = get_special_deductions_total(employee_id, year, month, db)
    cumulative_special = monthly_special * month + cum["cumulative_special"]

    # 4. 累计应纳税所得额
    # = 累计收入 - 累计社保 - 累计公积金 - 累计减除费用 - 累计专项附加扣除
    cumulative_taxable = (
        cum["cumulative_income"] + current_taxable
        - cum["cumulative_si"]
        - cum["cumulative_hf"]
        - cumulative_threshold
        - cumulative_special
    )

    if cumulative_taxable <= 0:
        return 0.0

    # 5. 查年度累进税率表
    for limit, rate, quick_deduction in ANNUAL_BRACKETS:
        if cumulative_taxable <= limit:
            cumulative_tax = cumulative_taxable * rate - quick_deduction
            break
    else:
        cumulative_tax = cumulative_taxable * 0.45 - 181920

    # 6. 当月应缴 = 累计应缴 - 已预缴
    current_tax = max(0, cumulative_tax - cum["cumulative_tax_paid"])

    return round(current_tax, 2)
