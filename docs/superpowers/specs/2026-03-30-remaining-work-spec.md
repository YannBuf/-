# 待完成工作规范

> 本文档记录 MVP 尚需完成的功能，作为实现参考。

---

## 当前状态

| 模块 | 完整度 |
|------|--------|
| 后端核心逻辑（分析引擎） | ~90% ✅ |
| 后端 API 路由 | ~80% ✅ |
| 前端 UI | ~85% ✅ |
| 前后端连接 | ~50% ⚠️ |
| 端到端可用性 | ~40% ⚠️ |

---

## 待完成功能

### 1. 文件上传与解析

**问题描述：**
- `datasource.py` 的 `POST /api/datasources/` 只创建了数据库记录，没有实际保存文件
- `FileParser` 服务存在但未被 API 调用
- 上传后的自动分析流程未打通

**需要完成：**

| 任务 | 描述 |
|------|------|
| 文件存储 | 上传文件保存到服务器本地目录或云存储 |
| 文件解析 | 调用 `FileParser.parse()` 解析文件内容 |
| 字段映射 | 根据 `field_mapper.py` 自动识别字段，提供映射确认 UI |
| 触发分析 | 解析完成后自动触发漏斗/RFM 分析 |
| 结果保存 | 分析结果存入数据库 |

**技术细节：**
```python
# backend/app/services/datasource.py
async def upload_and_parse(
    db: AsyncSession,
    user_id: int,
    file: UploadFile,
    name: str,
) -> Dict[str, Any]:
    # 1. 保存文件到 storage/
    file_path = save_file(file)

    # 2. 解析文件
    content = file.file.read()
    parsed = FileParser.parse(content, file.filename)

    # 3. 自动检测字段映射
    mappings = auto_detect_mappings(parsed["columns"])

    # 4. 转换数据
    mapper = FieldMapper(mappings)
    standard_data = mapper.to_standard(parsed["data"])

    # 5. 触发分析任务（Celery）
    task = run_funnel_analysis.delay(standard_data, user_id)

    return {"task_id": task.id, "parsed": parsed, "mappings": mappings}
```

---

### 2. 认证状态持久化

**问题描述：**
- 登录后 Token 只存在内存，刷新页面丢失
- 前端每个请求都需要带 Token，但目前未实现

**需要完成：**

| 任务 | 描述 |
|------|------|
| Token 存储 | 登录成功后存 localStorage |
| Token 注入 | 请求自动带上 Authorization header |
| 登出 | 清除 localStorage |
| 刷新 Token | 实现 token refresh 逻辑 |

**技术细节：**
```typescript
// frontend/src/services/api.ts
const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token')
  }
  return null
}

const apiCall = async (endpoint: string, options: Options = {}) => {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }
  // ... fetch logic
}
```

---

### 3. 前端文件上传 UI

**问题描述：**
- `handleFileUpload` 只是 alert，没有实际调用 API
- 没有字段映射确认步骤

**需要完成：**

| 任务 | 描述 |
|------|------|
| 上传进度 | 显示上传进度条 |
| 解析状态 | 显示"正在解析..." |
| 字段映射确认 | 用户确认/修改自动识别的字段映射 |
| 错误处理 | 显示上传失败/解析失败的原因 |
| 成功反馈 | 上传成功后刷新 Dashboard 数据 |

**UI 流程：**
```
拖拽文件 → 上传中(进度) → 解析中 → 字段映射确认 → 分析中 → 完成 → Dashboard 更新
```

---

### 4. 分析结果获取与展示

**问题描述：**
- 漏斗图和 RFM 图目前是硬编码数据
- 分析结果没有存数据库，前端无法获取

**需要完成：**

| 任务 | 描述 |
|------|------|
| 结果存储 | 分析结果存入 `AnalysisResult` 表 |
| 结果查询 | `GET /api/analytics/result/{id}` |
| 前端绑定 | Dashboard 调用真实 API 获取结果 |
| 加载状态 | 分析中显示 loading skeleton |

---

### 5. 报告生成完整流程

**问题描述：**
- `POST /api/reports/generate` 有，但前端"生成报告"按钮没调用
- PDF 生成是 HTML 模板，未实际生成 PDF 文件

**需要完成：**

| 任务 | 描述 |
|------|------|
| 前端触发 | 点击"生成报告"调用 API |
| 报告模板 | 选择报告类型（周报/月报/漏斗/RFM） |
| PDF 生成 | 使用 React-PDF 或 WeasyPrint 生成真实 PDF |
| 预览 | 报告页面支持预览 |
| 下载 | 支持下载 PDF 文件 |

---

## API 端点检查清单

| 端点 | 方法 | 状态 | 备注 |
|------|------|------|------|
| `/api/health` | GET | ✅ | 正常 |
| `/api/auth/register` | POST | ✅ | 正常 |
| `/api/auth/login` | POST | ✅ | 正常 |
| `/api/datasources/` | POST | ⚠️ | 需完善文件上传 |
| `/api/datasources/` | GET | ✅ | 正常 |
| `/api/analytics/overview` | GET | ✅ | 正常 |
| `/api/analytics/funnel` | POST | ✅ | 正常 |
| `/api/analytics/rfm` | POST | ✅ | 正常 |
| `/api/analytics/parse-columns` | POST | ✅ | 正常 |
| `/api/conversation/chat` | POST | ✅ | 需 LLM 配置 |
| `/api/conversation/insight` | POST | ✅ | 需 LLM 配置 |
| `/api/reports/generate` | POST | ⚠️ | PDF 生成待完善 |
| `/api/reports/list` | GET | ✅ | 有 mock fallback |

---

## 实现优先级

### P0 - 必须完成（MVP 演示）

1. 文件上传与存储
2. 文件解析触发分析
3. 认证 Token 持久化
4. 前端数据绑定（概览）

### P1 - 重要（完整功能）

5. 字段映射确认 UI
6. 分析结果获取与展示
7. 报告生成与下载

### P2 - 优化（可选）

8. PDF 真实生成
9. 刷新 Token
10. 完整错误处理

---

## 配置文件

### LLM 配置（backend/.env）

```env
# LLM 设置
LLM_API_URL=http://localhost:11434/v1/chat/completions
LLM_API_KEY=ollama
LLM_MODEL=llama2

# 或使用 OpenAI
# LLM_API_URL=https://api.openai.com/v1/chat/completions
# LLM_API_KEY=your-api-key
# LLM_MODEL=gpt-3.5-turbo
```

### 环境变量检查

确保后端启动时以下环境变量存在：
- `DATABASE_URL` — PostgreSQL 连接
- `REDIS_URL` — Redis 连接
- `SECRET_KEY` — JWT 密钥

---

## 测试检查清单

### 后端测试
- [ ] `pytest tests/test_auth.py` — 认证测试
- [ ] `pytest tests/test_funnel.py` — 漏斗分析测试
- [ ] `pytest tests/test_rfm.py` — RFM 分析测试
- [ ] `pytest tests/test_llm.py` — LLM 服务测试

### API 测试
- [ ] 上传 CSV/Excel 文件成功
- [ ] 文件解析返回正确字段
- [ ] 漏斗分析返回正确结果
- [ ] 聊天接口返回有效回复

### 前端测试
- [ ] 登录后 Token 存储
- [ ] Dashboard 加载真实数据
- [ ] 文件上传进度显示
- [ ] 错误状态正确显示

---

## 文档更新记录

| 日期 | 更新内容 |
|------|----------|
| 2026-03-30 | 初始创建 |
