"""招聘管理模型"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Recruitment(Base):
    """招聘需求/岗位"""
    __tablename__ = "recruitments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False, comment="招聘岗位")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="需求部门")
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True, comment="对应编制岗位")
    headcount = Column(Integer, default=1, comment="招聘人数")
    salary_range = Column(String(50), comment="薪资范围")
    requirements = Column(Text, comment="岗位要求")
    responsibilities = Column(Text, comment="岗位职责")
    channel = Column(String(50), comment="招聘渠道: 官网/Boss直聘/猎头/内推/校招")
    priority = Column(String(10), default="普通", comment="优先级: 紧急/普通/储备")
    status = Column(String(20), default="招聘中", comment="状态: 招聘中/已关闭/暂停")
    publish_date = Column(Date, comment="发布日期")
    close_date = Column(Date, comment="关闭日期")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    candidates = relationship("Candidate", back_populates="recruitment")


class Candidate(Base):
    """候选人"""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="姓名")
    gender = Column(String(4), comment="性别")
    phone = Column(String(20), comment="手机号")
    email = Column(String(100), comment="邮箱")
    education = Column(String(20), comment="学历")
    school = Column(String(100), comment="毕业院校")
    major = Column(String(100), comment="专业")
    years_of_work = Column(Integer, comment="工作年限")
    current_company = Column(String(100), comment="当前公司")
    current_position = Column(String(100), comment="当前职位")
    expected_salary = Column(String(50), comment="期望薪资")
    channel = Column(String(50), comment="来源渠道")

    # 招聘流程
    recruitment_id = Column(Integer, ForeignKey("recruitments.id"), comment="应聘岗位")
    stage = Column(String(20), default="简历筛选", comment="阶段: 简历筛选/初试/复试/终试/Offer/入职/放弃")
    interview_date = Column(Date, comment="面试日期")
    interviewer = Column(String(50), comment="面试官")
    interview_feedback = Column(Text, comment="面试评价")
    offer_date = Column(Date, comment="Offer发放日期")
    offer_salary = Column(String(50), comment="Offer薪资")
    onboard_date = Column(Date, comment="预计入职日期")
    is_onboarded = Column(Boolean, default=False, comment="是否已入职")

    resume_path = Column(String(255), comment="简历文件路径")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    recruitment = relationship("Recruitment", back_populates="candidates")
