"""PythonAnywhere 专用入口 - Flask 版本"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from app.database import init_db, SessionLocal
from app.models.employee import Employee, Department, Position, User
from app.models.recruitment import Recruitment, Candidate
from app.models.training import TrainingPlan, TrainingRecord
from app.models.performance import PerformancePlan, PerformanceItem, PerformanceAssessment, PerformanceScore, AssessmentEvaluator
from app.models.payroll import Payroll, SocialInsurance, SalaryTemplate, SalaryTemplateItem, PayrollItem, SpecialDeduction, PerformanceBonusLink
from app.models.contract import LaborContract, OnboardingRecord, ResignationRecord, HRBudget
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.services.payroll_calc import calc_payroll, calc_social_insurance, link_assessment_to_payroll
from app.services.tax_calc import calc_cumulative_tax, get_special_deductions_total
from app.services.report_service import get_dashboard_stats
from sqlalchemy import or_, func, extract
from datetime import datetime, date
from functools import wraps
from io import BytesIO
import json

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ===== 数据库初始化 =====
init_db()

with app.app_context():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(username="admin", password_hash=hash_password("admin123"), role="admin")
            db.add(admin)
            db.commit()
            print("管理员账号已创建: admin / admin123")
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"detail": "未登录"}), 401
        token = auth_header.split(" ")[1]
        db = SessionLocal()
        try:
            from jose import JWTError, jwt
            from app.config import settings
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return jsonify({"detail": "用户不存在"}), 401
            request.current_user = user
        except Exception:
            return jsonify({"detail": "Token无效"}), 401
        finally:
            db.close()
        return f(*args, **kwargs)
    return decorated


# ===== 前端静态文件 =====
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.isfile(os.path.join('static', path)):
        return send_from_directory('static', path)
    return send_from_directory('static', 'index.html')


# ===== 认证 =====
@app.post("/api/auth/login")
def login():
    data = request.get_json()
    db = next(get_db())
    user = db.query(User).filter(User.username == data["username"]).first()
    if not user or not verify_password(data["password"], user.password_hash):
        db.close()
        return jsonify({"detail": "用户名或密码错误"}), 401
    user.last_login = datetime.now()
    db.commit()
    token = create_access_token({"sub": user.username, "role": user.role})
    db.close()
    return jsonify({"access_token": token, "token_type": "bearer", "username": user.username, "role": user.role})


@app.get("/api/auth/me")
@require_auth
def me():
    user = request.current_user
    emp_name = None
    if user.employee_id:
        db = next(get_db())
        emp = db.query(Employee).filter(Employee.id == user.employee_id).first()
        emp_name = emp.name if emp else None
        db.close()
    return jsonify({"id": user.id, "username": user.username, "role": user.role, "employee_name": emp_name, "employee_id": user.employee_id})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "app": "寄居蟹一代-HR管理系统"})


# ===== 仪表盘 =====
@app.get("/api/dashboard/stats")
@require_auth
def dashboard():
    db = next(get_db())
    stats = get_dashboard_stats(db)
    db.close()
    return jsonify(stats)


# ===== 员工管理 =====
@app.get("/api/employees")
@require_auth
def list_employees():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    keyword = request.args.get("keyword")
    department_id = request.args.get("department_id", type=int)
    status = request.args.get("status")

    q = db.query(Employee)
    if keyword:
        q = q.filter(or_(Employee.name.contains(keyword), Employee.employee_no.contains(keyword), Employee.phone.contains(keyword)))
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    if status:
        q = q.filter(Employee.status == status)

    total = q.count()
    items = q.order_by(Employee.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": e.id, "employee_no": e.employee_no, "name": e.name, "gender": e.gender,
        "phone": e.phone, "email": e.email, "education": e.education,
        "department_id": e.department_id, "department_name": e.department.name if e.department else None,
        "position_id": e.position_id, "position_name": e.position.name if e.position else None,
        "status": e.status, "hire_date": str(e.hire_date) if e.hire_date else None,
        "probation_end": str(e.probation_end) if e.probation_end else None,
        "resign_date": str(e.resign_date) if e.resign_date else None,
        "base_salary": e.base_salary, "birthday": str(e.birthday) if e.birthday else None,
        "created_at": str(e.created_at) if e.created_at else None,
    } for e in items]
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.get("/api/employees/<int:emp_id>")
@require_auth
def get_employee(emp_id):
    db = next(get_db())
    e = db.query(Employee).filter(Employee.id == emp_id).first()
    if not e:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    result = {
        "id": e.id, "employee_no": e.employee_no, "name": e.name, "gender": e.gender,
        "phone": e.phone, "email": e.email, "id_card": e.id_card, "education": e.education,
        "major": e.major, "school": e.school, "address": e.address,
        "emergency_contact": e.emergency_contact, "emergency_phone": e.emergency_phone,
        "department_id": e.department_id, "department_name": e.department.name if e.department else None,
        "position_id": e.position_id, "position_name": e.position.name if e.position else None,
        "status": e.status, "hire_date": str(e.hire_date) if e.hire_date else None,
        "resign_date": str(e.resign_date) if e.resign_date else None,
        "probation_end": str(e.probation_end) if e.probation_end else None,
        "base_salary": e.base_salary, "bank_account": e.bank_account, "bank_name": e.bank_name,
        "birthday": str(e.birthday) if e.birthday else None,
        "created_at": str(e.created_at) if e.created_at else None,
        "updated_at": str(e.updated_at) if e.updated_at else None,
    }
    db.close()
    return jsonify(result)


@app.post("/api/employees")
@require_auth
def create_employee():
    db = next(get_db())
    data = request.get_json()
    exists = db.query(Employee).filter(Employee.employee_no == data["employee_no"]).first()
    if exists:
        db.close()
        return jsonify({"detail": "工号已存在"}), 400
    e = Employee(**{k: v for k, v in data.items() if k in Employee.__table__.columns.keys()})
    db.add(e)
    db.commit()
    db.refresh(e)
    db.close()
    return jsonify({"id": e.id, "message": "创建成功"})


@app.put("/api/employees/<int:emp_id>")
@require_auth
def update_employee(emp_id):
    db = next(get_db())
    e = db.query(Employee).filter(Employee.id == emp_id).first()
    if not e:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in Employee.__table__.columns.keys() and v is not None:
            setattr(e, k, v)
    e.updated_at = datetime.now()
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.delete("/api/employees/<int:emp_id>")
@require_auth
def delete_employee(emp_id):
    db = next(get_db())
    e = db.query(Employee).filter(Employee.id == emp_id).first()
    if not e:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    db.delete(e)
    db.commit()
    db.close()
    return jsonify({"message": "删除成功"})


# ===== 部门 =====
@app.get("/api/departments")
@require_auth
def list_departments():
    db = next(get_db())
    depts = db.query(Department).order_by(Department.sort_order).all()

    def build_tree(parent_id=None):
        result = []
        for d in depts:
            if d.parent_id == parent_id:
                emp_count = db.query(Employee).filter(Employee.department_id == d.id, Employee.status != "离职").count()
                result.append({
                    "id": d.id, "name": d.name, "parent_id": d.parent_id, "manager_id": d.manager_id,
                    "description": d.description, "sort_order": d.sort_order,
                    "employee_count": emp_count, "children": build_tree(d.id),
                })
        return result
    tree = build_tree(None)
    db.close()
    return jsonify(tree)


@app.post("/api/departments")
@require_auth
def create_department():
    db = next(get_db())
    data = request.get_json()
    d = Department(**{k: v for k, v in data.items() if k in Department.__table__.columns.keys()})
    db.add(d)
    db.commit()
    db.close()
    return jsonify({"id": d.id, "message": "创建成功"})


@app.put("/api/departments/<int:dept_id>")
@require_auth
def update_department(dept_id):
    db = next(get_db())
    d = db.query(Department).filter(Department.id == dept_id).first()
    if not d:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in Department.__table__.columns.keys():
            setattr(d, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.delete("/api/departments/<int:dept_id>")
@require_auth
def delete_department(dept_id):
    db = next(get_db())
    d = db.query(Department).filter(Department.id == dept_id).first()
    if not d:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    db.delete(d)
    db.commit()
    db.close()
    return jsonify({"message": "删除成功"})


# ===== 岗位 =====
@app.get("/api/positions")
@require_auth
def list_positions():
    db = next(get_db())
    dept_id = request.args.get("department_id", type=int)
    q = db.query(Position)
    if dept_id:
        q = q.filter(Position.department_id == dept_id)
    positions = q.all()
    result = [{
        "id": p.id, "name": p.name, "department_id": p.department_id,
        "department_name": p.department.name if p.department else None,
        "headcount": p.headcount, "description": p.description, "requirements": p.requirements,
        "current_count": db.query(Employee).filter(Employee.position_id == p.id, Employee.status != "离职").count(),
    } for p in positions]
    db.close()
    return jsonify(result)


@app.post("/api/positions")
@require_auth
def create_position():
    db = next(get_db())
    data = request.get_json()
    p = Position(**{k: v for k, v in data.items() if k in Position.__table__.columns.keys()})
    db.add(p)
    db.commit()
    db.close()
    return jsonify({"id": p.id, "message": "创建成功"})


# ===== 招聘 =====
@app.get("/api/recruitment/jobs")
@require_auth
def list_jobs():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    q = db.query(Recruitment)
    total = q.count()
    items = q.order_by(Recruitment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": r.id, "title": r.title, "department_id": r.department_id, "headcount": r.headcount,
        "salary_range": r.salary_range, "requirements": r.requirements, "channel": r.channel,
        "priority": r.priority, "status": r.status,
        "publish_date": str(r.publish_date) if r.publish_date else None,
        "candidate_count": db.query(Candidate).filter(Candidate.recruitment_id == r.id).count(),
        "created_at": str(r.created_at) if r.created_at else None,
    } for r in items]
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.post("/api/recruitment/jobs")
@require_auth
def create_job():
    db = next(get_db())
    data = request.get_json()
    r = Recruitment(**{k: v for k, v in data.items() if k in Recruitment.__table__.columns.keys()})
    db.add(r)
    db.commit()
    db.close()
    return jsonify({"id": r.id, "message": "创建成功"})


@app.put("/api/recruitment/jobs/<int:job_id>")
@require_auth
def update_job(job_id):
    db = next(get_db())
    r = db.query(Recruitment).filter(Recruitment.id == job_id).first()
    if not r:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in Recruitment.__table__.columns.keys():
            setattr(r, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.get("/api/recruitment/candidates")
@require_auth
def list_candidates():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    stage = request.args.get("stage")
    recruitment_id = request.args.get("recruitment_id", type=int)
    keyword = request.args.get("keyword")

    q = db.query(Candidate)
    if stage:
        q = q.filter(Candidate.stage == stage)
    if recruitment_id:
        q = q.filter(Candidate.recruitment_id == recruitment_id)
    if keyword:
        q = q.filter(or_(Candidate.name.contains(keyword), Candidate.phone.contains(keyword)))

    total = q.count()
    items = q.order_by(Candidate.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": c.id, "name": c.name, "phone": c.phone, "email": c.email, "education": c.education,
        "years_of_work": c.years_of_work, "current_company": c.current_company,
        "expected_salary": c.expected_salary, "channel": c.channel,
        "recruitment_id": c.recruitment_id,
        "recruitment_title": c.recruitment.title if c.recruitment else None,
        "stage": c.stage, "interview_date": str(c.interview_date) if c.interview_date else None,
        "interviewer": c.interviewer, "interview_feedback": c.interview_feedback,
        "offer_date": str(c.offer_date) if c.offer_date else None, "offer_salary": c.offer_salary,
        "onboard_date": str(c.onboard_date) if c.onboard_date else None,
        "remark": c.remark, "is_onboarded": c.is_onboarded,
        "created_at": str(c.created_at) if c.created_at else None,
    } for c in items]
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.post("/api/recruitment/candidates")
@require_auth
def create_candidate():
    db = next(get_db())
    data = request.get_json()
    c = Candidate(**{k: v for k, v in data.items() if k in Candidate.__table__.columns.keys()})
    db.add(c)
    db.commit()
    db.close()
    return jsonify({"id": c.id, "message": "创建成功"})


@app.put("/api/recruitment/candidates/<int:cand_id>")
@require_auth
def update_candidate(cand_id):
    db = next(get_db())
    c = db.query(Candidate).filter(Candidate.id == cand_id).first()
    if not c:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in Candidate.__table__.columns.keys():
            setattr(c, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.get("/api/recruitment/stats")
@require_auth
def recruitment_stats():
    db = next(get_db())
    channels = db.query(Candidate.channel, func.count(Candidate.id)).group_by(Candidate.channel).all()
    stages = db.query(Candidate.stage, func.count(Candidate.id)).group_by(Candidate.stage).all()
    result = {
        "by_channel": [{"name": c[0] or "未知", "value": c[1]} for c in channels],
        "by_stage": [{"name": s[0], "value": s[1]} for s in stages],
        "total_candidates": db.query(func.count(Candidate.id)).scalar() or 0,
        "total_jobs": db.query(func.count(Recruitment.id)).filter(Recruitment.status == "招聘中").scalar() or 0,
    }
    db.close()
    return jsonify(result)


# ===== 培训 =====
@app.get("/api/training/plans")
@require_auth
def list_training_plans():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    q = db.query(TrainingPlan)
    total = q.count()
    items = q.order_by(TrainingPlan.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": p.id, "title": p.title, "type": p.type, "trainer": p.trainer,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "location": p.location, "budget": p.budget, "actual_cost": p.actual_cost,
        "status": p.status, "max_participants": p.max_participants, "description": p.description,
        "participant_count": db.query(TrainingRecord).filter(TrainingRecord.plan_id == p.id).count(),
        "created_at": str(p.created_at) if p.created_at else None,
    } for p in items]
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.post("/api/training/plans")
@require_auth
def create_training_plan():
    db = next(get_db())
    data = request.get_json()
    p = TrainingPlan(**{k: v for k, v in data.items() if k in TrainingPlan.__table__.columns.keys()})
    db.add(p)
    db.commit()
    db.close()
    return jsonify({"id": p.id, "message": "创建成功"})


@app.put("/api/training/plans/<int:plan_id>")
@require_auth
def update_training_plan(plan_id):
    db = next(get_db())
    p = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not p:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in TrainingPlan.__table__.columns.keys():
            setattr(p, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.get("/api/training/records")
@require_auth
def list_training_records():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    q = db.query(TrainingRecord)
    total = q.count()
    items = q.order_by(TrainingRecord.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for r in items:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        result.append({
            "id": r.id, "plan_id": r.plan_id, "employee_id": r.employee_id,
            "employee_name": emp.name if emp else None,
            "score": r.score, "hours": r.hours, "status": r.status,
            "feedback": r.feedback, "certificate": r.certificate,
            "created_at": str(r.created_at) if r.created_at else None,
        })
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.post("/api/training/records")
@require_auth
def create_training_record():
    db = next(get_db())
    data = request.get_json()
    r = TrainingRecord(**{k: v for k, v in data.items() if k in TrainingRecord.__table__.columns.keys()})
    db.add(r)
    db.commit()
    db.close()
    return jsonify({"id": r.id, "message": "创建成功"})


@app.put("/api/training/records/<int:rec_id>")
@require_auth
def update_training_record(rec_id):
    db = next(get_db())
    r = db.query(TrainingRecord).filter(TrainingRecord.id == rec_id).first()
    if not r:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in TrainingRecord.__table__.columns.keys():
            setattr(r, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


# ===== 绩效管理 (Flask版) =====

def _apply_grading_flask(assessment_id, db):
    """Flask版重算总分和等级(使用方案自定义阈值)"""
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == assessment_id).first()
    if not a: return
    evaluators = db.query(AssessmentEvaluator).filter(
        AssessmentEvaluator.assessment_id == assessment_id, AssessmentEvaluator.status == "已完成").all()
    if evaluators:
        tw = sum(e.weight or 100 for e in evaluators)
        if tw > 0:
            a.total_score = round(sum((e.total_score or 0) * (e.weight or 100) for e in evaluators) / tw, 2)
    else:
        scores = db.query(PerformanceScore).filter(PerformanceScore.assessment_id == assessment_id).all()
        if scores:
            ss = 0
            for sc in scores:
                item = sc.item
                ss += (sc.score or 0) * (item.weight if item else 0) / 100
            a.total_score = round(ss, 2)
    plan = a.plan
    s_t = (plan.grade_s_threshold or 90) if plan else 90
    a_t = (plan.grade_a_threshold or 80) if plan else 80
    b_t = (plan.grade_b_threshold or 70) if plan else 70
    c_t = (plan.grade_c_threshold or 60) if plan else 60
    if a.total_score >= s_t: a.grade = "S"
    elif a.total_score >= a_t: a.grade = "A"
    elif a.total_score >= b_t: a.grade = "B"
    elif a.total_score >= c_t: a.grade = "C"
    else: a.grade = "D"
    a.status = "已完成"

@app.get("/api/performance/plans")
@require_auth
def list_performance_plans():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    year = request.args.get("year", type=int)
    status = request.args.get("status")
    q = db.query(PerformancePlan)
    if year: q = q.filter(PerformancePlan.year == year)
    if status: q = q.filter(PerformancePlan.status == status)
    total = q.count()
    plans = q.order_by(PerformancePlan.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": p.id, "name": p.name, "period": p.period, "year": p.year,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "type": p.type, "description": p.description, "status": p.status,
        "grade_s_threshold": p.grade_s_threshold or 90, "grade_a_threshold": p.grade_a_threshold or 80,
        "grade_b_threshold": p.grade_b_threshold or 70, "grade_c_threshold": p.grade_c_threshold or 60,
        "bonus_coefficients": p.bonus_coefficients,
        "self_review_enabled": p.self_review_enabled if p.self_review_enabled is not None else 1,
        "assessment_count": db.query(PerformanceAssessment).filter(PerformanceAssessment.plan_id == p.id).count(),
        "created_at": str(p.created_at) if p.created_at else None,
    } for p in plans]
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})

@app.post("/api/performance/plans")
@require_auth
def create_performance_plan():
    db = next(get_db())
    data = request.get_json()
    p = PerformancePlan(**{k: v for k, v in data.items() if k in PerformancePlan.__table__.columns.keys()})
    db.add(p); db.commit(); db.close()
    return jsonify({"id": p.id, "message": "创建成功"})

@app.put("/api/performance/plans/<int:plan_id>")
@require_auth
def update_performance_plan(plan_id):
    db = next(get_db())
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in PerformancePlan.__table__.columns.keys(): setattr(p, k, v)
    db.commit(); db.close()
    return jsonify({"message": "更新成功"})

@app.delete("/api/performance/plans/<int:plan_id>")
@require_auth
def delete_performance_plan(plan_id):
    db = next(get_db())
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    db.query(PerformanceScore).filter(PerformanceScore.assessment.has(PerformanceAssessment.plan_id == plan_id)).delete(synchronize_session=False)
    db.query(AssessmentEvaluator).filter(AssessmentEvaluator.assessment.has(PerformanceAssessment.plan_id == plan_id)).delete(synchronize_session=False)
    db.query(PerformanceAssessment).filter(PerformanceAssessment.plan_id == plan_id).delete()
    db.query(PerformanceItem).filter(PerformanceItem.plan_id == plan_id).delete()
    db.delete(p); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.put("/api/performance/plans/<int:plan_id>/grading")
@require_auth
def update_plan_grading(plan_id):
    db = next(get_db())
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k in ["grade_s_threshold", "grade_a_threshold", "grade_b_threshold", "grade_c_threshold", "bonus_coefficients", "self_review_enabled"]:
        if k in data: setattr(p, k, data[k])
    db.commit(); db.close()
    return jsonify({"message": "评级配置已更新"})

@app.get("/api/performance/plans/<int:plan_id>/items")
@require_auth
def list_performance_items(plan_id):
    db = next(get_db())
    items = db.query(PerformanceItem).filter(PerformanceItem.plan_id == plan_id).order_by(PerformanceItem.sort_order).all()
    result = [{"id": i.id, "plan_id": i.plan_id, "name": i.name, "description": i.description,
               "weight": i.weight, "target": i.target, "actual_value": i.actual_value,
               "scoring_method": i.scoring_method, "sort_order": i.sort_order} for i in items]
    db.close(); return jsonify(result)

@app.post("/api/performance/plans/<int:plan_id>/items")
@require_auth
def create_performance_item(plan_id):
    db = next(get_db())
    data = request.get_json()
    i = PerformanceItem(plan_id=plan_id, **{k: v for k, v in data.items() if k in PerformanceItem.__table__.columns.keys()})
    db.add(i); db.commit(); db.close()
    return jsonify({"id": i.id, "message": "创建成功"})

@app.put("/api/performance/items/<int:item_id>")
@require_auth
def update_performance_item(item_id):
    db = next(get_db())
    i = db.query(PerformanceItem).filter(PerformanceItem.id == item_id).first()
    if not i: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in PerformanceItem.__table__.columns.keys(): setattr(i, k, v)
    db.commit(); db.close()
    return jsonify({"message": "已更新"})

@app.delete("/api/performance/items/<int:item_id>")
@require_auth
def delete_performance_item(item_id):
    db = next(get_db())
    i = db.query(PerformanceItem).filter(PerformanceItem.id == item_id).first()
    if not i: db.close(); return jsonify({"detail": "不存在"}), 404
    db.query(PerformanceScore).filter(PerformanceScore.item_id == item_id).delete()
    db.delete(i); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.get("/api/performance/assessments")
@require_auth
def list_assessments():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    plan_id = request.args.get("plan_id", type=int)
    employee_id = request.args.get("employee_id", type=int)
    status = request.args.get("status")
    q = db.query(PerformanceAssessment)
    if plan_id: q = q.filter(PerformanceAssessment.plan_id == plan_id)
    if employee_id: q = q.filter(PerformanceAssessment.employee_id == employee_id)
    if status: q = q.filter(PerformanceAssessment.status == status)
    total = q.count()
    items = q.order_by(PerformanceAssessment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for a in items:
        emp = a.employee; eva = a.evaluator; plan = a.plan
        result.append({
            "id": a.id, "plan_id": a.plan_id, "plan_name": plan.name if plan else None,
            "employee_id": a.employee_id, "employee_name": emp.name if emp else None,
            "evaluator_id": a.evaluator_id, "evaluator_name": eva.name if eva else None,
            "total_score": a.total_score, "grade": a.grade,
            "self_review": a.self_review, "self_review_status": a.self_review_status,
            "evaluator_comment": a.evaluator_comment, "employee_confirmed": a.employee_confirmed,
            "status": a.status, "created_at": str(a.created_at) if a.created_at else None,
        })
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})

@app.post("/api/performance/assessments")
@require_auth
def create_assessment():
    db = next(get_db())
    data = request.get_json()
    a = PerformanceAssessment(**{k: v for k, v in data.items() if k in PerformanceAssessment.__table__.columns.keys()})
    db.add(a); db.commit(); db.close()
    return jsonify({"id": a.id, "message": "创建成功"})

@app.post("/api/performance/assessments/batch")
@require_auth
def batch_create_assessments():
    db = next(get_db())
    data = request.get_json()
    plan_id = data.get("plan_id"); department_id = data.get("department_id")
    employee_ids = data.get("employee_ids"); evaluator_id = data.get("evaluator_id")
    q = db.query(Employee).filter(Employee.status.in_(["在职", "试用期"]))
    if department_id: q = q.filter(Employee.department_id == department_id)
    if employee_ids: q = q.filter(Employee.id.in_(employee_ids))
    employees = q.all()
    count = 0
    for emp in employees:
        exists = db.query(PerformanceAssessment).filter(
            PerformanceAssessment.plan_id == plan_id, PerformanceAssessment.employee_id == emp.id).first()
        if exists: continue
        a = PerformanceAssessment(plan_id=plan_id, employee_id=emp.id, evaluator_id=evaluator_id)
        db.add(a); count += 1
    db.commit(); db.close()
    return jsonify({"message": f"已为{count}名员工创建考核记录", "count": count})

@app.put("/api/performance/assessments/<int:ass_id>")
@require_auth
def update_assessment(ass_id):
    db = next(get_db())
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in PerformanceAssessment.__table__.columns.keys(): setattr(a, k, v)
    db.commit(); db.close()
    return jsonify({"message": "更新成功"})

@app.delete("/api/performance/assessments/<int:ass_id>")
@require_auth
def delete_assessment(ass_id):
    db = next(get_db())
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a: db.close(); return jsonify({"detail": "不存在"}), 404
    db.query(PerformanceScore).filter(PerformanceScore.assessment_id == ass_id).delete()
    db.query(AssessmentEvaluator).filter(AssessmentEvaluator.assessment_id == ass_id).delete()
    db.delete(a); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.get("/api/performance/assessments/<int:ass_id>/detail")
@require_auth
def get_assessment_detail(ass_id):
    db = next(get_db())
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a: db.close(); return jsonify({"detail": "不存在"}), 404
    plan = a.plan; emp = a.employee
    scores = db.query(PerformanceScore).filter(PerformanceScore.assessment_id == ass_id).all()
    evals = db.query(AssessmentEvaluator).filter(AssessmentEvaluator.assessment_id == ass_id).all()
    db.close()
    return jsonify({
        "id": a.id, "plan": {"id": plan.id, "name": plan.name, "type": plan.type, "period": plan.period,
            "grade_s": plan.grade_s_threshold or 90, "grade_a": plan.grade_a_threshold or 80,
            "grade_b": plan.grade_b_threshold or 70, "grade_c": plan.grade_c_threshold or 60,
            "bonus_coefficients": plan.bonus_coefficients, "self_review_enabled": plan.self_review_enabled} if plan else None,
        "employee": {"id": emp.id, "name": emp.name, "department": emp.department.name if emp.department else None} if emp else None,
        "evaluator": {"id": a.evaluator_id, "name": a.evaluator.name if a.evaluator else None},
        "total_score": a.total_score, "grade": a.grade,
        "self_review": a.self_review, "self_review_status": a.self_review_status,
        "evaluator_comment": a.evaluator_comment, "employee_confirmed": a.employee_confirmed, "status": a.status,
        "scores": [{"id": s.id, "item_id": s.item_id, "item_name": s.item.name if s.item else None,
                    "score": s.score, "comment": s.comment, "weight": s.item.weight if s.item else 0} for s in scores],
        "evaluators": [{"id": e.id, "evaluator_id": e.evaluator_id, "evaluator_name": e.evaluator.name if e.evaluator else None,
                        "evaluator_type": e.evaluator_type, "weight": e.weight, "total_score": e.total_score,
                        "grade": e.grade, "comment": e.comment, "status": e.status} for e in evals],
    })

@app.put("/api/performance/assessments/<int:ass_id>/self-review")
@require_auth
def submit_self_review(ass_id):
    db = next(get_db())
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    a.self_review = data.get("self_review", a.self_review)
    a.self_review_status = "已提交"
    db.commit(); db.close()
    return jsonify({"message": "自评已提交"})

@app.put("/api/performance/assessments/<int:ass_id>/confirm")
@require_auth
def employee_confirm(ass_id):
    db = next(get_db())
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a: db.close(); return jsonify({"detail": "不存在"}), 404
    a.employee_confirmed = 1; a.confirmed_at = datetime.now(); a.status = "已确认"
    db.commit(); db.close()
    return jsonify({"message": "已确认"})

@app.post("/api/performance/assessments/<int:ass_id>/evaluators")
@require_auth
def add_evaluator(ass_id):
    db = next(get_db())
    data = request.get_json()
    e = AssessmentEvaluator(assessment_id=ass_id, **{k: v for k, v in data.items() if k in AssessmentEvaluator.__table__.columns.keys() and k != "assessment_id"})
    db.add(e); db.commit(); db.close()
    return jsonify({"id": e.id, "message": "评估人已添加"})

@app.delete("/api/performance/assessments/evaluators/<int:eval_id>")
@require_auth
def delete_evaluator(eval_id):
    db = next(get_db())
    e = db.query(AssessmentEvaluator).filter(AssessmentEvaluator.id == eval_id).first()
    if not e: db.close(); return jsonify({"detail": "不存在"}), 404
    db.delete(e); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.get("/api/performance/assessments/<int:ass_id>/evaluators")
@require_auth
def list_evaluators(ass_id):
    db = next(get_db())
    evals = db.query(AssessmentEvaluator).filter(AssessmentEvaluator.assessment_id == ass_id).all()
    db.close()
    return jsonify([{"id": e.id, "evaluator_id": e.evaluator_id, "evaluator_name": e.evaluator.name if e.evaluator else None,
                     "evaluator_type": e.evaluator_type, "weight": e.weight, "total_score": e.total_score,
                     "grade": e.grade, "comment": e.comment, "status": e.status,
                     "completed_at": str(e.completed_at) if e.completed_at else None} for e in evals])

@app.put("/api/performance/evaluators/<int:eval_id>/score")
@require_auth
def update_evaluator_score(eval_id):
    db = next(get_db())
    e = db.query(AssessmentEvaluator).filter(AssessmentEvaluator.id == eval_id).first()
    if not e: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json() or {}
    e.total_score = data.get("total_score", e.total_score)
    if data.get("grade"): e.grade = data["grade"]
    if data.get("comment"): e.comment = data["comment"]
    e.status = "已完成"; e.completed_at = datetime.now()
    db.commit()
    _apply_grading_flask(e.assessment_id, db)
    db.close()
    return jsonify({"message": "评分已更新"})

@app.post("/api/performance/scores")
@require_auth
def create_score():
    db = next(get_db())
    data = request.get_json()
    s = PerformanceScore(**{k: v for k, v in data.items() if k in PerformanceScore.__table__.columns.keys()})
    db.add(s); db.commit()
    _apply_grading_flask(data["assessment_id"], db)
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == data["assessment_id"]).first()
    db.close()
    return jsonify({"id": s.id, "message": "评分成功", "total_score": a.total_score if a else 0, "grade": a.grade if a else None})

@app.post("/api/performance/scores/batch")
@require_auth
def batch_create_scores():
    db = next(get_db())
    data = request.get_json()
    assessment_id = data.get("assessment_id")
    for sc in data.get("scores", []):
        s = PerformanceScore(assessment_id=assessment_id,
                             **{k: v for k, v in sc.items() if k in PerformanceScore.__table__.columns.keys()})
        db.add(s)
    db.commit()
    _apply_grading_flask(assessment_id, db)
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == assessment_id).first()
    db.close()
    return jsonify({"message": f"已提交{len(data.get('scores',[]))}项评分", "total_score": a.total_score if a else 0, "grade": a.grade if a else None})

@app.get("/api/performance/employee/<int:emp_id>/timeline")
@require_auth
def employee_performance_timeline(emp_id):
    db = next(get_db())
    year = request.args.get("year", type=int)
    q = db.query(PerformanceAssessment).filter(PerformanceAssessment.employee_id == emp_id)
    if year: q = q.join(PerformancePlan).filter(PerformancePlan.year == year)
    assessments = q.order_by(PerformanceAssessment.created_at.desc()).all()
    timeline = []
    for a in assessments:
        plan = a.plan
        scores = db.query(PerformanceScore).filter(PerformanceScore.assessment_id == a.id).all()
        timeline.append({"id": a.id, "plan_name": plan.name if plan else None, "period": plan.period if plan else None,
                         "type": plan.type if plan else None, "total_score": a.total_score, "grade": a.grade,
                         "status": a.status, "evaluator_comment": a.evaluator_comment,
                         "created_at": str(a.created_at) if a.created_at else None,
                         "scores": [{"item_name": s.item.name if s.item else None, "score": s.score} for s in scores]})
    latest = assessments[0] if assessments else None
    radar = []
    if latest:
        latest_scores = db.query(PerformanceScore).filter(PerformanceScore.assessment_id == latest.id).all()
        radar = [{"item_name": s.item.name if s.item else "未知", "score": s.score, "weight": s.item.weight if s.item else 0} for s in latest_scores]
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    db.close()
    return jsonify({
        "employee": {"id": emp.id, "name": emp.name, "department": emp.department.name if emp and emp.department else None} if emp else None,
        "total_assessments": len(timeline),
        "grades_summary": {"S": sum(1 for t in timeline if t["grade"]=="S"), "A": sum(1 for t in timeline if t["grade"]=="A"),
                           "B": sum(1 for t in timeline if t["grade"]=="B"), "C": sum(1 for t in timeline if t["grade"]=="C"),
                           "D": sum(1 for t in timeline if t["grade"]=="D")},
        "radar": radar, "timeline": timeline,
    })

@app.get("/api/performance/stats")
@require_auth
def performance_stats():
    db = next(get_db())
    year = request.args.get("year", type=int); plan_id = request.args.get("plan_id", type=int)
    q = db.query(PerformanceAssessment)
    if year: q = q.join(PerformancePlan).filter(PerformancePlan.year == year)
    if plan_id: q = q.filter(PerformanceAssessment.plan_id == plan_id)
    assessments = q.all()
    grade_dist = {}
    for a in assessments:
        g = a.grade or "未评级"; grade_dist[g] = grade_dist.get(g, 0) + 1
    completed = sum(1 for a in assessments if a.status in ("已完成", "已确认"))
    db.close()
    return jsonify({"grade_distribution": [{"grade": k, "count": v} for k, v in sorted(grade_dist.items())],
                    "total_assessments": len(assessments), "completed": completed,
                    "completion_rate": round(completed / max(len(assessments), 1) * 100, 1)})


# ===== 薪酬管理 (Flask版) =====

@app.get("/api/payroll/list")
@require_auth
def list_payroll():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    year = request.args.get("year", type=int); month = request.args.get("month", type=int)
    department_id = request.args.get("department_id", type=int)
    employee_id = request.args.get("employee_id", type=int)
    status = request.args.get("status"); keyword = request.args.get("keyword")
    q = db.query(Payroll).join(Employee)
    if year: q = q.filter(Payroll.year == year)
    if month: q = q.filter(Payroll.month == month)
    if department_id: q = q.filter(Employee.department_id == department_id)
    if employee_id: q = q.filter(Payroll.employee_id == employee_id)
    if status: q = q.filter(Payroll.status == status)
    if keyword: q = q.filter(Employee.name.contains(keyword))
    total = q.count()
    items = q.order_by(Payroll.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for p in items:
        emp = p.employee
        result.append({
            "id": p.id, "employee_id": p.employee_id,
            "employee_name": emp.name if emp else None,
            "department_name": emp.department.name if emp and emp.department else None,
            "department_id": emp.department_id if emp else None,
            "year": p.year, "month": p.month,
            "base_salary": p.base_salary, "performance_bonus": p.performance_bonus,
            "subsidy": p.subsidy, "overtime_pay": p.overtime_pay, "other_income": p.other_income,
            "social_insurance": p.social_insurance, "housing_fund": p.housing_fund,
            "tax": p.tax, "absence_deduction": p.absence_deduction, "other_deduction": p.other_deduction,
            "special_deduction": p.special_deduction,
            "total_income": p.total_income, "total_deduction": p.total_deduction,
            "net_salary": p.net_salary, "status": p.status, "template_id": p.template_id,
            "paid_at": str(p.paid_at) if p.paid_at else None, "remark": p.remark,
        })
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})

@app.post("/api/payroll/create")
@require_auth
def create_payroll():
    db = next(get_db())
    data = request.get_json()
    exclude = {"template_id"}
    p = Payroll(**{k: v for k, v in data.items() if k in Payroll.__table__.columns.keys() and k not in exclude})
    if data.get("template_id"): p.template_id = data["template_id"]
    db.add(p); db.flush()
    try: calc_payroll(p.employee_id, p.year, p.month, db)
    except Exception as e: db.rollback(); db.close(); return jsonify({"detail": str(e)}), 400
    db.commit(); db.close()
    return jsonify({"id": p.id, "net_salary": p.net_salary, "message": "计算完成"})

@app.put("/api/payroll/<int:payroll_id>")
@require_auth
def update_payroll(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in Payroll.__table__.columns.keys(): setattr(p, k, v)
    if data.get("status") == "已发放" and not p.paid_at: p.paid_at = datetime.now()
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit(); db.close()
    return jsonify({"net_salary": p.net_salary, "message": "更新成功"})

@app.delete("/api/payroll/<int:payroll_id>")
@require_auth
def delete_payroll(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    db.query(PayrollItem).filter(PayrollItem.payroll_id == payroll_id).delete()
    db.query(PerformanceBonusLink).filter(PerformanceBonusLink.payroll_id == payroll_id).delete()
    db.delete(p); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.put("/api/payroll/<int:payroll_id>/confirm")
@require_auth
def confirm_payroll(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    p.status = "已确认"; calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit(); db.close()
    return jsonify({"message": "已确认"})

@app.put("/api/payroll/<int:payroll_id>/pay")
@require_auth
def pay_payroll(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    if p.status != "已确认": db.close(); return jsonify({"detail": "只有已确认的工资才能发放"}), 400
    p.status = "已发放"; p.paid_at = datetime.now()
    db.commit(); db.close()
    return jsonify({"message": "已发放", "paid_at": str(p.paid_at)})

@app.post("/api/payroll/batch-generate/<int:year>/<int:month>")
@require_auth
def batch_payroll(year, month):
    db = next(get_db())
    dept_id = request.args.get("department_id", type=int)
    q = db.query(Employee).filter(Employee.status.in_(["在职", "试用期"]))
    if dept_id: q = q.filter(Employee.department_id == dept_id)
    employees = q.all()
    count = 0
    for emp in employees:
        exists = db.query(Payroll).filter(Payroll.employee_id == emp.id, Payroll.year == year, Payroll.month == month).first()
        if exists: continue
        p = Payroll(employee_id=emp.id, year=year, month=month, base_salary=emp.base_salary)
        db.add(p); db.flush(); calc_payroll(emp.id, year, month, db); count += 1
    db.commit(); db.close()
    return jsonify({"message": f"已为{count}名员工生成工资", "count": count})

@app.post("/api/payroll/batch-confirm")
@require_auth
def batch_confirm():
    db = next(get_db())
    year = request.args.get("year", type=int); month = request.args.get("month", type=int)
    dept_id = request.args.get("department_id", type=int)
    q = db.query(Payroll).join(Employee).filter(Payroll.year == year, Payroll.month == month, Payroll.status == "草稿")
    if dept_id: q = q.filter(Employee.department_id == dept_id)
    payrolls = q.all()
    for p in payrolls: p.status = "已确认"; calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit(); db.close()
    return jsonify({"message": f"已确认{len(payrolls)}条记录", "count": len(payrolls)})

@app.post("/api/payroll/batch-pay")
@require_auth
def batch_pay():
    db = next(get_db())
    year = request.args.get("year", type=int); month = request.args.get("month", type=int)
    dept_id = request.args.get("department_id", type=int)
    q = db.query(Payroll).join(Employee).filter(Payroll.year == year, Payroll.month == month, Payroll.status == "已确认")
    if dept_id: q = q.filter(Employee.department_id == dept_id)
    payrolls = q.all()
    now = datetime.now()
    for p in payrolls: p.status = "已发放"; p.paid_at = now
    db.commit(); db.close()
    return jsonify({"message": f"已发放{len(payrolls)}条记录", "count": len(payrolls)})

@app.get("/api/payroll/<int:payroll_id>/payslip")
@require_auth
def get_payslip(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    emp = p.employee
    items = db.query(PayrollItem).filter(PayrollItem.payroll_id == payroll_id).order_by(PayrollItem.sort_order).all()
    bonus_link = db.query(PerformanceBonusLink).filter(PerformanceBonusLink.payroll_id == payroll_id).first()
    assessment_info = None
    if bonus_link and bonus_link.assessment:
        a = bonus_link.assessment
        assessment_info = {"assessment_id": a.id, "grade": a.grade, "total_score": a.total_score,
                           "coefficient": bonus_link.coefficient, "bonus_amount": bonus_link.bonus_amount}
    db.close()
    return jsonify({
        "id": p.id, "employee": {"id": emp.id, "name": emp.name, "employee_no": emp.employee_no,
            "department": emp.department.name if emp.department else None,
            "position": emp.position.name if emp.position else None},
        "year": p.year, "month": p.month,
        "income_items": [{"name": "基本工资", "amount": p.base_salary or 0}, {"name": "绩效奖金", "amount": p.performance_bonus or 0},
                         {"name": "补贴", "amount": p.subsidy or 0}, {"name": "加班费", "amount": p.overtime_pay or 0},
                         {"name": "其他收入", "amount": p.other_income or 0}] +
                        [{"name": it.name, "amount": it.amount or 0, "dynamic": True} for it in items if it.type == "income"],
        "deduction_items": [{"name": "社保(个人)", "amount": p.social_insurance or 0}, {"name": "公积金(个人)", "amount": p.housing_fund or 0},
                            {"name": "个人所得税", "amount": p.tax or 0}, {"name": "缺勤扣款", "amount": p.absence_deduction or 0},
                            {"name": "其他扣款", "amount": p.other_deduction or 0}] +
                           [{"name": it.name, "amount": it.amount or 0, "dynamic": True} for it in items if it.type == "deduction"],
        "total_income": p.total_income, "total_deduction": p.total_deduction, "net_salary": p.net_salary,
        "status": p.status, "paid_at": str(p.paid_at) if p.paid_at else None, "assessment": assessment_info,
    })

@app.get("/api/payroll/export/excel")
@require_auth
def export_excel():
    import openpyxl
    db = next(get_db())
    year = request.args.get("year", type=int); month = request.args.get("month", type=int)
    dept_id = request.args.get("department_id", type=int)
    q = db.query(Payroll).join(Employee).filter(Payroll.year == year, Payroll.month == month)
    if dept_id: q = q.filter(Employee.department_id == dept_id)
    payrolls = q.order_by(Employee.department_id, Employee.employee_no).all()
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = f"{year}年{month}月工资表"
    ws.append(["工号","姓名","部门","基本工资","绩效奖金","补贴","加班费","其他收入","应发合计","社保","公积金","个税","缺勤扣款","其他扣款","专项扣除","扣款合计","实发工资","状态"])
    for p in payrolls:
        emp = p.employee
        ws.append([emp.employee_no, emp.name, emp.department.name if emp.department else "",
                   p.base_salary or 0, p.performance_bonus or 0, p.subsidy or 0, p.overtime_pay or 0, p.other_income or 0,
                   p.total_income or 0, p.social_insurance or 0, p.housing_fund or 0, p.tax or 0,
                   p.absence_deduction or 0, p.other_deduction or 0, p.special_deduction or 0,
                   p.total_deduction or 0, p.net_salary or 0, p.status])
    output = BytesIO(); wb.save(output); output.seek(0)
    db.close()
    from flask import send_file
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name=f"payroll_{year}_{month}.xlsx")

@app.get("/api/payroll/export/bank")
@require_auth
def export_bank():
    db = next(get_db())
    year = request.args.get("year", type=int); month = request.args.get("month", type=int)
    dept_id = request.args.get("department_id", type=int)
    q = db.query(Payroll).join(Employee).filter(Payroll.year == year, Payroll.month == month, Payroll.status.in_(["已确认","已发放"]))
    if dept_id: q = q.filter(Employee.department_id == dept_id)
    payrolls = q.order_by(Employee.employee_no).all()
    lines = ["姓名,银行卡号,开户行,实发金额"]
    for p in payrolls:
        emp = p.employee
        lines.append(f"{emp.name},{emp.bank_account or ''},{emp.bank_name or ''},{p.net_salary or 0}")
    output = BytesIO("\n".join(lines).encode("utf-8-sig"))
    db.close()
    from flask import send_file
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name=f"bank_{year}_{month}.csv")

@app.get("/api/payroll/employee/<int:emp_id>/history")
@require_auth
def employee_salary_history(emp_id):
    db = next(get_db())
    year = request.args.get("year", type=int)
    q = db.query(Payroll).filter(Payroll.employee_id == emp_id)
    if year: q = q.filter(Payroll.year == year)
    payrolls = q.order_by(Payroll.year.desc(), Payroll.month.desc()).all()
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    history = [{"id": p.id, "year": p.year, "month": p.month, "base_salary": p.base_salary,
                "performance_bonus": p.performance_bonus, "total_income": p.total_income,
                "total_deduction": p.total_deduction, "tax": p.tax, "net_salary": p.net_salary,
                "status": p.status, "paid_at": str(p.paid_at) if p.paid_at else None} for p in payrolls]
    trend = [{"label": f"{p.year}/{p.month:02d}", "net_salary": p.net_salary, "total_income": p.total_income}
             for p in reversed(payrolls[:24])]
    db.close()
    return jsonify({"employee": {"id": emp.id, "name": emp.name, "employee_no": emp.employee_no} if emp else None,
                    "total_records": len(history), "history": history, "trend": trend})

@app.get("/api/payroll/dashboard/department-cost")
@require_auth
def department_cost():
    db = next(get_db())
    year = request.args.get("year", type=int); month = request.args.get("month", type=int)
    results = db.query(Employee.department_id, Department.name, func.count(Payroll.id),
                       func.sum(Payroll.total_income), func.sum(Payroll.net_salary)
                       ).join(Employee).join(Department).filter(
                       Payroll.year == year, Payroll.month == month).group_by(Employee.department_id).all()
    db.close()
    return jsonify([{"department_id": r[0], "department_name": r[1], "headcount": r[2],
                     "total_income": round(float(r[3] or 0), 2), "total_net": round(float(r[4] or 0), 2)} for r in results])

@app.get("/api/payroll/dashboard/trends")
@require_auth
def payroll_trends():
    db = next(get_db())
    year = request.args.get("year", type=int)
    trends = []
    for month in range(1, 13):
        cur = db.query(func.count(Payroll.id), func.sum(Payroll.net_salary), func.sum(Payroll.total_income),
                       func.sum(Payroll.tax)).filter(Payroll.year == year, Payroll.month == month).first()
        prior = db.query(func.sum(Payroll.net_salary)).filter(Payroll.year == year - 1, Payroll.month == month).first()
        trends.append({"month": month, "label": f"{month}月", "headcount": cur[0] or 0,
                       "net_salary": round(float(cur[1] or 0), 2), "total_income": round(float(cur[2] or 0), 2),
                       "total_tax": round(float(cur[3] or 0), 2), "prior_net": round(float(prior[0] or 0), 2)})
    db.close()
    return jsonify({"year": year, "trends": trends})

@app.post("/api/payroll/<int:payroll_id>/items")
@require_auth
def add_payroll_item(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    item = PayrollItem(payroll_id=payroll_id, **{k: v for k, v in data.items() if k in PayrollItem.__table__.columns.keys()})
    db.add(item); db.flush(); calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit(); db.close()
    return jsonify({"id": item.id, "message": "已添加"})

@app.put("/api/payroll/items/<int:item_id>")
@require_auth
def update_payroll_item(item_id):
    db = next(get_db())
    item = db.query(PayrollItem).filter(PayrollItem.id == item_id).first()
    if not item: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in PayrollItem.__table__.columns.keys(): setattr(item, k, v)
    p = item.payroll; calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit(); db.close()
    return jsonify({"message": "已更新"})

@app.delete("/api/payroll/items/<int:item_id>")
@require_auth
def delete_payroll_item(item_id):
    db = next(get_db())
    item = db.query(PayrollItem).filter(PayrollItem.id == item_id).first()
    if not item: db.close(); return jsonify({"detail": "不存在"}), 404
    p = item.payroll; db.delete(item); db.flush()
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.get("/api/payroll/special-deductions")
@require_auth
def list_special_deductions():
    db = next(get_db())
    employee_id = request.args.get("employee_id", type=int); year = request.args.get("year", type=int)
    q = db.query(SpecialDeduction)
    if employee_id: q = q.filter(SpecialDeduction.employee_id == employee_id)
    if year: q = q.filter(SpecialDeduction.year == year)
    items = q.all()
    db.close()
    return jsonify([{"id": d.id, "employee_id": d.employee_id, "employee_name": d.employee.name if d.employee else None,
                     "year": d.year, "deduction_type": d.deduction_type, "amount": d.amount, "remark": d.remark} for d in items])

@app.post("/api/payroll/special-deductions")
@require_auth
def create_special_deduction():
    db = next(get_db())
    data = request.get_json()
    d = SpecialDeduction(**{k: v for k, v in data.items() if k in SpecialDeduction.__table__.columns.keys()})
    db.add(d); db.commit(); db.close()
    return jsonify({"id": d.id, "message": "创建成功"})

@app.put("/api/payroll/special-deductions/<int:ded_id>")
@require_auth
def update_special_deduction(ded_id):
    db = next(get_db())
    d = db.query(SpecialDeduction).filter(SpecialDeduction.id == ded_id).first()
    if not d: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in SpecialDeduction.__table__.columns.keys(): setattr(d, k, v)
    db.commit(); db.close()
    return jsonify({"message": "已更新"})

@app.delete("/api/payroll/special-deductions/<int:ded_id>")
@require_auth
def delete_special_deduction(ded_id):
    db = next(get_db())
    d = db.query(SpecialDeduction).filter(SpecialDeduction.id == ded_id).first()
    if not d: db.close(); return jsonify({"detail": "不存在"}), 404
    db.delete(d); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.get("/api/payroll/social-insurance")
@require_auth
def list_social_insurance():
    db = next(get_db())
    city = request.args.get("city")
    q = db.query(SocialInsurance)
    if city: q = q.filter(SocialInsurance.city == city)
    items = q.order_by(SocialInsurance.year.desc()).all()
    db.close()
    return jsonify([{"id": s.id, "city": s.city, "year": s.year,
                     "pension_base_min": s.pension_base_min, "pension_base_max": s.pension_base_max,
                     "pension_personal": s.pension_personal, "pension_company": s.pension_company,
                     "medical_base_min": s.medical_base_min, "medical_base_max": s.medical_base_max,
                     "medical_personal": s.medical_personal, "medical_company": s.medical_company,
                     "unemployment_personal": s.unemployment_personal, "unemployment_company": s.unemployment_company,
                     "injury_company": s.injury_company, "maternity_company": s.maternity_company,
                     "housing_fund_min": s.housing_fund_min, "housing_fund_max": s.housing_fund_max,
                     "housing_fund_personal": s.housing_fund_personal, "housing_fund_company": s.housing_fund_company} for s in items])

@app.post("/api/payroll/social-insurance")
@require_auth
def create_social_insurance():
    db = next(get_db())
    data = request.get_json()
    s = SocialInsurance(**{k: v for k, v in data.items() if k in SocialInsurance.__table__.columns.keys()})
    db.add(s); db.commit(); db.close()
    return jsonify({"id": s.id, "message": "创建成功"})

@app.put("/api/payroll/social-insurance/<int:si_id>")
@require_auth
def update_social_insurance(si_id):
    db = next(get_db())
    s = db.query(SocialInsurance).filter(SocialInsurance.id == si_id).first()
    if not s: db.close(); return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in SocialInsurance.__table__.columns.keys(): setattr(s, k, v)
    db.commit(); db.close()
    return jsonify({"message": "已更新"})

@app.delete("/api/payroll/social-insurance/<int:si_id>")
@require_auth
def delete_social_insurance(si_id):
    db = next(get_db())
    s = db.query(SocialInsurance).filter(SocialInsurance.id == si_id).first()
    if not s: db.close(); return jsonify({"detail": "不存在"}), 404
    db.delete(s); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.post("/api/payroll/<int:payroll_id>/link-assessment")
@require_auth
def link_assessment(payroll_id):
    db = next(get_db())
    data = request.get_json()
    try:
        result = link_assessment_to_payroll(payroll_id, data["assessment_id"], db)
        db.commit()
    except ValueError as e: db.rollback(); db.close(); return jsonify({"detail": str(e)}), 400
    db.close()
    return jsonify({"message": "关联成功", **result})

@app.get("/api/payroll/templates")
@require_auth
def list_templates():
    db = next(get_db())
    templates = db.query(SalaryTemplate).order_by(SalaryTemplate.id.desc()).all()
    db.close()
    return jsonify([{"id": t.id, "name": t.name, "description": t.description,
                     "item_count": len(t.items), "created_at": str(t.created_at) if t.created_at else None} for t in templates])

@app.post("/api/payroll/templates")
@require_auth
def create_template():
    db = next(get_db())
    data = request.get_json()
    t = SalaryTemplate(name=data.get("name"), description=data.get("description"))
    db.add(t); db.flush()
    for i, item_data in enumerate(data.get("items") or []):
        item = SalaryTemplateItem(template_id=t.id, name=item_data.get("name"), type=item_data.get("type"),
                                  is_taxable=item_data.get("is_taxable", 1), sort_order=item_data.get("sort_order", i))
        db.add(item)
    db.commit(); db.close()
    return jsonify({"id": t.id, "message": "创建成功"})

@app.delete("/api/payroll/templates/<int:template_id>")
@require_auth
def delete_template(template_id):
    db = next(get_db())
    t = db.query(SalaryTemplate).filter(SalaryTemplate.id == template_id).first()
    if not t: db.close(); return jsonify({"detail": "不存在"}), 404
    db.query(SalaryTemplateItem).filter(SalaryTemplateItem.template_id == template_id).delete()
    db.delete(t); db.commit(); db.close()
    return jsonify({"message": "已删除"})

@app.get("/api/payroll/summary")
@require_auth
def payroll_summary():
    db = next(get_db())
    year = request.args.get("year", type=int); month = request.args.get("month", type=int)
    stats = db.query(func.count(Payroll.id), func.sum(Payroll.total_income), func.sum(Payroll.total_deduction),
                     func.sum(Payroll.tax), func.sum(Payroll.social_insurance), func.sum(Payroll.housing_fund),
                     func.sum(Payroll.net_salary)).filter(Payroll.year == year, Payroll.month == month).first()
    status_stats = db.query(Payroll.status, func.count(Payroll.id)).filter(
        Payroll.year == year, Payroll.month == month).group_by(Payroll.status).all()
    db.close()
    return jsonify({"year": year, "month": month, "employee_count": stats[0] or 0,
                    "total_income": round(float(stats[1] or 0), 2), "total_deduction": round(float(stats[2] or 0), 2),
                    "total_tax": round(float(stats[3] or 0), 2), "total_social_insurance": round(float(stats[4] or 0), 2),
                    "total_housing_fund": round(float(stats[5] or 0), 2), "total_net_salary": round(float(stats[6] or 0), 2),
                    "status_breakdown": {s: c for s, c in status_stats}})


# ===== 劳动关系 =====
@app.get("/api/contracts")
@require_auth
def list_contracts():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    q = db.query(LaborContract)
    total = q.count()
    items = q.order_by(LaborContract.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for c in items:
        emp = db.query(Employee).filter(Employee.id == c.employee_id).first()
        result.append({
            "id": c.id, "employee_id": c.employee_id, "employee_name": emp.name if emp else None,
            "contract_no": c.contract_no, "type": c.type,
            "start_date": str(c.start_date) if c.start_date else None,
            "end_date": str(c.end_date) if c.end_date else None,
            "probation_months": c.probation_months, "status": c.status,
            "sign_date": str(c.sign_date) if c.sign_date else None,
            "termination_date": str(c.termination_date) if c.termination_date else None,
            "termination_reason": c.termination_reason, "remark": c.remark,
            "created_at": str(c.created_at) if c.created_at else None,
        })
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.post("/api/contracts")
@require_auth
def create_contract():
    db = next(get_db())
    data = request.get_json()
    c = LaborContract(**{k: v for k, v in data.items() if k in LaborContract.__table__.columns.keys()})
    db.add(c)
    db.commit()
    db.close()
    return jsonify({"id": c.id, "message": "创建成功"})


@app.put("/api/contracts/<int:contract_id>")
@require_auth
def update_contract(contract_id):
    db = next(get_db())
    c = db.query(LaborContract).filter(LaborContract.id == contract_id).first()
    if not c:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in LaborContract.__table__.columns.keys():
            setattr(c, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.get("/api/contracts/expiring")
@require_auth
def expiring_contracts():
    db = next(get_db())
    today = date.today()
    items = db.query(LaborContract).filter(LaborContract.status == "有效").all()
    result = []
    for c in items:
        if c.end_date:
            days_left = (c.end_date - today).days
            if 0 <= days_left <= 30:
                emp = db.query(Employee).filter(Employee.id == c.employee_id).first()
                result.append({
                    "id": c.id, "employee_name": emp.name if emp else None,
                    "contract_no": c.contract_no, "end_date": str(c.end_date), "days_left": days_left,
                })
    db.close()
    return jsonify(result)


@app.get("/api/contracts/onboarding")
@require_auth
def list_onboarding():
    db = next(get_db())
    items = db.query(OnboardingRecord).order_by(OnboardingRecord.id.desc()).all()
    result = []
    for o in items:
        emp = db.query(Employee).filter(Employee.id == o.employee_id).first()
        result.append({
            "id": o.id, "employee_id": o.employee_id, "employee_name": emp.name if emp else None,
            "onboard_date": str(o.onboard_date) if o.onboard_date else None,
            "id_card_copy": o.id_card_copy, "education_cert": o.education_cert,
            "photo": o.photo, "bank_card": o.bank_card,
            "health_check": o.health_check, "resignation_cert": o.resignation_cert,
            "signed_contract": o.signed_contract,
            "computer": o.computer, "phone_device": o.phone_device,
            "access_card": o.access_card, "office_supplies": o.office_supplies,
            "status": o.status,
        })
    db.close()
    return jsonify(result)


@app.post("/api/contracts/onboarding")
@require_auth
def create_onboarding():
    db = next(get_db())
    data = request.get_json()
    o = OnboardingRecord(**{k: v for k, v in data.items() if k in OnboardingRecord.__table__.columns.keys()})
    db.add(o)
    db.commit()
    db.close()
    return jsonify({"id": o.id, "message": "创建成功"})


@app.put("/api/contracts/onboarding/<int:rec_id>")
@require_auth
def update_onboarding(rec_id):
    db = next(get_db())
    o = db.query(OnboardingRecord).filter(OnboardingRecord.id == rec_id).first()
    if not o:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in OnboardingRecord.__table__.columns.keys():
            setattr(o, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.get("/api/contracts/resignation")
@require_auth
def list_resignation():
    db = next(get_db())
    items = db.query(ResignationRecord).order_by(ResignationRecord.id.desc()).all()
    result = []
    for r in items:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        result.append({
            "id": r.id, "employee_id": r.employee_id, "employee_name": emp.name if emp else None,
            "apply_date": str(r.apply_date) if r.apply_date else None,
            "resign_date": str(r.resign_date) if r.resign_date else None,
            "type": r.type, "reason": r.reason, "exit_interview": r.exit_interview,
            "handover_person": r.handover_person, "handover_status": r.handover_status,
            "asset_returned": r.asset_returned, "status": r.status,
            "created_at": str(r.created_at) if r.created_at else None,
        })
    db.close()
    return jsonify(result)


@app.post("/api/contracts/resignation")
@require_auth
def create_resignation():
    db = next(get_db())
    data = request.get_json()
    r = ResignationRecord(**{k: v for k, v in data.items() if k in ResignationRecord.__table__.columns.keys()})
    db.add(r)
    db.commit()
    db.close()
    return jsonify({"id": r.id, "message": "创建成功"})


@app.put("/api/contracts/resignation/<int:rec_id>")
@require_auth
def update_resignation(rec_id):
    db = next(get_db())
    r = db.query(ResignationRecord).filter(ResignationRecord.id == rec_id).first()
    if not r:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in ResignationRecord.__table__.columns.keys():
            setattr(r, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.get("/api/contracts/budget")
@require_auth
def list_budget():
    db = next(get_db())
    year = request.args.get("year", type=int)
    q = db.query(HRBudget)
    if year: q = q.filter(HRBudget.year == year)
    items = q.all()
    result = [{
        "id": b.id, "year": b.year, "department_id": b.department_id,
        "budget_amount": b.budget_amount, "spent_amount": b.spent_amount,
        "category": b.category, "description": b.description,
    } for b in items]
    db.close()
    return jsonify(result)


@app.post("/api/contracts/budget")
@require_auth
def create_budget():
    db = next(get_db())
    data = request.get_json()
    b = HRBudget(**{k: v for k, v in data.items() if k in HRBudget.__table__.columns.keys()})
    db.add(b)
    db.commit()
    db.close()
    return jsonify({"id": b.id, "message": "创建成功"})


# ===== 用户管理 =====
@app.get("/api/users")
@require_auth
def list_users():
    db = next(get_db())
    users = db.query(User).all()
    result = [{
        "id": u.id, "username": u.username, "role": u.role,
        "employee_id": u.employee_id, "is_active": u.is_active,
        "last_login": str(u.last_login) if u.last_login else None,
        "created_at": str(u.created_at) if u.created_at else None,
    } for u in users]
    db.close()
    return jsonify(result)


@app.post("/api/users")
@require_auth
def create_user():
    db = next(get_db())
    data = request.get_json()
    exists = db.query(User).filter(User.username == data["username"]).first()
    if exists:
        db.close()
        return jsonify({"detail": "用户名已存在"}), 400
    u = User(
        username=data["username"],
        password_hash=hash_password(data.get("password", "123456")),
        role=data.get("role", "user"),
        employee_id=data.get("employee_id"),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    db.close()
    return jsonify({"id": u.id, "message": "用户创建成功"})


@app.put("/api/users/<int:user_id>")
@require_auth
def update_user(user_id):
    db = next(get_db())
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    if "password" in data and data["password"]:
        u.password_hash = hash_password(data["password"])
    if "role" in data:
        u.role = data["role"]
    if "is_active" in data:
        u.is_active = data["is_active"]
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.delete("/api/users/<int:user_id>")
@require_auth
def delete_user(user_id):
    db = next(get_db())
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    if u.role == "admin":
        db.close()
        return jsonify({"detail": "不能删除管理员"}), 400
    db.delete(u)
    db.commit()
    db.close()
    return jsonify({"message": "删除成功"})


if __name__ == "__main__":
    app.run(debug=True, port=8000)
