"""FastAPI 应用主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.config import settings
from app.database import init_db
from app.routers import (
    auth, employees, recruitment, training,
    performance, payroll, contracts, dashboard,
)

app = FastAPI(
    title=f"{settings.APP_NAME} API",
    version=settings.APP_VERSION,
    description="寄居蟹一代 - 人力资源管理系统",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(recruitment.router)
app.include_router(training.router)
app.include_router(performance.router)
app.include_router(payroll.router)
app.include_router(contracts.router)
app.include_router(dashboard.router)

# 上传目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# 前端静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
HAS_STATIC = os.path.exists(STATIC_DIR)


@app.on_event("startup")
def startup():
    init_db()
    # 初始化默认管理员账号
    from app.database import SessionLocal
    from app.models.employee import User
    from app.auth import hash_password

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("默认管理员账号已创建: admin / admin123")
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# ===== 前端 SPA 托管（生产模式）=====
if HAS_STATIC:
    # 挂载静态资源 (js/css/assets)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str = ""):
        """所有非 API 路径返回 index.html（SPA 路由）"""
        file_path = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "message": "开发模式 - 前端请运行 npm run dev",
            "docs": "/docs",
        }
