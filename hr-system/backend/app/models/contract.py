"""劳动关系管理模型"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class LaborContract(Base):
    """劳动合同"""
    __tablename__ = "labor_contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), comment="员工ID")
    contract_no = Column(String(50), unique=True, comment="合同编号")
    type = Column(String(20), default="固定期限", comment="类型: 固定期限/无固定期限/项目合同/实习协议")

    start_date = Column(Date, comment="合同开始日期")
    end_date = Column(Date, comment="合同结束日期")
    probation_months = Column(Integer, default=0, comment="试用期月数")

    status = Column(String(20), default="有效", comment="状态: 有效/即将到期/已到期/已解除")
    sign_date = Column(Date, comment="签订日期")
    termination_date = Column(Date, comment="解除日期")
    termination_reason = Column(String(255), comment="解除原因")

    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    employee = relationship("Employee")


class OnboardingRecord(Base):
    """入职记录"""
    __tablename__ = "onboarding_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), comment="员工ID")
    onboard_date = Column(Date, comment="入职日期")

    # 手续清单
    id_card_copy = Column(Integer, default=0, comment="身份证复印件(0未交/1已交)")
    education_cert = Column(Integer, default=0, comment="学历证书")
    photo = Column(Integer, default=0, comment="照片")
    bank_card = Column(Integer, default=0, comment="银行卡")
    health_check = Column(Integer, default=0, comment="体检报告")
    resignation_cert = Column(Integer, default=0, comment="离职证明")
    signed_contract = Column(Integer, default=0, comment="已签合同")

    # 物品领用
    computer = Column(String(100), comment="电脑")
    phone_device = Column(String(100), comment="电话")
    access_card = Column(String(50), comment="门禁卡")
    office_supplies = Column(String(255), comment="办公用品")

    status = Column(String(20), default="办理中", comment="状态: 办理中/已完成")
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")


class ResignationRecord(Base):
    """离职记录"""
    __tablename__ = "resignation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), comment="员工ID")
    apply_date = Column(Date, comment="申请日期")
    resign_date = Column(Date, comment="最后工作日")
    type = Column(String(20), comment="类型: 主动离职/协商解除/辞退/退休")
    reason = Column(Text, comment="离职原因")
    exit_interview = Column(Text, comment="离职面谈记录")

    # 交接
    handover_person = Column(String(50), comment="工作交接人")
    handover_status = Column(String(20), default="未完成", comment="交接状态")
    asset_returned = Column(Integer, default=0, comment="资产归还(0未/1已)")

    status = Column(String(20), default="审批中", comment="状态: 审批中/交接中/已完成")
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee")


class HRBudget(Base):
    """人力预算"""
    __tablename__ = "hr_budgets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, comment="预算年份")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="部门")
    budget_amount = Column(Integer, default=0, comment="预算总额")
    spent_amount = Column(Integer, default=0, comment="已支出")
    category = Column(String(30), comment="类别: 薪酬/招聘/培训/福利/其他")
    description = Column(String(255), comment="说明")
    created_at = Column(DateTime, default=datetime.now)
