# 零摩擦上传体验设计

## 概述

当前上传流程要求用户理解字段映射概念并手动确认，造成不必要的认知负担和操作摩擦。改进目标：**上传 → Thinking动画 → 分析完成 → 直接展示结果**，用户零思考。

## 核心原则

- 用户只做一件事：上传文件
- AI 自动完成所有分析和决策
- Thinking 动画传达"深度工作"感，让等待变得有意义

---

## 方案设计

### 1. 后端改动：保留 Celery 异步架构

#### 当前行为
- `upload_and_parse` 调用 Celery `.delay()` 异步触发分析
- API 立即返回 201，前端显示"确认映射"界面
- 分析在后台运行，用户看不到进度

#### 改进行为
- 上传 API **立即返回** `datasource_id`（不等待分析完成）
- Celery 异步分析**保持不变**（系统可扩展性）
- 新增轮询端点 `GET /api/analytics/result?datasource_id=xxx`，前端轮询结果
- 分析完成后结果存储到数据库，前端可获取

#### 改动点
| 文件 | 改动 |
|------|------|
| `app/api/analytics.py` | 新增 `GET /api/analytics/result?datasource_id=xxx` 端点，查询分析结果 |
| `app/models/analysis.py` | 新增 `AnalysisResult` 模型，存储 funnel/rfm 分析结果 |
| `app/tasks/analyze.py` | Celery task 分析完成后保存结果到数据库 |
| `app/services/datasource.py` | 移除 `update_datasource_mappings` 函数（不再需要） |

#### 权衡
- **优点**：API 响应快（不阻塞），系统可水平扩展，Celery 异步架构不变
- **缺点**：前端需要轮询
- **对策**：前端轮询时显示 Thinking 动画（消息是"精心设计的假进度"）

---

### 2. 前端改动：Thinking 动画 + 轮询

#### 当前行为
上传后显示字段映射确认 UI，强制用户操作。

#### 改进行为
上传后显示全屏 Thinking 界面，轮询分析结果，完成后自动跳转到结果。

#### Thinking 界面设计

```
┌─────────────────────────────────────────┐
│                                         │
│              ◉ 深度思考中...            │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │  ▸ 正在解析您的数据文件...      │    │
│  │  ✓ 正在识别用户购买路径...      │    │
│  │  ✓ 正在计算转化漏斗...          │    │
│  │  ✓ 正在构建用户画像...          │    │
│  │  ✓ 正在分析高价值客户群体...    │    │
│  │  ✓ 正在生成RFM分层模型...      │    │
│  │  ✓ 正在优化分析结果...          │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│         ████████████░░░░ 78%            │
│                                         │
└─────────────────────────────────────────┘
```

#### 消息列表（循环播放）

| 序号 | 消息 | 显示时段 |
|------|------|----------|
| 1 | 正在解析您的数据文件... | 0-10% |
| 2 | 正在识别用户购买路径... | 10-25% |
| 3 | 正在计算转化漏斗... | 25-45% |
| 4 | 正在构建用户画像... | 45-60% |
| 5 | 正在分析高价值客户群体... | 60-75% |
| 6 | 正在生成RFM分层模型... | 75-90% |
| 7 | 正在优化分析结果... | 90-98% |
| 8 | 正在准备您的报告... | 98-100% |

#### 动画行为
- 消息每 800-1200ms 随机切换（显得自然，不是机械跳动）
- 进度条从 0% 平滑增长到 100%（基于假进度，与真实轮询结果无关）
- 当前活跃消息前显示 `▸`，已过的消息前显示 `✓`
- 完成后显示 "✓ 分析完成！" 停留 500ms，然后自动跳转

#### 轮询策略
```
1. 上传成功 → 进入 thinking 状态
2. 每 1s 轮询 GET /api/analytics/result?datasource_id=xxx
3. 结果返回 → 停止 thinking → 展示分析结果
4. 超时（30s）→ 显示友好错误："分析耗时较长，请稍后刷新页面查看"
```

#### 状态机改动

```
uploadState: 'idle' → 'uploading' → 'thinking' → 'done'
                ↓                                    ↓
             error                                idle (2s后)
```

移除 `mapping_confirm` 状态。

---

### 3. 字段映射：自动处理，不暴露给用户

#### 当前行为
- 上传后自动检测字段映射，显示确认界面
- 用户必须理解 user_id、amount 等概念

#### 改进行为
- 上传时自动检测 + 应用映射
- 如检测失败，自动使用默认映射（id → user_id, amount → price）
- 不显示任何映射相关 UI

#### 映射策略
| 检测到的字段 | 映射为 |
|-------------|--------|
| user_id, userid, uid, 用户ID, 买家 | user_id |
| price, amount, payment, 金额, 价格 | amount |
| date, time, order_date, 下单时间 | date |
| order_id, orderid, 订单号 | order_id |

---

## 数据流

```
用户选择文件
    ↓
POST /api/datasources/?name=xxx
    ↓
[后端] 读取文件 → 保存 → 解析 → 触发 Celery 异步分析 → 立即返回
    ↓
返回 { "datasource_id": 1 }
    ↓
[前端] Thinking动画开始 → 每1s轮询 GET /api/analytics/result?datasource_id=1
    ↓
[后端] Celery分析完成 → 结果存储 → 轮询返回结果
    ↓
[前端] Thinking动画停止 → 展示结果仪表盘
```

---

## API 响应结构

### POST /api/datasources/

**请求**: `multipart/form-data { name: string, file: File }`

**响应 (201)**:
```json
{
  "datasource_id": 1
}
```

### GET /api/analytics/result?datasource_id=xxx

**响应 (200)** - 分析完成时：
```json
{
  "status": "completed",
  "funnel_result": {
    "steps": [{"name": "浏览", "count": 5000}, {"name": "加购", "count": 2000}, {"name": "下单", "count": 500}],
    "conversion_rates": {"browse_to_cart": 0.4, "cart_to_order": 0.25},
    "drop_off_step": "加购"
  },
  "rfm_result": {
    "segments": {
      "high_value": {"count": 120, "avg_amount": 1500},
      "medium_value": {"count": 300, "avg_amount": 500},
      "low_value": {"count": 580, "avg_amount": 150}
    },
    "total_customers": 1000
  },
  "overview": {
    "total_orders": 1000,
    "total_revenue": 450000,
    "avg_order_value": 450,
    "top_category": "数码",
    "date_range": {"start": "2024-01-01", "end": "2024-03-31"}
  }
}
```

**响应 (200)** - 分析进行中：
```json
{
  "status": "processing"
}
```

**响应 (400)** - 分析失败：
```json
{
  "status": "failed",
  "error": "分析失败：请确保文件包含必要的 user_id 和 amount 字段"
}
```

---

## 新增代码

1. `app/api/analytics.py` - `GET /api/analytics/result` 端点
2. `app/models/analysis.py` - `AnalysisResult` 模型（存储分析结果）
3. 前端 Thinking 动画组件

---

## 移除的代码

1. `app/api/datasource.py` - `POST /confirm-mappings` 端点
2. `app/services/datasource.py` - `update_datasource_mappings` 函数
3. 前端 `handleMappingConfirm` 函数和相关 UI
4. `uploadState === 'mapping_confirm'` 相关逻辑

---

## 测试要点

1. 上传 CSV 文件 → 立即返回 datasource_id → 显示 Thinking 动画
2. 等待后自动获取分析结果并展示
3. 上传后不显示任何映射确认 UI
4. Thinking 动画消息循环自然，无明显重复感
5. 分析失败时显示友好错误，不是技术报错
