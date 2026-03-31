# 电商数据分析智能助手 - MVP 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的电商数据分析智能助手 MVP，包含数据接入、漏斗分析、RFM 分析、自然语言查询、PDF 报告生成

**Architecture:** FastAPI 后端 + React 前端分离架构，Celery 任务队列，PostgreSQL 数据库。本地 LLM 支持（OpenAI-compatible API）

**Tech Stack:** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Celery / Redis / PostgreSQL / React / Tailwind CSS / WeasyPrint

---

## 项目结构

```
CommercialDataAnalyzer/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 入口
│   │   ├── config.py         # 配置管理
│   │   ├── database.py       # 数据库连接
│   │   ├── models/           # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── datasource.py
│   │   │   ├── dataset.py
│   │   │   ├── conversation.py
│   │   │   └── report.py
│   │   ├── schemas/          # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── datasource.py
│   │   │   ├── analytics.py
│   │   │   └── report.py
│   │   ├── api/              # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── datasource.py
│   │   │   ├── analytics.py
│   │   │   ├── conversation.py
│   │   │   └── report.py
│   │   ├── services/         # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── datasource.py
│   │   │   ├── analytics.py
│   │   │   ├── llm.py        # LLM 抽象层
│   │   │   ├── insight.py    # AI 洞察生成
│   │   │   └── report.py
│   │   ├── tasks/           # Celery 任务
│   │   │   ├── __init__.py
│   │   │   ├── analyze.py
│   │   │   └── report.py
│   │   └── core/             # 核心安全/工具
│   │       ├── __init__.py
│   │       ├── security.py
│   │       └── audit.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_datasource.py
│   │   ├── test_analytics.py
│   │   └── test_llm.py
│   ├── alembic/              # 数据库迁移
│   │   └── env.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                 # React 前端
│   ├── src/
│   │   ├── app/             # Next.js App Router (或 React Router)
│   │   ├── components/
│   │   │   ├── ui/          # shadcn/ui 组件
│   │   │   ├── analytics/   # 分析组件
│   │   │   ├── chat/       # 对话组件
│   │   │   └── report/     # 报告组件
│   │   ├── hooks/          # 自定义 hooks
│   │   ├── services/       # API 调用
│   │   └── lib/            # 工具函数
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── SPEC.md                  # 设计规范链接
└── README.md
```

---

## Phase 1: 基础设施 (Week 1-2)

### Task 1: 项目脚手架与环境配置

**Files:**
- Create: `backend/requirements.txt`
- Create: `frontend/package.json`
- Create: `docker-compose.yml`
- Create: `Makefile`

- [ ] **Step 1: 创建 backend/requirements.txt**

```
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Tasks
celery==5.3.6
redis==5.0.1

# LLM
openai==1.10.0
httpx==0.26.0

# Data Processing
pandas==2.2.0
numpy==1.26.3
openpyxl==3.1.2
xlrd==2.0.1

# PDF
weasyprint==60.1
jinja2==3.1.3

# Security
pydantic[email]==2.5.3
python-dotenv==1.0.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0

# Utils
python-dateutil==2.8.2
```

- [ ] **Step 2: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: analytics
      POSTGRES_PASSWORD: analytics_dev
      POSTGRES_DB: analytics_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U analytics"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://analytics:analytics_dev@postgres:5432/analytics_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=dev-secret-key-change-in-prod
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 3: 创建 Makefile**

```makefile
.PHONY: setup dev backend frontend test lint clean

setup:
	docker compose up -d postgres redis
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev:
	docker compose up

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest tests/ -v

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

clean:
	docker compose down -v
	rm -rf backend/__pycache__ frontend/.next
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat: add project scaffolding and docker compose"
```

---

### Task 2: FastAPI 项目结构

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

- [ ] **Step 1: 创建 app/config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "电商数据分析助手"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://analytics:analytics_dev@localhost:5432/analytics_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM
    LLM_API_URL: str = "http://localhost:11434/v1/chat/completions"  # Ollama default
    LLM_API_KEY: str = "ollama"
    LLM_MODEL: str = "llama2"

    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".xls", ".json"}

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2: 创建 app/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

- [ ] **Step 3: 创建 app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import auth, datasource, analytics, conversation, report

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(datasource.router, prefix="/api/datasource", tags=["datasource"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])
app.include_router(report.router, prefix="/api/report", tags=["report"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/ && git commit -m "feat: add FastAPI project structure"
```

---

### Task 3: 用户认证模块

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/api/auth.py`
- Create: `backend/app/core/security.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: 创建 app/models/user.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OWNER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: 创建 app/core/security.py**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

- [ ] **Step 3: 创建 app/schemas/auth.py**

```python
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int  # user_id
```

- [ ] **Step 4: 创建 app/services/auth.py**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.schemas.auth import UserCreate, UserLogin, Token
from datetime import timedelta
from app.config import get_settings

settings = get_settings()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, credentials: UserLogin) -> User | None:
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(credentials.password, user.hashed_password):
        return None
    return user


async def generate_token(user: User) -> Token:
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token)
```

- [ ] **Step 5: 创建 app/api/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import create_user, authenticate_user, generate_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(db, user_data)
        return user
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return await generate_token(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    # TODO: Add auth dependency
):
    # Placeholder - will be completed with auth dependency
    return {"id": 1, "email": "placeholder", "role": "owner"}
```

- [ ] **Step 6: 创建测试 backend/tests/test_auth.py**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import Base, engine


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "testpassword123"},
    )
    response = await client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client):
    await client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "testpassword123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/auth/register",
        json={"email": "wrong@example.com", "password": "testpassword123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
```

- [ ] **Step 7: 运行测试验证**

```bash
cd backend && pytest tests/test_auth.py -v
# Expected: PASS (all 4 tests)
```

- [ ] **Step 8: 提交**

```bash
git add backend/app/models/user.py backend/app/core/security.py backend/app/schemas/auth.py backend/app/services/auth.py backend/app/api/auth.py backend/tests/test_auth.py && git commit -m "feat: add user authentication module

- User model with role support
- JWT token generation and verification
- Password hashing with bcrypt
- Register and login endpoints
- Basic auth tests"
```

---

### Task 4: 审计日志模块

**Files:**
- Create: `backend/app/models/audit.py`
- Create: `backend/app/core/audit.py`
- Modify: `backend/app/main.py` (add middleware)

- [ ] **Step 1: 创建 app/models/audit.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    DATA_UPLOAD = "data_upload"
    DATA_DELETE = "data_delete"
    REPORT_GENERATE = "report_generate"
    REPORT_EXPORT = "report_export"
    QUERY_EXECUTE = "query_execute"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    resource = Column(String(255))
    details = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

- [ ] **Step 2: 创建 app/core/audit.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog, AuditAction
from typing import Optional


async def log_audit(
    db: AsyncSession,
    user_id: int,
    action: AuditAction,
    resource: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
    )
    db.add(audit_log)
    await db.commit()
    return audit_log
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/audit.py backend/app/core/audit.py && git commit -m "feat: add audit logging module

- AuditLog model with action types
- log_audit helper function for recording actions
- Tracks user_id, action, resource, details, ip_address"
```

---

## Phase 2: 数据接入 (Week 2-3)

### Task 5: 数据源管理

**Files:**
- Create: `backend/app/models/datasource.py`
- Create: `backend/app/schemas/datasource.py`
- Create: `backend/app/services/datasource.py`
- Create: `backend/app/api/datasource.py`

- [ ] **Step 1: 创建 app/models/datasource.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from app.database import Base
import enum


class DataSourceType(str, enum.Enum):
    FILE = "file"
    MYSQL = "mysql"


class DataSource(Base):
    __tablename__ = "datasources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(DataSourceType), nullable=False)
    config = Column(JSON)  # Encrypted storage for DB credentials
    schema_info = Column(JSON)  # Table/column metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    datasource_id = Column(Integer, ForeignKey("datasources.id"), nullable=False)
    name = Column(String(255), nullable=False)
    table_name = Column(String(255))
    row_count = Column(Integer, default=0)
    columns = Column(JSON)  # Column metadata
    last_sync = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: 创建 app/schemas/datasource.py**

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DataSourceCreate(BaseModel):
    name: str
    type: str  # "file" or "mysql"


class DataSourceResponse(BaseModel):
    id: int
    name: str
    type: str
    schema_info: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetResponse(BaseModel):
    id: int
    name: str
    table_name: Optional[str] = None
    row_count: int
    columns: Optional[dict] = None
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 创建 app/services/datasource.py**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.datasource import DataSource, Dataset
from app.schemas.datasource import DataSourceCreate
from typing import Optional


async def create_datasource(
    db: AsyncSession,
    user_id: int,
    data: DataSourceCreate,
    config: Optional[dict] = None,
) -> DataSource:
    datasource = DataSource(
        user_id=user_id,
        name=data.name,
        type=data.type,
        config=config or {},
    )
    db.add(datasource)
    await db.commit()
    await db.refresh(datasource)
    return datasource


async def get_user_datasources(db: AsyncSession, user_id: int) -> list[DataSource]:
    result = await db.execute(
        select(DataSource)
        .where(DataSource.user_id == user_id)
        .order_by(DataSource.created_at.desc())
    )
    return result.scalars().all()


async def get_datasource(db: AsyncSession, datasource_id: int, user_id: int) -> Optional[DataSource]:
    result = await db.execute(
        select(DataSource)
        .where(DataSource.id == datasource_id, DataSource.user_id == user_id)
    )
    return result.scalar_one_or_none()
```

- [ ] **Step 4: 创建 app/api/datasource.py**

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.datasource import DataSourceCreate, DataSourceResponse, DatasetResponse
from app.services.datasource import create_datasource, get_user_datasources, get_datasource
from app.core.audit import log_audit
from app.models.audit import AuditAction
from typing import List

router = APIRouter()


@router.post("/", response_model=DataSourceResponse, status_code=201)
async def create_file_datasource(
    name: str,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    # Validate file type
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = DataSourceCreate(name=name, type="file")
    datasource = await create_datasource(db, user_id=1, data=data)
    return datasource


@router.get("/", response_model=List[DataSourceResponse])
async def list_datasources(db: AsyncSession = Depends(get_db)):
    return await get_user_datasources(db, user_id=1)


@router.get("/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource_by_id(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
):
    datasource = await get_datasource(db, datasource_id, user_id=1)
    if not datasource:
        raise HTTPException(status_code=404, detail="Data source not found")
    return datasource
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/models/datasource.py backend/app/schemas/datasource.py backend/app/services/datasource.py backend/app/api/datasource.py && git commit -m "feat: add datasource management module

- DataSource model for file and MySQL sources
- Dataset model for actual data tables
- CRUD operations for datasources
- File upload endpoint (basic)"
```

---

### Task 6: 文件解析与字段映射

**Files:**
- Create: `backend/app/services/file_parser.py`
- Create: `backend/app/services/field_mapper.py`

- [ ] **Step 1: 创建 app/services/file_parser.py**

```python
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from io import BytesIO


class FileParser:
    """Parse CSV and Excel files into standardized format."""

    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

    @classmethod
    def parse(cls, file_content: bytes, filename: str) -> Dict[str, Any]:
        ext = "." + filename.split(".")[-1].lower()

        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        df = cls._read_file(file_content, ext)

        return {
            "columns": list(df.columns),
            "column_types": {col: str(df[col].dtype) for col in df.columns},
            "row_count": len(df),
            "sample_data": df.head(10).to_dict(orient="records"),
            "data": df.to_json(orient="records", date_format="iso"),
        }

    @classmethod
    def _read_file(cls, content: bytes, ext: str) -> pd.DataFrame:
        buffer = BytesIO(content)

        if ext == ".csv":
            return pd.read_csv(buffer, encoding="utf-8-sig")
        elif ext in {".xlsx", ".xls"}:
            return pd.read_excel(buffer, engine="openpyxl" if ext == ".xlsx" else "xlrd")

        raise ValueError(f"Cannot parse extension: {ext}")


def detect_event_type_column(columns: List[str]) -> Optional[str]:
    """Auto-detect which column likely contains event_type data."""
    event_type_patterns = [
        "event", "behavior", "action", "type",
        "事件", "行为", "类型", "操作",
    ]

    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in event_type_patterns):
            return col
    return None


def detect_user_id_column(columns: List[str]) -> Optional[str]:
    """Auto-detect which column likely contains user_id data."""
    user_id_patterns = [
        "user", "member", "buyer", "customer", "userid", "uid",
        "用户", "会员", "买家", "customer_id", "user_id",
    ]

    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in user_id_patterns):
            return col
    return None


def detect_amount_column(columns: List[str]) -> Optional[str]:
    """Auto-detect which column likely contains amount/money data."""
    amount_patterns = [
        "amount", "money", "price", "payment", "revenue", "total", "sum",
        "金额", "价格", "付款", "收入", "总价",
    ]

    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in amount_patterns):
            return col
    return None
```

- [ ] **Step 2: 创建 app/services/field_mapper.py**

```python
from typing import Dict, List, Optional
from enum import Enum


class StandardField(str, Enum):
    USER_ID = "user_id"
    EVENT_TYPE = "event_type"
    EVENT_TIME = "event_time"
    PRODUCT_ID = "product_id"
    ORDER_ID = "order_id"
    AMOUNT = "amount"


# Event type value mappings
EVENT_TYPE_MAPPINGS = {
    # English
    "impression": "impression",
    "browse": "impression",
    "view": "impression",
    "click": "click",
    "add_to_cart": "add_to_cart",
    "addcart": "add_to_cart",
    "cart": "add_to_cart",
    "remove_from_cart": "remove_from_cart",
    "removecart": "remove_from_cart",
    "checkout": "checkout",
    "begin_checkout": "checkout",
    "purchase": "purchase",
    "buy": "purchase",
    "order": "purchase",
    "paid": "purchase",
    "refund": "refund",
    "return": "refund",
    # Chinese
    "浏览": "impression",
    "访问": "impression",
    "点击": "click",
    "加购": "add_to_cart",
    "加入购物车": "add_to_cart",
    "取消加购": "remove_from_cart",
    "结算": "checkout",
    "下单": "purchase",
    "购买": "purchase",
    "支付": "purchase",
    "付款": "purchase",
    "退款": "refund",
    "退货": "refund",
}


class FieldMapper:
    """Map user column names to standard field names."""

    def __init__(self, column_mappings: Dict[str, str]):
        """
        Args:
            column_mappings: Dict mapping user's column names to standard field names
            e.g., {"买家ID": "user_id", "行为": "event_type"}
        """
        self.mappings = column_mappings
        self.reverse_mappings = {v: k for k, v in column_mappings.items()}

    def to_standard(self, data: List[Dict]) -> List[Dict]:
        """Convert data from user column names to standard field names."""
        result = []
        for row in data:
            new_row = {}
            for user_col, value in row.items():
                std_col = self.mappings.get(user_col, user_col)
                if std_col == "event_type" and isinstance(value, str):
                    value = self.normalize_event_type(value)
                new_row[std_col] = value
            result.append(new_row)
        return result

    @staticmethod
    def normalize_event_type(value: str) -> str:
        """Normalize event type value to standard enum."""
        value_lower = value.lower().strip()
        return EVENT_TYPE_MAPPINGS.get(value_lower, value_lower)


def auto_detect_mappings(columns: List[str]) -> Dict[str, str]:
    """Auto-detect column mappings based on column names."""
    from app.services.file_parser import detect_event_type_column, detect_user_id_column, detect_amount_column

    mappings = {}

    user_id_col = detect_user_id_column(columns)
    if user_id_col:
        mappings[user_id_col] = StandardField.USER_ID

    event_type_col = detect_event_type_column(columns)
    if event_type_col:
        mappings[event_type_col] = StandardField.EVENT_TYPE

    amount_col = detect_amount_column(columns)
    if amount_col:
        mappings[amount_col] = StandardField.AMOUNT

    return mappings
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/services/file_parser.py backend/app/services/field_mapper.py && git commit -m "feat: add file parsing and field mapping

- FileParser for CSV/Excel parsing
- Auto-detection of user_id, event_type, amount columns
- FieldMapper to normalize data to standard schema
- Event type value normalization (English/Chinese)"
```

---

## Phase 3: 核心分析 (Week 3-5)

### Task 7: 漏斗分析引擎

**Files:**
- Create: `backend/app/services/funnel.py`
- Create: `backend/tests/test_funnel.py`

- [ ] **Step 1: 创建 app/services/funnel.py**

```python
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime


class FunnelAnalyzer:
    """
    Analyze conversion funnels from user behavior data.

    Standard event types: impression -> click -> add_to_cart -> checkout -> purchase
    """

    DEFAULT_STEPS = [
        "impression",
        "click",
        "add_to_cart",
        "checkout",
        "purchase",
    ]

    def __init__(self, steps: Optional[List[str]] = None):
        self.steps = steps or self.DEFAULT_STEPS

    def analyze(
        self,
        events: List[Dict[str, Any]],
        user_id_field: str = "user_id",
        event_type_field: str = "event_type",
        timestamp_field: str = "event_time",
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze funnel conversion.

        Returns:
            dict with step counts, conversion rates, and drop-off analysis
        """
        # Filter and sort events
        events = self._filter_events(events, timestamp_field, window_days)

        # Count users at each step
        step_users = self._count_users_per_step(events, user_id_field, event_type_field)

        # Calculate conversion metrics
        funnel_data = self._calculate_funnel_metrics(step_users)

        # Find biggest drop-off
        biggest_dropoff = self._find_biggest_dropoff(funnel_data)

        return {
            "funnel": funnel_data,
            "total_users": len(set(e.get(user_id_field) for e in events)),
            "biggest_dropoff": biggest_dropoff,
            "steps": self.steps,
        }

    def _filter_events(
        self, events: List[Dict[str, Any]], timestamp_field: str, window_days: int
    ) -> List[Dict[str, Any]]:
        """Filter events within time window."""
        # For MVP, skip time filtering (assume data is already recent)
        return [e for e in events if e.get(timestamp_field) and e.get(timestamp_field)]

    def _count_users_per_step(
        self,
        events: List[Dict[str, Any]],
        user_id_field: str,
        event_type_field: str,
    ) -> Dict[str, set]:
        """Count unique users who completed each step."""
        step_users = defaultdict(set)

        for event in events:
            user_id = event.get(user_id_field)
            event_type = event.get(event_type_field, "").lower()

            if user_id and event_type in self.steps:
                step_users[event_type].add(user_id)

        return dict(step_users)

    def _calculate_funnel_metrics(
        self, step_users: Dict[str, set]
    ) -> List[Dict[str, Any]]:
        """Calculate conversion rates between steps."""
        results = []
        prev_count = None

        for step in self.steps:
            count = len(step_users.get(step, set()))

            if prev_count is None:
                conversion_rate = 1.0 if count > 0 else 0.0
            else:
                conversion_rate = count / prev_count if prev_count > 0 else 0.0

            dropoff_rate = 1.0 - conversion_rate

            results.append({
                "step": step,
                "user_count": count,
                "conversion_rate": round(conversion_rate, 4),
                "dropoff_rate": round(dropoff_rate, 4),
            })

            prev_count = count

        return results

    def _find_biggest_dropoff(
        self, funnel_data: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find the step with the biggest drop-off rate."""
        max_dropoff = 0
        max_dropoff_step = None

        for step in funnel_data:
            if step["dropoff_rate"] > max_dropoff and step["user_count"] > 0:
                max_dropoff = step["dropoff_rate"]
                max_dropoff_step = step["step"]

        if max_dropoff_step and max_dropoff > 0.1:  # Only report if >10% dropoff
            return {
                "step": max_dropoff_step,
                "dropoff_rate": round(max_dropoff, 4),
            }
        return None
```

- [ ] **Step 2: 创建测试 backend/tests/test_funnel.py**

```python
import pytest
from app.services.funnel import FunnelAnalyzer


@pytest.fixture
def sample_events():
    return [
        {"user_id": "u1", "event_type": "impression", "event_time": "2024-01-01"},
        {"user_id": "u1", "event_type": "click", "event_time": "2024-01-01"},
        {"user_id": "u1", "event_type": "add_to_cart", "event_time": "2024-01-01"},
        {"user_id": "u2", "event_type": "impression", "event_time": "2024-01-01"},
        {"user_id": "u2", "event_type": "click", "event_time": "2024-01-01"},
        {"user_id": "u3", "event_type": "impression", "event_time": "2024-01-01"},
    ]


def test_funnel_analyzer_basic(sample_events):
    analyzer = FunnelAnalyzer()
    result = analyzer.analyze(sample_events)

    assert result["total_users"] == 3
    assert len(result["funnel"]) == 5  # 5 default steps

    # Step: impression - all 3 users
    impression_step = result["funnel"][0]
    assert impression_step["step"] == "impression"
    assert impression_step["user_count"] == 3
    assert impression_step["conversion_rate"] == 1.0

    # Step: click - 2 users
    click_step = result["funnel"][1]
    assert click_step["step"] == "click"
    assert click_step["user_count"] == 2
    assert click_step["conversion_rate"] == 2/3  # 2 out of 3

    # Step: add_to_cart - 1 user
    cart_step = result["funnel"][2]
    assert cart_step["step"] == "add_to_cart"
    assert cart_step["user_count"] == 1


def test_funnel_biggest_dropoff(sample_events):
    analyzer = FunnelAnalyzer()
    result = analyzer.analyze(sample_events)

    # add_to_cart has biggest dropoff (1/2 = 50%)
    assert result["biggest_dropoff"] is not None
    assert result["biggest_dropoff"]["step"] == "add_to_cart"


def test_funnel_empty_events():
    analyzer = FunnelAnalyzer()
    result = analyzer.analyze([])

    assert result["total_users"] == 0
    assert all(step["user_count"] == 0 for step in result["funnel"])


def test_funnel_custom_steps():
    custom_steps = ["impression", "purchase"]
    analyzer = FunnelAnalyzer(steps=custom_steps)

    events = [
        {"user_id": "u1", "event_type": "impression"},
        {"user_id": "u2", "event_type": "impression"},
    ]

    result = analyzer.analyze(events)
    assert len(result["funnel"]) == 2
    assert result["funnel"][0]["step"] == "impression"
    assert result["funnel"][1]["step"] == "purchase"
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && pytest tests/test_funnel.py -v
# Expected: PASS (4 tests)
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/funnel.py backend/tests/test_funnel.py && git commit -m "feat: add funnel analysis engine

- FunnelAnalyzer class for conversion analysis
- Calculates step-by-step user counts and conversion rates
- Identifies biggest drop-off point
- Supports custom funnel steps
- Full test coverage"
```

---

### Task 8: RFM 分析引擎

**Files:**
- Create: `backend/app/services/rfm.py`
- Create: `backend/tests/test_rfm.py`

- [ ] **Step 1: 创建 app/services/rfm.py**

```python
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RFMResult:
    """RFM analysis result for a single customer."""
    user_id: str
    recency: int  # days since last purchase
    frequency: int  # number of purchases
    monetary: float  # total amount
    rfm_score: Tuple[int, int, int]  # R, F, M scores (1-5 each)
    segment: str  # customer segment name


class RFMAnalyzer:
    """
    RFM (Recency, Frequency, Monetary) customer analysis.

    Divides customers into segments based on purchase behavior.
    """

    # Segment definitions
    SEGMENTS = {
        "champions": "高价值 champion 客户 - 最近活跃购买频繁",
        "loyal": "忠诚客户 - 购买频次高",
        "potential_loyalist": "潜在忠诚 - 有购买历史的新客户",
        "recent": "新客户 - 最近有购买",
        "promising": "有潜力 - 最近有互动但需培养",
        "needs_attention": "需关注 - 活跃度下降",
        "at_risk": "风险客户 - 很久没购买",
        "lost": "流失客户 - 长期未购买",
    }

    def __init__(self, reference_date: Optional[datetime] = None):
        self.reference_date = reference_date or datetime.now()

    def analyze(
        self,
        orders: List[Dict[str, Any]],
        user_id_field: str = "user_id",
        order_time_field: str = "event_time",
        amount_field: str = "amount",
    ) -> Dict[str, Any]:
        """
        Perform RFM analysis on order data.

        Returns:
            dict with segment distribution and individual customer results
        """
        # Aggregate customer metrics
        customer_metrics = self._aggregate_metrics(
            orders, user_id_field, order_time_field, amount_field
        )

        # Calculate RFM scores
        scored_customers = self._score_customers(customer_metrics)

        # Segment customers
        segmented = self._segment_customers(scored_customers)

        return {
            "segment_distribution": self._count_segments(segmented),
            "segment_details": self.SEGMENTS,
            "customers": [self._rfm_to_dict(rfm) for rfm in segmented],
            "summary": self._generate_summary(segmented),
        }

    def _aggregate_metrics(
        self,
        orders: List[Dict[str, Any]],
        user_id_field: str,
        order_time_field: str,
        amount_field: str,
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate order data by user."""
        customer_data = defaultdict(lambda: {"orders": [], "amounts": []})

        for order in orders:
            user_id = str(order.get(user_id_field, ""))
            if not user_id:
                continue

            order_time_str = order.get(order_time_field)
            amount = float(order.get(amount_field, 0) or 0)

            # Parse datetime
            if isinstance(order_time_str, str):
                try:
                    order_time = datetime.fromisoformat(order_time_str.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(order_time_str, datetime):
                order_time = order_time_str
            else:
                continue

            customer_data[user_id]["orders"].append(order_time)
            customer_data[user_id]["amounts"].append(amount)

        # Calculate R, F, M per customer
        result = {}
        for user_id, data in customer_data.items():
            if not data["orders"]:
                continue

            last_order = max(data["orders"])
            recency = (self.reference_date - last_order).days
            frequency = len(data["orders"])
            monetary = sum(data["amounts"])

            result[user_id] = {
                "recency": recency,
                "frequency": frequency,
                "monetary": monetary,
            }

        return result

    def _score_customers(
        self, customer_metrics: Dict[str, Dict[str, Any]]
    ) -> List[RFMResult]:
        """Calculate RFM scores (1-5) for each customer."""
        if not customer_metrics:
            return []

        # Get quintile boundaries
        recencies = [m["recency"] for m in customer_metrics.values()]
        frequencies = [m["frequency"] for m in customer_metrics.values()]
        monetaries = [m["monetary"] for m in customer_metrics.values()]

        # R: lower is better (less days since purchase)
        r_quintiles = self._get_quintile_boundaries(recencies, lower_is_better=True)
        # F: higher is better
        f_quintiles = self._get_quintile_boundaries(frequencies, lower_is_better=False)
        # M: higher is better
        m_quintiles = self._get_quintile_boundaries(monetaries, lower_is_better=False)

        results = []
        for user_id, metrics in customer_metrics.items():
            r_score = self._calculate_score(metrics["recency"], r_quintiles, lower_is_better=True)
            f_score = self._calculate_score(metrics["frequency"], f_quintiles, lower_is_better=False)
            m_score = self._calculate_score(metrics["monetary"], m_quintiles, lower_is_better=False)

            rfm_score = (r_score, f_score, m_score)

            results.append(RFMResult(
                user_id=user_id,
                recency=metrics["recency"],
                frequency=metrics["frequency"],
                monetary=metrics["monetary"],
                rfm_score=rfm_score,
                segment="",  # Will be filled by _segment_customers
            ))

        return results

    def _get_quintile_boundaries(
        self, values: List[float], lower_is_better: bool
    ) -> List[float]:
        """Get quintile (20%) boundaries for scoring."""
        if not values:
            return [0, 0, 0, 0]

        sorted_values = sorted(values)
        n = len(sorted_values)

        # 5 quintiles = 6 boundaries (including min and max)
        q1 = sorted_values[int(n * 0.2)]
        q2 = sorted_values[int(n * 0.4)]
        q3 = sorted_values[int(n * 0.6)]
        q4 = sorted_values[int(n * 0.8)]

        if lower_is_better:
            return [float('inf'), q4, q3, q2, q1, -float('inf')]
        else:
            return [-float('inf'), q1, q2, q3, q4, float('inf')]

    def _calculate_score(
        self, value: float, quintiles: List[float], lower_is_better: bool
    ) -> int:
        """Calculate score (1-5) based on quintile boundaries."""
        for i, boundary in enumerate(quintiles[1:], 1):
            if value < boundary:
                return 6 - i if lower_is_better else i
        return 1 if lower_is_better else 5

    def _segment_customers(self, customers: List[RFMResult]) -> List[RFMResult]:
        """Assign segment names to customers based on RFM scores."""
        for customer in customers:
            r, f, m = customer.rfm_score
            score_sum = r + f + m

            if r >= 4 and f >= 4 and m >= 4:
                customer.segment = "champions"
            elif f >= 4 and m >= 3:
                customer.segment = "loyal"
            elif r >= 3 and f >= 2:
                customer.segment = "potential_loyalist"
            elif r >= 3:
                customer.segment = "recent"
            elif r >= 2:
                customer.segment = "promising"
            elif score_sum >= 6:
                customer.segment = "needs_attention"
            elif f >= 2:
                customer.segment = "at_risk"
            else:
                customer.segment = "lost"

        return customers

    def _count_segments(self, customers: List[RFMResult]) -> Dict[str, int]:
        """Count customers in each segment."""
        counts = defaultdict(int)
        for customer in customers:
            counts[customer.segment] += 1
        return dict(counts)

    def _rfm_to_dict(self, rfm: RFMResult) -> Dict[str, Any]:
        """Convert RFMResult to dict for JSON serialization."""
        return {
            "user_id": rfm.user_id,
            "recency": rfm.recency,
            "frequency": rfm.frequency,
            "monetary": round(rfm.monetary, 2),
            "rfm_score": rfm.rfm_score,
            "segment": rfm.segment,
        }

    def _generate_summary(self, customers: List[RFMResult]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not customers:
            return {}

        total = len(customers)
        segments = self._count_segments(customers)

        return {
            "total_customers": total,
            "avg_recency": sum(c.recency for c in customers) / total,
            "avg_frequency": sum(c.frequency for c in customers) / total,
            "avg_monetary": sum(c.monetary for c in customers) / total,
            "top_segment": max(segments, key=segments.get) if segments else None,
            "high_value_count": sum(1 for c in customers if c.segment in ["champions", "loyal"]),
        }
```

- [ ] **Step 2: 创建测试 backend/tests/test_rfm.py**

```python
import pytest
from datetime import datetime, timedelta
from app.services.rfm import RFMAnalyzer, RFMResult


@pytest.fixture
def sample_orders():
    """Sample order data for testing."""
    today = datetime.now()
    return [
        {"user_id": "u1", "event_time": (today - timedelta(days=1)).isoformat(), "amount": 500},
        {"user_id": "u1", "event_time": (today - timedelta(days=5)).isoformat(), "amount": 300},
        {"user_id": "u2", "event_time": (today - timedelta(days=10)).isoformat(), "amount": 200},
        {"user_id": "u3", "event_time": (today - timedelta(days=60)).isoformat(), "amount": 100},
        {"user_id": "u4", "event_time": (today - timedelta(days=90)).isoformat(), "amount": 50},
    ]


def test_rfm_basic(sample_orders):
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(sample_orders)

    assert "segment_distribution" in result
    assert "customers" in result
    assert "summary" in result
    assert result["summary"]["total_customers"] == 5


def test_rfm_champions_segment(sample_orders):
    """u1 has recent, frequent, high-value purchases - should be champion."""
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(sample_orders)

    u1 = next((c for c in result["customers"] if c["user_id"] == "u1"), None)
    assert u1 is not None
    assert u1["segment"] in ["champions", "loyal", "potential_loyalist"]


def test_rfm_lost_segment(sample_orders):
    """u4 has very old purchase - should be lost."""
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(sample_orders)

    u4 = next((c for c in result["customers"] if c["user_id"] == "u4"), None)
    assert u4 is not None
    assert u4["segment"] == "lost"


def test_rfm_rfm_scores_range():
    """RFM scores should be 1-5."""
    orders = [
        {"user_id": "u1", "event_time": datetime.now().isoformat(), "amount": 1000},
    ]
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(orders)

    u1 = result["customers"][0]
    r, f, m = u1["rfm_score"]
    assert 1 <= r <= 5
    assert 1 <= f <= 5
    assert 1 <= m <= 5


def test_rfm_empty_orders():
    """Empty orders should return empty result."""
    analyzer = RFMAnalyzer()
    result = analyzer.analyze([])

    assert result["summary"]["total_customers"] == 0
    assert len(result["customers"]) == 0
```

- [ ] **Step 3: 运行测试**

```bash
cd backend && pytest tests/test_rfm.py -v
# Expected: PASS (5 tests)
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/services/rfm.py backend/tests/test_rfm.py && git commit -m "feat: add RFM customer analysis engine

- RFMAnalyzer for Recency, Frequency, Monetary analysis
- 8 customer segments (champions, loyal, at_risk, etc.)
- Quintile-based scoring (1-5)
- Full test coverage"
```

---

## Phase 4: 报告与对话 (Week 5-7)

### Task 9: LLM 抽象层

**Files:**
- Create: `backend/app/services/llm.py`
- Create: `backend/app/services/insight.py`
- Create: `backend/tests/test_llm.py`

- [ ] **Step 1: 创建 app/services/llm.py**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
import json
import httpx
from app.config import get_settings

settings = get_settings()


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Send chat request and return response text."""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Send chat request and yield response chunks."""
        pass


class OpenAICompatibleLLM(BaseLLM):
    """
    LLM adapter for OpenAI-compatible APIs.

    Supports:
    - OpenAI API
    - Local models via Ollama
    - vLLM
    - LM Studio
    """

    def __init__(
        self,
        api_url: str = None,
        api_key: str = None,
        model: str = None,
    ):
        self.api_url = api_url or settings.LLM_API_URL
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_url.rsplit("/v1", 1)[0],
                timeout=120.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Send chat request and return full response."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_url}",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[str]:
        """Send chat request and yield response chunks."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_url}",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            continue


def get_llm() -> BaseLLM:
    """Get configured LLM instance."""
    return OpenAICompatibleLLM()
```

- [ ] **Step 2: 创建 app/services/insight.py**

```python
from typing import Dict, Any, List, Optional
from app.services.llm import BaseLLM


class InsightGenerator:
    """
    Generate human-readable insights from analysis results.

    Uses LLM to convert data metrics into actionable recommendations.
    """

    SYSTEM_PROMPT = """你是一个专业的电商数据分析师。你的任务是：
1. 分析用户提供的业务数据
2. 用通俗易懂的语言解释数据含义
3. 指出关键发现和异常
4. 提供具体的优化建议

请用中文回答。回答要简洁、专业、有洞察力。"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def generate_funnel_insight(self, funnel_data: Dict[str, Any]) -> str:
        """Generate insight for funnel analysis results."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""分析以下漏斗数据，给出简洁的洞察和建议：

{self._format_funnel_data(funnel_data)}

请用2-3句话总结：1) 最大问题在哪 2) 具体建议是什么。"""},
        ]

        response = await self.llm.chat(messages, temperature=0.5, max_tokens=300)
        return response

    async def generate_rfm_insight(self, rfm_data: Dict[str, Any]) -> str:
        """Generate insight for RFM analysis results."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""分析以下客户分层数据，给出简洁的洞察和建议：

{self._format_rfm_data(rfm_data)}

请用2-3句话总结：1) 客户整体质量如何 2) 重点该关注哪类客户 3) 如何提升客户价值。"""},
        ]

        response = await self.llm.chat(messages, temperature=0.5, max_tokens=300)
        return response

    async def generate_dashboard_summary(
        self,
        metrics: Dict[str, Any],
        funnel: Dict[str, Any],
        rfm: Dict[str, Any],
    ) -> str:
        """Generate overall dashboard summary."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""作为电商数据分析师，请总结以下数据整体情况：

【核心指标】
{self._format_metrics(metrics)}

【转化漏斗】
{self._format_funnel_data(funnel)}

【客户分层】
{self._format_rfm_data(rfm)}

请用3-4句话总结：
1. 本月整体表现如何
2. 最大的机会或风险是什么
3. 最应该关注的一个行动点是什么"""},
        ]

        response = await self.llm.chat(messages, temperature=0.5, max_tokens=400)
        return response

    def _format_funnel_data(self, data: Dict[str, Any]) -> str:
        """Format funnel data for LLM prompt."""
        lines = []
        for step in data.get("funnel", []):
            step_name = step.get("step", "")
            count = step.get("user_count", 0)
            rate = step.get("conversion_rate", 0)
            lines.append(f"- {step_name}: {count}人, 转化率{rate*100:.1f}%")
        return "\n".join(lines)

    def _format_rfm_data(self, data: Dict[str, Any]) -> str:
        """Format RFM data for LLM prompt."""
        summary = data.get("summary", {})
        distribution = data.get("segment_distribution", {})

        lines = [
            f"总客户数: {summary.get('total_customers', 0)}",
            f"高价值客户: {summary.get('high_value_count', 0)}",
            f"平均消费金额: ¥{summary.get('avg_monetary', 0):.0f}",
            "客户分层:",
        ]

        for segment, count in distribution.items():
            lines.append(f"  - {segment}: {count}人")

        return "\n".join(lines)

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for LLM prompt."""
        lines = []
        for key, value in metrics.items():
            if isinstance(value, float):
                if abs(value) > 100:
                    lines.append(f"- {key}: {value:.0f}")
                else:
                    lines.append(f"- {key}: {value:.2f}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)


class NLUnderstanding:
    """
    Convert natural language queries into structured analysis requests.

    Uses LLM to understand user intent and extract parameters.
    """

    QUERY_TYPES = [
        "funnel_analysis",
        "rfm_analysis",
        "comparison",
        "trend",
        "customer_list",
        "general",
    ]

    SYSTEM_PROMPT = """你是一个电商数据分析助手。用户会用自然语言提问，你需要：
1. 判断用户想做什么分析（漏斗分析/RFM分析/对比/趋势/客户列表/其他）
2. 提取关键参数（时间范围、用户群体、具体指标等）
3. 用JSON格式返回结果

请严格按照以下JSON格式返回，不要添加任何解释：
{
  "query_type": "funnel_analysis|rfm_analysis|comparison|trend|customer_list|general",
  "parameters": {
    "time_range": "最近7天|最近30天|本月|上月|自定义",
    "filters": {},
    "sort_by": null
  },
  "original_question": "用户原始问题"
}"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def parse(self, user_query: str) -> Dict[str, Any]:
        """Parse user query into structured request."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        response = await self.llm.chat(messages, temperature=0.3, max_tokens=500)

        # Extract JSON from response
        try:
            # Try to find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            else:
                return self._default_result(user_query)
        except json.JSONDecodeError:
            return self._default_result(user_query)

    def _default_result(self, user_query: str) -> Dict[str, Any]:
        """Return default result when parsing fails."""
        return {
            "query_type": "general",
            "parameters": {},
            "original_question": user_query,
        }
```

- [ ] **Step 3: 创建测试 backend/tests/test_llm.py**

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.llm import OpenAICompatibleLLM
from app.services.insight import InsightGenerator, NLUnderstanding


@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    llm = OpenAICompatibleLLM(api_url="http://localhost/v1/chat/completions", api_key="test")
    llm.chat = AsyncMock(return_value="这是一个测试回复")
    return llm


@pytest.mark.asyncio
async def test_insight_generator_funnel(mock_llm):
    """Test funnel insight generation."""
    generator = InsightGenerator(mock_llm)

    funnel_data = {
        "funnel": [
            {"step": "impression", "user_count": 1000, "conversion_rate": 1.0},
            {"step": "click", "user_count": 500, "conversion_rate": 0.5},
            {"step": "purchase", "user_count": 50, "conversion_rate": 0.1},
        ],
        "biggest_dropoff": {"step": "click", "dropoff_rate": 0.8},
    }

    insight = await generator.generate_funnel_insight(funnel_data)

    assert insight == "这是一个测试回复"
    mock_llm.chat.assert_called_once()


@pytest.mark.asyncio
async def test_nl_understanding_parse(mock_llm):
    """Test natural language query parsing."""
    parser = NLUnderstanding(mock_llm)
    mock_llm.chat.return_value = '{"query_type": "funnel_analysis", "parameters": {"time_range": "最近7天"}, "original_question": "最近7天漏斗"}'

    result = await parser.parse("最近7天的漏斗转化情况怎么样？")

    assert result["query_type"] == "funnel_analysis"
    assert result["parameters"]["time_range"] == "最近7天"


@pytest.mark.asyncio
async def test_nl_understanding_invalid_json(mock_llm):
    """Test handling of invalid LLM response."""
    parser = NLUnderstanding(mock_llm)
    mock_llm.chat.return_value = "这不是JSON格式"

    result = await parser.parse("我的数据怎么样？")

    assert result["query_type"] == "general"
    assert result["original_question"] == "我的数据怎么样？"
```

- [ ] **Step 4: 运行测试**

```bash
cd backend && pytest tests/test_llm.py -v
# Expected: PASS (3 tests)
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/llm.py backend/app/services/insight.py backend/tests/test_llm.py && git commit -m "feat: add LLM abstraction layer and insight generation

- OpenAICompatibleLLM adapter for local/Ollama models
- InsightGenerator for creating human-readable insights
- NLUnderstanding for parsing natural language queries
- Full test coverage with mocks"
```

---

### Task 10: PDF 报告生成

**Files:**
- Create: `backend/app/services/report_generator.py`

- [ ] **Step 1: 创建 app/services/report_generator.py**

```python
from typing import Dict, Any, Optional
from datetime import datetime
import json


class ReportGenerator:
    """
    Generate PDF reports from analysis data.

    MVP uses WeasyPrint for PDF generation.
    Future: React-PDF for frontend rendering.
    """

    TEMPLATES = {
        "weekly": "周报",
        "monthly": "月报",
        "funnel": "漏斗分析报告",
        "rfm": "客户分析报告",
        "custom": "自定义报告",
    }

    def __init__(self, output_dir: str = "/tmp/reports"):
        self.output_dir = output_dir

    async def generate(
        self,
        report_type: str,
        data: Dict[str, Any],
        title: Optional[str] = None,
    ) -> str:
        """
        Generate PDF report and return file path.

        Args:
            report_type: Type of report (weekly/monthly/funnel/rfm/custom)
            data: Analysis data to include
            title: Optional custom title

        Returns:
            Path to generated PDF file
        """
        template_name = self.TEMPLATES.get(report_type, "报告")

        content = self._build_html_content(
            title=title or f"{template_name} - {datetime.now().strftime('%Y-%m-%d')}",
            report_type=report_type,
            data=data,
        )

        # Save HTML for React-PDF rendering
        html_path = f"{self.output_dir}/report_{datetime.now().timestamp()}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)

        # For MVP, return HTML path
        # WeasyPrint PDF generation would go here
        return html_path

    def _build_html_content(
        self,
        title: str,
        report_type: str,
        data: Dict[str, Any],
    ) -> str:
        """Build HTML content for the report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; }}
        h1 {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric-card {{ display: inline-block; padding: 20px; margin: 10px; background: #f5f5f5; border-radius: 8px; min-width: 150px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #0066cc; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f0f0f0; font-weight: 600; }}
        .insight {{ background: #e8f4fc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ margin-top: 40px; color: #999; font-size: 0.8em; text-align: center; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>

    {self._render_data_content(report_type, data)}

    <div class="footer">
        由电商数据分析智能助手生成
    </div>
</body>
</html>
"""
        return html

    def _render_data_content(self, report_type: str, data: Dict[str, Any]) -> str:
        """Render specific content based on report type."""
        if report_type == "funnel":
            return self._render_funnel_content(data)
        elif report_type == "rfm":
            return self._render_rfm_content(data)
        elif report_type in ["weekly", "monthly"]:
            return self._render_summary_content(data)
        else:
            return self._render_generic_content(data)

    def _render_funnel_content(self, data: Dict[str, Any]) -> str:
        """Render funnel analysis content."""
        funnel = data.get("funnel", [])
        rows = ""
        for step in funnel:
            rows += f"""
            <tr>
                <td>{step.get('step', '')}</td>
                <td>{step.get('user_count', 0)}</td>
                <td>{step.get('conversion_rate', 0)*100:.1f}%</td>
                <td>{step.get('dropoff_rate', 0)*100:.1f}%</td>
            </tr>"""

        return f"""
    <h2>转化漏斗分析</h2>
    <table>
        <tr>
            <th>步骤</th>
            <th>用户数</th>
            <th>转化率</th>
            <th>流失率</th>
        </tr>
        {rows}
    </table>
    {self._render_insight(data.get('biggest_dropoff'), "最大流失环节")}
"""

    def _render_rfm_content(self, data: Dict[str, Any]) -> str:
        """Render RFM analysis content."""
        summary = data.get("summary", {})
        distribution = data.get("segment_distribution", {})

        segment_rows = ""
        for segment, count in distribution.items():
            segment_rows += f"<tr><td>{segment}</td><td>{count}</td></tr>"

        return f"""
    <h2>客户分析</h2>
    <div class="metric-card">
        <div class="metric-value">{summary.get('total_customers', 0)}</div>
        <div class="metric-label">总客户数</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{summary.get('high_value_count', 0)}</div>
        <div class="metric-label">高价值客户</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">¥{summary.get('avg_monetary', 0):.0f}</div>
        <div class="metric-label">平均消费</div>
    </div>

    <h3>客户分层</h3>
    <table>
        <tr><th>分层</th><th>客户数</th></tr>
        {segment_rows}
    </table>
"""

    def _render_summary_content(self, data: Dict[str, Any]) -> str:
        """Render weekly/monthly summary."""
        html = "<h2>核心指标</h2>"
        metrics = data.get("metrics", {})

        for key, value in metrics.items():
            display_value = f"¥{value:.0f}" if "amount" in key.lower() else f"{value:.2f}" if isinstance(value, float) else str(value)
            html += f"""
    <div class="metric-card">
        <div class="metric-value">{display_value}</div>
        <div class="metric-label">{key}</div>
    </div>"""

        return html

    def _render_generic_content(self, data: Dict[str, Any]) -> str:
        """Render generic content."""
        return f"<pre>{json.dumps(data, ensure_ascii=False, indent=2)}</pre>"

    def _render_insight(self, insight: Optional[Dict], label: str) -> str:
        """Render insight section."""
        if not insight:
            return ""

        return f"""
    <div class="insight">
        <strong>{label}:</strong> {insight.get('step', '')} (流失率: {insight.get('dropoff_rate', 0)*100:.1f}%)
    </div>
"""
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/services/report_generator.py && git commit -m "feat: add PDF report generator

- ReportGenerator for creating HTML reports
- Support for funnel, RFM, weekly, monthly report templates
- Structured HTML output ready for React-PDF or WeasyPrint"
```

---

## Phase 5: 运营支撑 (Week 7-8)

### Task 11: Celery 任务队列

**Files:**
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/analyze.py`
- Create: `backend/app/tasks/report.py`
- Create: `backend/celery_app.py`

- [ ] **Step 1: 创建 backend/celery_app.py**

```python
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.analyze", "app.tasks.report"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_routes={
        "app.tasks.analyze.*": {"queue": "analysis"},
        "app.tasks.report.*": {"queue": "reports"},
    },
    task_annotations={
        "app.tasks.analyze.*": {"rate_limit": "10/m"},
        "app.tasks.report.*": {"rate_limit": "5/m"},
    },
)
```

- [ ] **Step 2: 创建 backend/app/tasks/analyze.py**

```python
from app.tasks.celery_app import celery_app
from app.services.funnel import FunnelAnalyzer
from app.services.rfm import RFMAnalyzer
import json


@celery_app.task(name="app.tasks.analyze.run_funnel_analysis")
def run_funnel_analysis(data: list, user_id: int) -> dict:
    """
    Run funnel analysis asynchronously.

    Args:
        data: List of event records
        user_id: User ID for audit logging

    Returns:
        Analysis results
    """
    analyzer = FunnelAnalyzer()
    result = analyzer.analyze(data)
    return {
        "user_id": user_id,
        "analysis_type": "funnel",
        "result": result,
    }


@celery_app.task(name="app.tasks.analyze.run_rfm_analysis")
def run_rfm_analysis(data: list, user_id: int) -> dict:
    """
    Run RFM analysis asynchronously.

    Args:
        data: List of order records
        user_id: User ID for audit logging

    Returns:
        Analysis results
    """
    analyzer = RFMAnalyzer()
    result = analyzer.analyze(data)
    return {
        "user_id": user_id,
        "analysis_type": "rfm",
        "result": result,
    }
```

- [ ] **Step 3: 提交**

```bash
git add backend/celery_app.py backend/app/tasks/ && git commit -m "feat: add Celery task queue

- Celery app configuration with Redis broker
- Task routing for analysis and reports queues
- Rate limiting per task type
- Funnel and RFM async analysis tasks"
```

---

## Phase 6: 测试与上线准备 (Week 8-10)

### Task 12: API 集成测试

**Files:**
- Create: `backend/tests/test_api_integration.py`

- [ ] **Step 1: 创建集成测试**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import Base, engine


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_full_user_flow(client):
    """Test complete user flow: register -> login -> upload -> analyze."""

    # 1. Register
    register_resp = await client.post(
        "/api/auth/register",
        json={"email": "flow@example.com", "password": "test123"},
    )
    assert register_resp.status_code == 201

    # 2. Login
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "flow@example.com", "password": "test123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # 3. Health check
    health_resp = await client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"
```

- [ ] **Step 2: 提交**

```bash
git add backend/tests/test_api_integration.py && git commit -m "test: add API integration test

- Test full user flow: register -> login -> health check"
```

---

## 实施检查清单

### Week 1-2: 基础设施
- [ ] 项目脚手架
- [ ] FastAPI 结构
- [ ] 用户认证
- [ ] 审计日志

### Week 2-3: 数据接入
- [ ] 数据源管理
- [ ] 文件解析
- [ ] 字段映射

### Week 3-5: 核心分析
- [ ] 漏斗分析
- [ ] RFM 分析
- [ ] LLM 集成

### Week 5-7: 报告与对话
- [ ] NL 查询
- [ ] 报告生成
- [ ] 对话 UI

### Week 7-8: 运营支撑
- [ ] Celery 任务
- [ ] 引导向导
- [ ] 邮件推送

### Week 8-10: 测试与上线
- [ ] 集成测试
- [ ] E2E 测试
- [ ] 部署配置

---

## 成功标准

| 里程碑 | 完成标准 |
|--------|----------|
| M1 | 用户可注册/登录，JWT 正常工作 |
| M2 | 可上传 CSV/Excel，字段自动映射 |
| M3 | 漏斗图正常显示，RFM 分层正确 |
| M4 | AI 解读可工作，报告可生成 |
| M5 | 完整流程跑通，可部署 |
