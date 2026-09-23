# map-test

晶圆 Wafer Map 智能可视化与良率分析平台。

本项目面向晶圆 CP / MAP 测试数据，提供文件解析、标准化 Wafer 数据模型、交互式 Wafer Map、Bin/良率/空间分布分析、多 Wafer / Lot 对比、分析记录留存，以及基于结构化分析结果的 LLM 辅助诊断。

> 当前阶段：产品与技术基线定义。后续实现必须以 `AGENTS.md` 与 `docs/` 中的正式规范为准。

## 核心原则

1. 解析正确、数据可信优先于可视化，确定性分析优先于 AI。
2. 前端不得直接理解不同厂商原始 MAP 格式，统一消费标准 WaferDataset。
3. LLM 是解释与辅助诊断层，不替代确定性统计，不得把假设包装为已确认根因。
4. 产品保持轻量单体，不主动扩展成 MES、SPC 全套系统或复杂企业平台。
5. 生产晶圆原始文件属于敏感数据，未经许可不得提交公开仓库。

## 规划技术栈

- Frontend: React + TypeScript + Vite + Ant Design + Apache ECharts + TanStack Router + TanStack Query
- Backend: Python + FastAPI + Pydantic + NumPy
- Persistence: SQLite（开发及 MVP），SQLAlchemy + Alembic；架构可迁移 PostgreSQL
- Test: Vitest + React Testing Library + Playwright + pytest
- Delivery: Docker + GitHub Actions

详细规范将在 `docs/` 中维护。
