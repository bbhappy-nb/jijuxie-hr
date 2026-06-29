"""培训管理模型"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class TrainingPlan(Base):
    """培训计划"""
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="培训主题")
    type = Column(String(30), comment="类型: 新员工培训/技能提升/管理培训/外部培训/线上课程")
    trainer = Column(String(50), comment="讲师/机构")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    location = Column(String(100), comment="培训地点")
    budget = Column(Integer, default=0, comment="预算")
    actual_cost = Column(Integer, default=0, comment="实际费用")
    target_audience = Column(String(200), comment="目标学员")
    max_participants = Column(Integer, comment="人数上限")
    description = Column(Text, comment="培训内容")
    status = Column(String(20), default="计划中", comment="状态: 计划中/进行中/已完成/已取消")
    created_at = Column(DateTime, default=datetime.now)

    records = relationship("TrainingRecord", back_populates="plan")


class TrainingRecord(Base):
    """培训记录"""
    __tablename__ = "training_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id"), comment="培训计划ID")
    employee_id = Column(Integer, ForeignKey("employees.id"), comment="员工ID")
    score = Column(Integer, comment="考核分数")
    hours = Column(Integer, default=0, comment="培训学时")
    status = Column(String(20), default="已报名", comment="状态: 已报名/已参加/已完成/未通过")
    feedback = Column(Text, comment="培训反馈")
    certificate = Column(String(100), comment="获得证书")
    created_at = Column(DateTime, default=datetime.now)

    plan = relationship("TrainingPlan", back_populates="records")
    employee = relationship("Employee")
