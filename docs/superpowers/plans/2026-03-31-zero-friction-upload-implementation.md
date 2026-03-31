# 零摩擦上传体验实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现零摩擦上传体验：上传文件 → Thinking动画 → 分析完成 → 直接展示结果

**Architecture:**
- 保留 Celery 异步架构，上传API立即返回datasource_id
- 新增轮询端点 GET /api/analytics/result?datasource_id=xxx
- 前端轮询时显示Thinking动画（精心设计的假进度消息）
- 移除映射确认UI，用户无感知完成所有操作

**Tech Stack:** FastAPI, SQLAlchemy, Celery, React, Next.js

---

## 文件结构

```
backend/
├── app/
│   ├── models/
│   │   ├── analysis.py          # CREATE: AnalysisResult模型
│   │   └── datasource.py        # MODIFY: 已有
│   ├── api/
│   │   ├── analytics.py         # MODIFY: 添加result端点
│   │   └── datasource.py        # MODIFY: 移除confirm-mappings
│   ├── services/
│   │   └── datasource.py        # MODIFY: 移除update_datasource_mappings
│   └── tasks/
│       └── analyze.py            # MODIFY: 保存结果到DB

frontend/src/
├── components/analytics/
│   └── ThinkingAnimation.tsx     # CREATE: Thinking动画组件
├── services/
│   └── api.ts                   # MODIFY: 添加轮询方法
└── app/
    └── page.tsx                 # MODIFY: 移除mapping_confirm，改用thinking
```

---

## Task 1: 创建 AnalysisResult 模型

**Files:**
- Create: `backend/app/models/analysis.py`
- Modify: `backend/app/models/__init__.py` (如果存在)
- Modify: `backend/app/database.py` (如果需要导入)

- [ ] **Step 1: 创建 AnalysisResult 模型**

```python
# backend/app/models/analysis.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, enum.Enum):
    FUNNEL = "funnel"
    RFM = "rfm"
    OVERVIEW = "overview"


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    datasource_id = Column(Integer, ForeignKey("datasources.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    result_data = Column(JSON, nullable=True)  # 分析结果
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: 在 database.py 中导入**

检查 `backend/app/database.py` 是否需要添加导入。

- [ ] **Step 3: 运行 DB migrate**

```bash
cd /mnt/e/project/CommercialDataAnalyzer/backend
# 创建迁移或直接创建表
python -c "
import asyncio
from app.database import engine, Base
from app.models.analysis import AnalysisResult
from app.models.datasource import DataSource, Dataset
from app.models.user import User
from app.models.audit import AuditLog

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tables created successfully')

asyncio.run(create_tables())
"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/analysis.py
git commit -m "feat: add AnalysisResult model for storing analysis data"
```

---

## Task 2: 修改 Celery Task 保存结果到 DB

**Files:**
- Modify: `backend/app/tasks/analyze.py`

- [ ] **Step 1: 修改 Celery tasks 保存结果**

```python
# backend/app/tasks/analyze.py
from celery_app import celery_app
from app.services.funnel import FunnelAnalyzer
from app.services.rfm import RFMAnalyzer
from app.models.analysis import AnalysisResult, AnalysisStatus, AnalysisType
from app.database import SessionLocal
import json

def save_analysis_result(datasource_id: int, user_id: int, analysis_type: AnalysisType, result_data: dict, status: AnalysisStatus = AnalysisStatus.COMPLETED, error_message: str = None):
    """保存分析结果到数据库"""
    db = SessionLocal()
    try:
        # 查找已存在的记录或创建新记录
        existing = db.query(AnalysisResult).filter(
            AnalysisResult.datasource_id == datasource_id,
            AnalysisResult.analysis_type == analysis_type
        ).first()

        if existing:
            existing.status = status
            existing.result_data = result_data
            existing.error_message = error_message
        else:
            analysis_result = AnalysisResult(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=analysis_type,
                status=status,
                result_data=result_data,
                error_message=error_message
            )
            db.add(analysis_result)

        db.commit()
    finally:
        db.close()


@celery_app.task(name="app.tasks.analyze.run_funnel_analysis")
def run_funnel_analysis(data: list, user_id: int, datasource_id: int = None) -> dict:
    """
    Run funnel analysis asynchronously.

    Args:
        data: List of event records
        user_id: User ID for audit logging
        datasource_id: DataSource ID for storing results

    Returns:
        Analysis results
    """
    try:
        analyzer = FunnelAnalyzer()
        result = analyzer.analyze(data)

        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.FUNNEL,
                result_data=result
            )

        return {
            "user_id": user_id,
            "analysis_type": "funnel",
            "result": result,
        }
    except Exception as e:
        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.FUNNEL,
                result_data=None,
                status=AnalysisStatus.FAILED,
                error_message=str(e)
            )
        raise


@celery_app.task(name="app.tasks.analyze.run_rfm_analysis")
def run_rfm_analysis(data: list, user_id: int, datasource_id: int = None) -> dict:
    """
    Run RFM analysis asynchronously.

    Args:
        data: List of order records
        user_id: User ID for audit logging
        datasource_id: DataSource ID for storing results

    Returns:
        Analysis results
    """
    try:
        analyzer = RFMAnalyzer()
        result = analyzer.analyze(data)

        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.RFM,
                result_data=result
            )

        return {
            "user_id": user_id,
            "analysis_type": "rfm",
            "result": result,
        }
    except Exception as e:
        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.RFM,
                result_data=None,
                status=AnalysisStatus.FAILED,
                error_message=str(e)
            )
        raise
```

- [ ] **Step 2: 验证语法**

```bash
cd /mnt/e/project/CommercialDataAnalyzer/backend
python3 -m py_compile app/tasks/analyze.py
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/tasks/analyze.py
git commit -m "feat: modify Celery tasks to save results to database"
```

---

## Task 3: 添加 GET /api/analytics/result 端点

**Files:**
- Modify: `backend/app/api/analytics.py`

- [ ] **Step 1: 添加 result 端点**

在 `backend/app/api/analytics.py` 添加：

```python
from app.models.analysis import AnalysisResult, AnalysisStatus, AnalysisType

@router.get("/result")
async def get_analysis_result(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get analysis result for a datasource. Poll this endpoint after upload."""
    from sqlalchemy import select

    # 查询 funnel 和 rfm 结果
    results = {}
    status = "processing"

    funnel_result = await db.execute(
        select(AnalysisResult).where(
            AnalysisResult.datasource_id == datasource_id,
            AnalysisResult.analysis_type == AnalysisType.FUNNEL
        )
    )
    funnel_record = funnel_result.scalar_one_or_none()

    rfm_result = await db.execute(
        select(AnalysisResult).where(
            AnalysisResult.datasource_id == datasource_id,
            AnalysisResult.analysis_type == AnalysisType.RFM
        )
    )
    rfm_record = rfm_result.scalar_one_or_none()

    # 确定状态
    if funnel_record and rfm_record:
        if funnel_record.status == AnalysisStatus.FAILED or rfm_record.status == AnalysisStatus.FAILED:
            status = "failed"
            failed_record = funnel_record if funnel_record.status == AnalysisStatus.FAILED else rfm_record
            return {
                "status": "failed",
                "error": failed_record.error_message or "分析失败"
            }
        elif funnel_record.status == AnalysisStatus.COMPLETED and rfm_record.status == AnalysisStatus.COMPLETED:
            status = "completed"
            results["funnel_result"] = funnel_record.result_data
            results["rfm_result"] = rfm_record.result_data

            # 生成 overview
            results["overview"] = {
                "total_orders": rfm_record.result_data.get("total_orders", 0),
                "total_revenue": rfm_record.result_data.get("total_revenue", 0),
                "avg_order_value": rfm_record.result_data.get("avg_order_value", 0),
                "total_customers": rfm_record.result_data.get("total_customers", 0),
            }
        else:
            status = "processing"
    else:
        status = "processing"

    return {
        "status": status,
        **results
    }
```

- [ ] **Step 2: 验证语法**

```bash
python3 -m py_compile app/api/analytics.py
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/analytics.py
git commit -m "feat: add GET /api/analytics/result endpoint for polling"
```

---

## Task 4: 移除 confirm-mappings 端点和 update_datasource_mappings

**Files:**
- Modify: `backend/app/api/datasource.py`
- Modify: `backend/app/services/datasource.py`

- [ ] **Step 1: 从 datasource.py 移除 confirm-mappings 端点**

删除 `@router.post("/confirm-mappings")` 函数（整个函数）

- [ ] **Step 2: 从 datasource.py 移除 update_datasource_mappings 导入**

```python
# 原来
from app.services.datasource import create_datasource, get_user_datasources, get_datasource, upload_and_parse, update_datasource_mappings
# 改为
from app.services.datasource import create_datasource, get_user_datasources, get_datasource, upload_and_parse
```

- [ ] **Step 3: 从 services/datasource.py 移除 update_datasource_mappings 函数**

删除整个 `update_datasource_mappings` 函数

- [ ] **Step 4: 验证语法**

```bash
python3 -m py_compile app/api/datasource.py app/services/datasource.py
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/datasource.py backend/app/services/datasource.py
git commit -m "feat: remove confirm-mappings endpoint and update_datasource_mappings"
```

---

## Task 5: 前端 - 创建 ThinkingAnimation 组件

**Files:**
- Create: `frontend/src/components/analytics/ThinkingAnimation.tsx`

- [ ] **Step 1: 创建 ThinkingAnimation 组件**

```tsx
// frontend/src/components/analytics/ThinkingAnimation.tsx
'use client'

import React, { useEffect, useState } from 'react'

interface ThinkingAnimationProps {
  onComplete?: () => void
  estimatedDuration?: number // 预估时间(ms)，用于进度条
}

const THINKING_MESSAGES = [
  { text: '正在解析您的数据文件...', progress: 10 },
  { text: '正在识别用户购买路径...', progress: 25 },
  { text: '正在计算转化漏斗...', progress: 45 },
  { text: '正在构建用户画像...', progress: 60 },
  { text: '正在分析高价值客户群体...', progress: 75 },
  { text: '正在生成RFM分层模型...', progress: 90 },
  { text: '正在优化分析结果...', progress: 98 },
  { text: '正在准备您的报告...', progress: 100 },
]

export default function ThinkingAnimation({
  onComplete,
  estimatedDuration = 8000,
}: ThinkingAnimationProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [displayedMessages, setDisplayedMessages] = useState<typeof THINKING_MESSAGES>([])
  const [progress, setProgress] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    // 初始化显示第一条消息
    setDisplayedMessages([THINKING_MESSAGES[0]])

    const messageInterval = setInterval(() => {
      setCurrentIndex(prev => {
        const next = prev + 1
        if (next < THINKING_MESSAGES.length) {
          setDisplayedMessages(msgs => [...msgs.slice(-6), THINKING_MESSAGES[next]])
          // 随机延迟 800-1200ms
          return next
        }
        return prev
      })
    }, 900 + Math.random() * 400)

    // 进度条动画
    const startTime = Date.now()
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime
      const newProgress = Math.min((elapsed / estimatedDuration) * 100, 99)
      setProgress(newProgress)

      if (elapsed >= estimatedDuration) {
        clearInterval(progressInterval)
      }
    }, 50)

    // 完成
    setTimeout(() => {
      clearInterval(messageInterval)
      clearInterval(progressInterval)
      setProgress(100)
      setIsComplete(true)
      setTimeout(() => {
        onComplete?.()
      }, 500)
    }, estimatedDuration)

    return () => {
      clearInterval(messageInterval)
      clearInterval(progressInterval)
    }
  }, [estimatedDuration, onComplete])

  return (
    <div className="fixed inset-0 bg-surface/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-surface-elevated border border-border rounded-2xl p-8 w-full max-w-md mx-4 shadow-2xl">
        <div className="text-center mb-6">
          <div className="text-2xl font-medium text-text-primary mb-2">
            {isComplete ? '✓ 分析完成！' : '◉ 深度思考中...'}
          </div>
          <div className="text-sm text-text-secondary">
            {isComplete ? '正在跳转到结果...' : '请稍候'}
          </div>
        </div>

        <div className="space-y-1 mb-6">
          {displayedMessages.map((msg, idx) => {
            const isLast = idx === displayedMessages.length - 1 && !isComplete
            const isDone = displayedMessages.indexOf(msg) < displayedMessages.length - 1

            return (
              <div
                key={idx}
                className={`text-sm flex items-center gap-2 ${
                  isDone ? 'text-text-secondary' : 'text-text-primary'
                }`}
              >
                <span className="w-4">
                  {isDone ? '✓' : isLast ? '▸' : '○'}
                </span>
                <span>{msg.text}</span>
              </div>
            )
          })}
        </div>

        <div className="relative h-2 bg-surface rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary to-primary/80 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="text-right text-xs text-text-secondary mt-1">
          {Math.round(progress)}%
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/analytics/ThinkingAnimation.tsx
git commit -m "feat: add ThinkingAnimation component"
```

---

## Task 6: 前端 - 修改 api.ts 添加轮询方法

**Files:**
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: 添加 getAnalysisResult 方法**

在 `analyticsApi` 对象中添加：

```typescript
getAnalysisResult: (datasourceId: number) => {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return fetch(`${API_BASE}/api/analytics/result?datasource_id=${datasourceId}`, {
    method: 'GET',
    headers,
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`获取分析结果失败: ${response.status}`)
    }
    return response.json()
  })
},
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat: add getAnalysisResult polling method"
```

---

## Task 7: 前端 - 修改 page.tsx 移除 mapping_confirm，改用 thinking

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: 添加 ThinkingAnimation 导入**

```typescript
import ThinkingAnimation from '@/components/analytics/ThinkingAnimation'
```

- [ ] **Step 2: 修改 UploadState 类型**

```typescript
// 原来
type UploadState = 'idle' | 'uploading' | 'parsing' | 'mapping_confirm' | 'analyzing' | 'done' | 'error'

// 改为
type UploadState = 'idle' | 'uploading' | 'thinking' | 'done' | 'error'
```

- [ ] **Step 3: 修改 handleFileUpload 函数**

将：
```typescript
setUploadState('mapping_confirm')
```

改为：
```typescript
setUploadState('thinking')
setDatasourceId(result.datasource_id)
```

并添加轮询逻辑：
```typescript
// 在 setUploadState('thinking') 后添加
const pollResult = async () => {
  if (!result.datasource_id) return

  let attempts = 0
  const maxAttempts = 30 // 30秒超时

  const poll = async () => {
    if (attempts >= maxAttempts) {
      setUploadState('error')
      setUploadError('分析耗时较长，请稍后刷新页面查看')
      return
    }

    try {
      const res = await analyticsApi.getAnalysisResult(result.datasource_id)
      if (res.status === 'completed') {
        // 设置分析结果
        setFunnelData(res.funnel_result)
        setRFMData(res.rfm_result)
        setOverviewData(res.overview)
        setUploadState('done')
      } else if (res.status === 'failed') {
        setUploadState('error')
        setUploadError(res.error || '分析失败')
      } else {
        attempts++
        setTimeout(poll, 1000)
      }
    } catch (err) {
      attempts++
      setTimeout(poll, 1000)
    }
  }

  await poll()
}

pollResult()
```

- [ ] **Step 4: 移除 handleMappingConfirm 函数和映射确认 UI**

删除整个 `handleMappingConfirm` 函数
删除 `FieldMappingConfirmProps` 接口
删除 `FieldMappingConfirm` 组件

- [ ] **Step 5: 在 return JSX 中添加 ThinkingAnimation**

在合适位置添加：
```tsx
{uploadState === 'thinking' && (
  <ThinkingAnimation
    estimatedDuration={10000}
    onComplete={() => {}}
  />
)}
```

- [ ] **Step 6: 移除 mapping_confirm 相关的所有代码**

搜索 `mapping_confirm`，删除所有相关逻辑

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat: replace mapping_confirm with thinking animation"
```

---

## Task 8: 端到端测试

- [ ] **Step 1: 重启后端服务**

```bash
docker compose down && docker compose up -d
```

- [ ] **Step 2: 上传 CSV 文件测试**

1. 登录系统
2. 上传 CSV 文件
3. 验证：显示 Thinking 动画
4. 验证：动画结束后显示分析结果
5. 验证：没有映射确认界面

- [ ] **Step 3: 检查后端日志**

```
[UPLOAD] Upload completed successfully for datasource_id=X
[Celery] task queued
GET /api/analytics/result?datasource_id=X -> status: processing
GET /api/analytics/result?datasource_id=X -> status: completed
```

- [ ] **Step 4: Commit**

如果测试通过，所有代码已完成。

---

## 验证清单

- [ ] 上传后立即显示 datasource_id
- [ ] Thinking 动画正常显示
- [ ] 轮询获取到分析结果
- [ ] 结果正确显示在仪表盘
- [ ] 没有显示映射确认 UI
- [ ] 分析失败时显示友好错误
