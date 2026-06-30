"""薪酬福利管理模型"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class SalaryTemplate(Base):
    """工资模板/薪资结构"""
    __tablename__ = "salary_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(String(255), comment="说明")
    created_at = Column(DateTime, default=datetime.now)

    items = relationship("SalaryTemplateItem", back_populates="template")


class SalaryTemplateItem(Base):
    """工资项定义"""
    __tablename__ = "salary_template_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("salary_templates.id"))
    name = Column(String(50), nullable=False, comment="工资项名称")
    type = Column(String(10), comment="类型: income(加项)/deduction(减项)")
    is_default = Column(Integer, default=1, comment="是否默认项")
    is_taxable = Column(Integer, default=1, comment="是否计税")
    sort_order = Column(Integer, default=0, comment="排序")

    template = relationship("SalaryTemplate", back_populates="items")


class Payroll(Base):
    """月度工资表"""
    __tablename__ = "payrolls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), comment="员工ID")
    year = Column(Integer, comment="年份")
    month = Column(Integer, comment="月份")

    # 收入项
    base_salary = Column(Float, default=0, comment="基本工资")
    performance_bonus = Column(Float, default=0, comment="绩效工资")
    subsidy = Column(Float, default=0, comment="补贴")
    overtime_pay = Column(Float, default=0, comment="加班费")
    other_income = Column(Float, default=0, comment="其他收入")

    # 扣除项
    social_insurance = Column(Float, default=0, comment="社保个人部分")
    housing_fund = Column(Float, default=0, comment="公积金个人部分")
    tax = Column(Float, default=0, comment="个人所得税")
    absence_deduction = Column(Float, default=0, comment="缺勤扣款")
    other_deduction = Column(Float, default=0, comment="其他扣款")

    # 汇总
    total_income = Column(Float, default=0, comment="应发合计")
    total_deduction = Column(Float, default=0, comment="扣款合计")
    net_salary = Column(Float, default=0, comment="实发工资")

    # 新增: 模板关联 + 专项扣除 + 发放时间
    template_id = Column(Integer, ForeignKey("salary_templates.id"), nullable=True, comment="薪资结构模板")
    special_deduction = Column(Float, default=0, comment="月度专项附加扣除合计")
    paid_at = Column(DateTime, nullable=True, comment="发放时间")

    status = Column(String(20), default="草稿", comment="状态: 草稿/已确认/已发放")
    remark = Column(String(255), comment="备注")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    employee = relationship("Employee")
    items = relationship("PayrollItem", back_populates="payroll")
    bonus_links = relationship("PerformanceBonusLink", back_populates="payroll")


class PayrollItem(Base):
    """动态薪资项 (每工资条可自定义收入/扣款行)"""
    __tablename__ = "payroll_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payroll_id = Column(Integer, ForeignKey("payrolls.id"), comment="所属工资条")
    name = Column(String(50), nullable=False, comment="项目名称")
    type = Column(String(10), nullable=False, comment="类型: income/deduction")
    amount = Column(Float, default=0, comment="金额")
    is_taxable = Column(Integer, default=1, comment="是否计税")
    sort_order = Column(Integer, default=0, comment="排序")

    payroll = relationship("Payroll", back_populates="items")


class SpecialDeduction(Base):
    """专项附加扣除"""
    __tablename__ = "special_deductions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), comment="员工ID")
    year = Column(Integer, comment="年份")
    deduction_type = Column(String(20), nullable=False, comment="类型: 子女教育/继续教育/大病医疗/住房贷款利息/住房租金/赡养老人/婴幼儿照护")
    amount = Column(Float, default=0, comment="月度扣除金额")
    remark = Column(String(200), comment="备注")

    employee = relationship("Employee")


class PerformanceBonusLink(Base):
    """绩效-薪酬联动记录"""
    __tablename__ = "performance_bonus_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payroll_id = Column(Integer, ForeignKey("payrolls.id"), comment="工资条ID")
    assessment_id = Column(Integer, ForeignKey("performance_assessments.id"), comment="绩效评估ID")
    coefficient = Column(Float, default=1.0, comment="奖金系数")
    bonus_amount = Column(Float, default=0, comment="奖金金额")

    payroll = relationship("Payroll", back_populates="bonus_links")
    assessment = relationship("PerformanceAssessment")


class SocialInsurance(Base):
    """社保公积金配置"""
    __tablename__ = "social_insurances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city = Column(String(50), comment="参保城市")
    year = Column(Integer, comment="年份")

    # 社保基数 & 比例
    pension_base_min = Column(Float, comment="养老基数下限")
    pension_base_max = Column(Float, comment="养老基数上限")
    pension_personal = Column(Float, comment="养老个人比例(%)")
    pension_company = Column(Float, comment="养老单位比例(%)")

    medical_base_min = Column(Float, comment="医疗基数下限")
    medical_base_max = Column(Float, comment="医疗基数上限")
    medical_personal = Column(Float, comment="医疗个人比例(%)")
    medical_company = Column(Float, comment="医疗单位比例(%)")

    unemployment_personal = Column(Float, comment="失业个人比例(%)")
    unemployment_company = Column(Float, comment="失业单位比例(%)")

    injury_company = Column(Float, comment="工伤单位比例(%)")
    maternity_company = Column(Float, comment="生育单位比例(%)")

    housing_fund_min = Column(Float, comment="公积金基数下限")
    housing_fund_max = Column(Float, comment="公积金基数上限")
    housing_fund_personal = Column(Float, comment="公积金个人比例(%)")
    housing_fund_company = Column(Float, comment="公积金单位比例(%)")

    created_at = Column(DateTime, default=datetime.now)
