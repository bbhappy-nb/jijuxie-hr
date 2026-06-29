"""员工基础信息模型"""
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class Gender(str, enum.Enum):
    MALE = "男"
    FEMALE = "女"


class Education(str, enum.Enum):
    HIGH_SCHOOL = "高中及以下"
    ASSOCIATE = "大专"
    BACHELOR = "本科"
    MASTER = "硕士"
    DOCTOR = "博士"


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "在职"
    PROBATION = "试用期"
    RESIGNED = "离职"
    SUSPENDED = "停薪留职"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_no = Column(String(20), unique=True, nullable=False, comment="工号")
    name = Column(String(50), nullable=False, comment="姓名")
    gender = Column(String(4), default=Gender.MALE.value, comment="性别")
    birthday = Column(Date, comment="出生日期")
    phone = Column(String(20), comment="手机号")
    email = Column(String(100), comment="邮箱")
    id_card = Column(String(18), comment="身份证号")
    education = Column(String(20), default=Education.BACHELOR.value, comment="学历")
    major = Column(String(100), comment="专业")
    school = Column(String(100), comment="毕业院校")
    address = Column(String(255), comment="现住址")
    emergency_contact = Column(String(50), comment="紧急联系人")
    emergency_phone = Column(String(20), comment="紧急联系电话")

    # 工作信息
    department_id = Column(Integer, ForeignKey("departments.id"), comment="部门ID")
    position_id = Column(Integer, ForeignKey("positions.id"), comment="岗位ID")
    status = Column(String(10), default=EmployeeStatus.ACTIVE.value, comment="员工状态")
    hire_date = Column(Date, comment="入职日期")
    resign_date = Column(Date, comment="离职日期")
    probation_end = Column(Date, comment="转正日期")

    # 薪酬信息
    base_salary = Column(Integer, default=0, comment="基本工资")
    bank_account = Column(String(30), comment="银行卡号")
    bank_name = Column(String(50), comment="开户行")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    position = relationship("Position", back_populates="employees", foreign_keys=[position_id])


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="部门名称")
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="上级部门ID")
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True, comment="部门负责人ID")
    description = Column(String(255), comment="部门描述")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, default=datetime.now)

    employees = relationship("Employee", back_populates="department", foreign_keys="[Employee.department_id]")
    children = relationship("Department", backref="parent", remote_side=[id])
    positions = relationship("Position", back_populates="department")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="岗位名称")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="所属部门")
    headcount = Column(Integer, default=1, comment="编制人数")
    description = Column(String(500), comment="岗位职责")
    requirements = Column(String(500), comment="任职要求")
    created_at = Column(DateTime, default=datetime.now)

    department = relationship("Department", back_populates="positions")
    employees = relationship("Employee", back_populates="position", foreign_keys="[Employee.position_id]")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True, comment="关联员工")
    role = Column(String(20), default="user", comment="角色: admin/manager/user/viewer")
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_login = Column(DateTime, comment="最后登录时间")
    created_at = Column(DateTime, default=datetime.now)
