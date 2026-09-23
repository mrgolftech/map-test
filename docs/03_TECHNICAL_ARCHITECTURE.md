# 03 — 技术架构与前后端设计准则

## 1. 总体架构

MVP 采用单体前后端分离开发、单容器可部署架构。

```text
Browser
  ↓
React SPA
  ↓ /api/v1
FastAPI
  ├─ parsers
  ├─ validation
  ├─ analysis
  ├─ ai
  ├─ persistence
  └─ simulator
        ↓
SQLite / file storage
```

开发期前后端独立启动；生产可由 FastAPI 或轻量 Web Server 提供前端 dist，并统一暴露 API。

禁止在 MVP 引入微服务、消息队列、Redis、Kubernetes 等无必要基础设施。

## 2. 前端技术基线

- React；
- TypeScript strict；
- Vite；
- Ant Design；
- Apache ECharts；
- TanStack Router；
- TanStack Query；
- Lucide React；
- Vitest；
- React Testing Library；
- Playwright。

Zustand 仅在存在明确跨页面客户端状态时引入，不能因为“可能需要”提前使用。

## 3. 前端分层

推荐：

```text
src/
├─ app/
│  ├─ router
│  ├─ providers
│  └─ theme
├─ api/
├─ components/
│  ├─ layout
│  ├─ common
│  └─ charts
├─ features/
│  ├─ dashboard
│  ├─ upload
│  ├─ wafer
│  ├─ lot
│  ├─ history
│  ├─ ai
│  └─ settings
├─ types/
├─ utils/
└─ styles/
```

### 3.1 前端职责

前端负责：

- 文件选择与上传；
- API 调用；
- 状态与错误反馈；
- Wafer / Chart 渲染；
- 筛选、排序、交互；
- 导出触发；
- 页面路由与可恢复筛选；
- AI 结果结构化呈现。

前端不负责：

- 解析 PAT / CP；
- 重新计算权威 Yield；
- 重新解释源文件 Bin；
- 确定性空间统计；
- 根因逻辑；
- LLM API Key 持有。

### 3.2 Server State

API 数据统一通过 TanStack Query 管理。

不得在多个页面各自手写 fetch + loading + error。

查询 key 必须结构化，例如：

```text
['analysis', analysisId]
['history', filters]
['lot', lotId, filters]
```

### 3.3 URL State

以下状态优先放 URL search：

- History filters；
- Dashboard filters；
- Lot filters；
- 可分享的 Wafer tab / selected bin（视体验决定）。

临时 hover、zoom、drawer open 不需要 URL 化。

## 4. 后端技术基线

- Python 3.12+；
- FastAPI；
- Pydantic v2；
- NumPy；
- Pandas 只在表格处理明显更优时使用；
- SQLAlchemy 2；
- Alembic；
- SQLite；
- pytest。

空间算法优先基于 NumPy / Python 实现，避免一开始引入大型 ML 依赖。

## 5. 后端分层

推荐：

```text
backend/app/
├─ api/
│  └─ v1/
├─ schemas/
├─ parsers/
├─ validation/
├─ analysis/
├─ ai/
├─ services/
├─ repositories/
├─ db/
├─ simulator/
└─ core/
```

依赖方向：

```text
API
 ↓
Service
 ↓
Domain Analysis / Parser / AI abstraction
 ↓
Repository / DB / external provider
```

禁止：

- Route 内堆积解析算法；
- Parser 直接写数据库；
- Analysis 直接调用 HTTP；
- AI provider 直接依赖 FastAPI Request；
- ORM Model 直接作为 API response contract。

## 6. Parser 插件与组装架构

借鉴成熟半导体解析项目的“严格解析 + 标准化”思路，并结合 PAT + CP 多源组合场景，Phase 1 采用：

```text
Source File(s)
      ↓
Format Detector
      ↓
Source Parser(s)
      ↓
SourceParseResult[]
      ↓
WaferAssembler
      ↓
Canonical WaferDataset
      ↓
Canonical Validator
      ↓
ParseResult
```

目录至少：

```text
parsers/
├─ base.py
├─ detector.py
├─ pat_parser.py
├─ cp_parser.py
└─ assembler.py
```

### 6.1 Detector

Detector 必须基于可解释 evidence：

- extension；
- magic/header/signature；
- required section / keyword；
- row/map structure。

扩展名只能作为证据之一。若多个 Parser 同时匹配且无法唯一决定，返回明确的 FORMAT_AMBIGUOUS，不猜测。

### 6.2 Source Parser

每个 Parser 只负责一个源文件格式，输出内部 SourceParseResult。

SourceParseResult 可以是不完整的。例如：

- 某文件只提供 metadata / Bin 定义；
- 某文件只提供 map rows；
- 某文件同时提供完整信息。

Parser 不要求单文件独立构造完整 WaferDataset。

### 6.3 WaferAssembler

Assembler 负责：

- 关联一个或多个 SourceParseResult；
- 合并字段来源；
- 检查 Product / Lot / Wafer / geometry 等冲突；
- 构造唯一 Canonical WaferDataset；
- 保留 source provenance。

Assembler 不负责 Yield/空间 Pattern 等 Phase 2 分析。

### 6.4 Validation 分层

至少分为：

1. source structural validation；
2. parser semantic validation；
3. cross-file / assembly validation；
4. canonical WaferDataset validation。

新增厂商格式时，应新增 Parser / assembler rule，不修改前端和确定性分析核心。

## 7. API 设计

统一前缀：

```text
/api/v1
```

MVP 至少规划：

```text
GET    /health
GET    /version

POST   /files/parse
POST   /analyses
GET    /analyses
GET    /analyses/{id}
DELETE /analyses/{id}

POST   /analyses/{id}/ai
POST   /analyses/compare

GET    /lots
GET    /lots/{lot_id}/summary

GET    /settings/llm
PUT    /settings/llm
POST   /settings/llm/test

POST   /simulator/generate
```

具体接口可在实现中微调，但变化必须同步更新文档。

`POST /files/parse` 返回 ParseResult，而不是裸 WaferDataset：

```text
ParseResult
├─ dataset?
├─ sources[]
├─ validation_issues[]
└─ status: VALID | WARNING | INVALID
```

这样前端可以显示文件探测、来源与校验信息，但仍不理解 PAT / CP 内部语法。

## 8. API 返回规范

成功：

```json
{
  "data": {},
  "meta": {}
}
```

错误：

```json
{
  "error": {
    "code": "PARSER_ROW_LENGTH_MISMATCH",
    "message": "Map row length does not match declared columns.",
    "details": {},
    "request_id": "..."
  }
}
```

错误码必须稳定、可测试、可用于前端映射。

禁止把 Python traceback 直接返回浏览器。

## 9. 上传安全

原始文件视为不可信输入。

必须限制：

- 文件数量；
- 单文件大小；
- 总大小；
- 扩展名；
- 内容编码；
- 超长单行；
- 总行数；
- 非法路径；
- zip bomb（若未来支持压缩包）；
- 上传超时。

禁止：

- 执行源文件内容；
- 根据源文件内容拼接系统路径；
- 任意路径读取；
- 将真实生产文件写进 Git。

## 10. 持久化

MVP 使用 SQLite。

推荐主要表：

```text
analysis
analysis_file
wafer_summary
ai_report
app_setting
```

WaferDataset 与 AnalysisSummary 可先以 JSON 列持久化，同时对高频查询字段做结构化列：

- product_id；
- lot_id；
- wafer_id；
- flow_id；
- yield；
- tested_die；
- pass_die；
- fail_die；
- main_fail_bin；
- created_at。

未来迁移 PostgreSQL 时不改变领域模型和 API 语义。

## 11. 原始文件存储策略

默认开发策略：

- fixture 放 `tests/fixtures/`；
- 用户上传原始文件存受控数据目录；
- DB 仅保存相对资源标识，不保存任意绝对路径；
- 删除分析时明确处理源文件保留策略。

生产文件默认不上传 GitHub、不写日志。

## 12. AI Provider 抽象

AI 层必须是 provider interface：

```text
AIProvider
├─ analyze(summary, optional_image)
├─ test_connection()
└─ capabilities()
```

默认支持 OpenAI-compatible API。

配置仅后端读取：

```text
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

前端不得接触真实 API Key。

## 13. AI 降级

AI 是 optional dependency。

以下情况核心功能必须正常：

- 无 API Key；
- Provider 超时；
- 429；
- 5xx；
- JSON 输出不合法；
- 模型不支持图像；
- 上下文超限。

AI 失败只影响 AI Panel，不影响已完成的 Parser / Analysis / History。

## 14. 性能基线

目标：

- 1 万 Die 单 Wafer 流畅交互；
- 常规页面首屏不因为完整 Die 表阻塞；
- List API 分页；
- Lot 比较优先读取预计算 summary，不重复解析原始文件；
- LLM 不发送完整数万 Die 明细；
- 统计结果在上传时计算并持久化；
- 高频趋势查询使用结构化索引字段。

## 15. 日志与可观测性

日志至少包含：

- request_id；
- operation；
- duration；
- parser type；
- analysis id；
- provider status。

禁止日志记录：

- LLM API Key；
- 原始文件全文；
- Cookie / Authorization；
- 完整敏感 prompt（生产默认）。

## 16. 配置

环境变量统一使用 `.env.example` 说明。

配置读取集中在 backend core/config，不允许模块散落 `os.getenv()`。

前端只暴露必要非敏感构建配置。
