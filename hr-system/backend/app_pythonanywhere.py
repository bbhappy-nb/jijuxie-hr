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
from app.models.performance import PerformancePlan, PerformanceItem, PerformanceAssessment, PerformanceScore
from app.models.payroll import Payroll, SocialInsurance
from app.models.contract import LaborContract, OnboardingRecord, ResignationRecord, HRBudget
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.services.payroll_calc import calc_payroll
from app.services.report_service import get_dashboard_stats
from sqlalchemy import or_, func, extract
from datetime import datetime, date
from functools import wraps
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


# ===== 绩效 =====
@app.get("/api/performance/plans")
@require_auth
def list_performance_plans():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    q = db.query(PerformancePlan)
    total = q.count()
    items = q.order_by(PerformancePlan.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = [{
        "id": p.id, "name": p.name, "period": p.period, "year": p.year,
        "start_date": str(p.start_date) if p.start_date else None,
        "end_date": str(p.end_date) if p.end_date else None,
        "type": p.type, "description": p.description, "status": p.status,
        "assessment_count": db.query(PerformanceAssessment).filter(PerformanceAssessment.plan_id == p.id).count(),
        "created_at": str(p.created_at) if p.created_at else None,
    } for p in items]
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.post("/api/performance/plans")
@require_auth
def create_performance_plan():
    db = next(get_db())
    data = request.get_json()
    p = PerformancePlan(**{k: v for k, v in data.items() if k in PerformancePlan.__table__.columns.keys()})
    db.add(p)
    db.commit()
    db.close()
    return jsonify({"id": p.id, "message": "创建成功"})


@app.put("/api/performance/plans/<int:plan_id>")
@require_auth
def update_performance_plan(plan_id):
    db = next(get_db())
    p = db.query(PerformancePlan).filter(PerformancePlan.id == plan_id).first()
    if not p:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in PerformancePlan.__table__.columns.keys():
            setattr(p, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.get("/api/performance/plans/<int:plan_id>/items")
@require_auth
def list_performance_items(plan_id):
    db = next(get_db())
    items = db.query(PerformanceItem).filter(PerformanceItem.plan_id == plan_id).order_by(PerformanceItem.sort_order).all()
    result = [{"id": i.id, "plan_id": i.plan_id, "name": i.name, "description": i.description,
               "weight": i.weight, "target": i.target, "sort_order": i.sort_order} for i in items]
    db.close()
    return jsonify(result)


@app.post("/api/performance/plans/<int:plan_id>/items")
@require_auth
def create_performance_item(plan_id):
    db = next(get_db())
    data = request.get_json()
    i = PerformanceItem(plan_id=plan_id, **{k: v for k, v in data.items() if k in PerformanceItem.__table__.columns.keys()})
    db.add(i)
    db.commit()
    db.close()
    return jsonify({"id": i.id, "message": "创建成功"})


@app.get("/api/performance/assessments")
@require_auth
def list_assessments():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    q = db.query(PerformanceAssessment)
    total = q.count()
    items = q.order_by(PerformanceAssessment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for a in items:
        emp = db.query(Employee).filter(Employee.id == a.employee_id).first()
        eva = db.query(Employee).filter(Employee.id == a.evaluator_id).first()
        result.append({
            "id": a.id, "plan_id": a.plan_id, "employee_id": a.employee_id,
            "employee_name": emp.name if emp else None,
            "evaluator_id": a.evaluator_id, "evaluator_name": eva.name if eva else None,
            "total_score": a.total_score, "grade": a.grade,
            "self_review": a.self_review, "evaluator_comment": a.evaluator_comment,
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
    db.add(a)
    db.commit()
    db.close()
    return jsonify({"id": a.id, "message": "创建成功"})


@app.put("/api/performance/assessments/<int:ass_id>")
@require_auth
def update_assessment(ass_id):
    db = next(get_db())
    a = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == ass_id).first()
    if not a:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in PerformanceAssessment.__table__.columns.keys():
            setattr(a, k, v)
    db.commit()
    db.close()
    return jsonify({"message": "更新成功"})


@app.post("/api/performance/scores")
@require_auth
def create_score():
    db = next(get_db())
    data = request.get_json()
    s = PerformanceScore(**{k: v for k, v in data.items() if k in PerformanceScore.__table__.columns.keys()})
    db.add(s)
    db.flush()

    # 重新计算总分
    assessment = db.query(PerformanceAssessment).filter(PerformanceAssessment.id == data["assessment_id"]).first()
    if assessment:
        scores = db.query(PerformanceScore).filter(PerformanceScore.assessment_id == data["assessment_id"]).all()
        score_sum = 0
        for sc in scores:
            item = db.query(PerformanceItem).filter(PerformanceItem.id == sc.item_id).first()
            weight = item.weight if item else 0
            score_sum += sc.score * weight / 100
        assessment.total_score = round(score_sum, 2)
        if score_sum >= 90: assessment.grade = "S"
        elif score_sum >= 80: assessment.grade = "A"
        elif score_sum >= 70: assessment.grade = "B"
        elif score_sum >= 60: assessment.grade = "C"
        else: assessment.grade = "D"
        assessment.status = "已完成"
    db.commit()
    db.close()
    return jsonify({"id": s.id, "message": "评分成功"})


@app.get("/api/performance/stats")
@require_auth
def performance_stats():
    db = next(get_db())
    grades = db.query(PerformanceAssessment.grade, func.count(PerformanceAssessment.id)).group_by(PerformanceAssessment.grade).all()
    result = {
        "grade_distribution": [{"grade": g[0] or "未评级", "count": g[1]} for g in grades],
        "total_assessments": sum(g[1] for g in grades),
    }
    db.close()
    return jsonify(result)


# ===== 薪酬 =====
@app.get("/api/payroll/list")
@require_auth
def list_payroll():
    db = next(get_db())
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    department_id = request.args.get("department_id", type=int)

    q = db.query(Payroll).join(Employee)
    if year: q = q.filter(Payroll.year == year)
    if month: q = q.filter(Payroll.month == month)
    if department_id: q = q.filter(Employee.department_id == department_id)

    total = q.count()
    items = q.order_by(Payroll.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for p in items:
        emp = db.query(Employee).filter(Employee.id == p.employee_id).first()
        result.append({
            "id": p.id, "employee_id": p.employee_id,
            "employee_name": emp.name if emp else None,
            "department_name": emp.department.name if emp and emp.department else None,
            "year": p.year, "month": p.month,
            "base_salary": p.base_salary, "performance_bonus": p.performance_bonus,
            "subsidy": p.subsidy, "overtime_pay": p.overtime_pay, "other_income": p.other_income,
            "social_insurance": p.social_insurance, "housing_fund": p.housing_fund,
            "tax": p.tax, "absence_deduction": p.absence_deduction, "other_deduction": p.other_deduction,
            "total_income": p.total_income, "total_deduction": p.total_deduction,
            "net_salary": p.net_salary, "status": p.status, "remark": p.remark,
        })
    db.close()
    return jsonify({"total": total, "page": page, "page_size": page_size, "items": result})


@app.post("/api/payroll/create")
@require_auth
def create_payroll():
    db = next(get_db())
    data = request.get_json()
    p = Payroll(**{k: v for k, v in data.items() if k in Payroll.__table__.columns.keys()})
    db.add(p)
    db.flush()
    try: calc_payroll(p.employee_id, p.year, p.month, db)
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({"detail": str(e)}), 400
    db.commit()
    db.close()
    return jsonify({"id": p.id, "net_salary": p.net_salary, "message": "计算完成"})


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
        db.add(p)
        db.flush()
        calc_payroll(emp.id, year, month, db)
        count += 1
    db.commit()
    db.close()
    return jsonify({"message": f"已为{count}名员工生成工资", "count": count})


@app.put("/api/payroll/<int:payroll_id>")
@require_auth
def update_payroll(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    data = request.get_json()
    for k, v in data.items():
        if k in Payroll.__table__.columns.keys():
            setattr(p, k, v)
    calc_payroll(p.employee_id, p.year, p.month, db)
    db.commit()
    db.close()
    return jsonify({"net_salary": p.net_salary, "message": "更新成功"})


@app.put("/api/payroll/<int:payroll_id>/confirm")
@require_auth
def confirm_payroll(payroll_id):
    db = next(get_db())
    p = db.query(Payroll).filter(Payroll.id == payroll_id).first()
    if not p:
        db.close()
        return jsonify({"detail": "不存在"}), 404
    p.status = "已确认"
    db.commit()
    db.close()
    return jsonify({"message": "已确认"})


@app.get("/api/payroll/summary")
@require_auth
def payroll_summary():
    db = next(get_db())
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    stats = db.query(
        func.count(Payroll.id), func.sum(Payroll.total_income), func.sum(Payroll.total_deduction),
        func.sum(Payroll.tax), func.sum(Payroll.social_insurance), func.sum(Payroll.housing_fund),
        func.sum(Payroll.net_salary),
    ).filter(Payroll.year == year, Payroll.month == month).first()
    db.close()
    return jsonify({
        "year": year, "month": month,
        "employee_count": stats[0] or 0,
        "total_income": round(float(stats[1] or 0), 2),
        "total_deduction": round(float(stats[2] or 0), 2),
        "total_tax": round(float(stats[3] or 0), 2),
        "total_social_insurance": round(float(stats[4] or 0), 2),
        "total_housing_fund": round(float(stats[5] or 0), 2),
        "total_net_salary": round(float(stats[6] or 0), 2),
    })


@app.get("/api/payroll/social-insurance")
@require_auth
def list_social_insurance():
    db = next(get_db())
    items = db.query(SocialInsurance).all()
    result = [{
        "id": s.id, "city": s.city, "year": s.year,
        "pension_base_min": s.pension_base_min, "pension_base_max": s.pension_base_max,
        "pension_personal": s.pension_personal, "pension_company": s.pension_company,
        "medical_base_min": s.medical_base_min, "medical_base_max": s.medical_base_max,
        "medical_personal": s.medical_personal, "medical_company": s.medical_company,
        "unemployment_personal": s.unemployment_personal, "unemployment_company": s.unemployment_company,
        "injury_company": s.injury_company, "maternity_company": s.maternity_company,
        "housing_fund_min": s.housing_fund_min, "housing_fund_max": s.housing_fund_max,
        "housing_fund_personal": s.housing_fund_personal, "housing_fund_company": s.housing_fund_company,
    } for s in items]
    db.close()
    return jsonify(result)


@app.post("/api/payroll/social-insurance")
@require_auth
def create_social_insurance():
    db = next(get_db())
    data = request.get_json()
    s = SocialInsurance(**{k: v for k, v in data.items() if k in SocialInsurance.__table__.columns.keys()})
    db.add(s)
    db.commit()
    db.close()
    return jsonify({"id": s.id, "message": "创建成功"})


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
