"""绩效管理模型"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PerformancePlan(Base):
    """绩效考核方案"""
    __tablename__ = "performance_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="方案名称")
    period = Column(String(30), comment="考核周期: 月度/季度/半年度/年度")
    year = Column(Integer, comment="考核年份")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    type = Column(String(30), default="KPI", comment="类型: KPI/OKR/360度")
    description = Column(Text, comment="方案说明")
    status = Column(String(20), default="草稿", comment="状态: 草稿/进行中/已完成")
    created_at = Column(DateTime, default=datetime.now)

    items = relationship("PerformanceItem", back_populates="plan")
    assessments = relationship("PerformanceAssessment", back_populates="plan")


class PerformanceItem(Base):
    """考核指标"""
    __tablename__ = "performance_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("performance_plans.id"), comment="所属方案")
    name = Column(String(100), nullable=False, comment="指标名称")
    description = Column(Text, comment="指标说明")
    weight = Column(Float, default=0, comment="权重(%)")
    target = Column(String(200), comment="目标值")
    sort_order = Column(Integer, default=0, comment="排序")

    plan = relationship("PerformancePlan", back_populates="items")
    scores = relationship("PerformanceScore", back_populates="item")


class PerformanceAssessment(Base):
    """考核记录"""
    __tablename__ = "performance_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("performance_plans.id"), comment="考核方案")
    employee_id = Column(Integer, ForeignKey("employees.id"), comment="被考核员工")
    evaluator_id = Column(Integer, ForeignKey("employees.id"), comment="考核人")
    total_score = Column(Float, default=0, comment="总分")
    grade = Column(String(5), comment="等级: S/A/B/C/D")
    self_review = Column(Text, comment="自评")
    evaluator_comment = Column(Text, comment="考核评语")
    status = Column(String(20), default="待考核", comment="状态: 待考核/已完成/已确认")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    plan = relationship("PerformancePlan", back_populates="assessments")
    employee = relationship("Employee", foreign_keys=[employee_id])
    evaluator = relationship("Employee", foreign_keys=[evaluator_id])
    scores = relationship("PerformanceScore", back_populates="assessment")


class PerformanceScore(Base):
    """指标评分"""
    __tablename__ = "performance_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("performance_assessments.id"), comment="考核记录ID")
    item_id = Column(Integer, ForeignKey("performance_items.id"), comment="指标ID")
    score = Column(Float, default=0, comment="得分")
    comment = Column(String(200), comment="评分说明")

    assessment = relationship("PerformanceAssessment", back_populates="scores")
    item = relationship("PerformanceItem", back_populates="scores")
