# 寄居蟹一代 - 人力资源管理系统

覆盖人力资源管理六大模块的专业级 Web 管理系统。

## 功能模块

| 模块 | 功能 |
|------|------|
| 🏠 **工作台** | 员工统计、部门分布、薪酬趋势、待办提醒 |
| 👥 **员工档案** | 员工信息CRUD、批量导入导出、详情查看 |
| 🏢 **人力资源规划** | 组织架构树图、岗位编制管理、人力预算 |
| 💼 **招聘管理** | 招聘岗位发布、候选人跟踪、渠道分析 |
| 📚 **培训管理** | 培训计划、培训记录、学分统计 |
| 🏆 **绩效管理** | KPI/OKR考核方案、评分、等级分布 |
| 💰 **薪酬管理** | 工资计算、个税社保、批量生成工资条 |
| 📝 **劳动关系** | 劳动合同、入离职手续、合同到期提醒 |
| ⚙️ **系统设置** | 用户权限、密码修改 |

## 技术栈

- **前端**: React 18 + TypeScript + Ant Design 5 + ECharts
- **后端**: Python FastAPI + SQLAlchemy + SQLite
- **部署**: Docker + Nginx

## 快速启动

### 本地开发

```bash
# 1. 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. 启动前端
cd frontend
npm install
npm run dev

# 3. 打开浏览器访问
# 前端: http://localhost:5173
# 后端API文档: http://localhost:8000/docs
```

### Docker 部署

```bash
# 一键启动
docker-compose up -d

# 访问 http://localhost
```

### 默认管理员账号

- 用户名: `admin`
- 密码: `admin123`

## API 文档

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 文档。

## 项目结构

```
hr-system/
├── backend/                # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py        # 应用入口
│   │   ├── config.py      # 配置
│   │   ├── database.py    # 数据库
│   │   ├── auth.py        # JWT认证
│   │   ├── models/        # 数据模型
│   │   ├── routers/       # API路由
│   │   ├── services/      # 业务逻辑
│   │   └── schemas/       # 数据校验
│   └── requirements.txt
├── frontend/               # React 前端
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── services/      # API调用
│   │   └── stores/        # 状态管理
│   └── vite.config.ts
└── docker-compose.yml      # Docker编排
```
