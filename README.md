# map-test

晶圆 Wafer Map 智能可视化与良率分析平台。

本项目面向晶圆 CP / MAP 测试数据，提供文件解析、标准化 Wafer 数据模型、交互式 Wafer Map、Bin/良率/空间分布分析、多 Wafer / Lot 对比、分析记录留存，以及基于结构化分析结果的 LLM 辅助诊断。

## 当前能力

MVP 主链路已经实现：

```text
PAT / CP
→ 格式探测与 Parser
→ canonical WaferDataset
→ 确定性单片分析
→ 交互 Wafer Map
→ SQLite 历史
→ Multi-Wafer / Lot 对比
→ 可选 LLM 辅助诊断
→ HTML / PDF 归档报告
```

主要能力包括：

- PAT / CP / PAT+CP 解析、来源证据、交叉校验和明确错误码；
- Yield、Bin、Center/Mid/Edge、方向/象限、Enrichment、Cluster、Pattern 分析；
- ECharts Canvas Wafer Map、PASS/FAIL/Bin 筛选、Die 详情、PNG/CSV 导出；
- 分析历史持久化与筛选；
- Lot Yield/Bin/空间趋势、IQR 异常、Wafer Matrix 和 Mini Map；
- OpenAI-compatible LLM Provider，结构化 FACT/JUDGMENT/HYPOTHESIS/RECOMMENDATION 输出；
- AI 报告随分析历史持久化，LLM 不可用时仍可恢复已保存报告；
- 脱敏 Simulator：单 Pattern Golden Set、单片多 Fail Bin、生产规模长尾多 Bin、演示 Lot；
- 独立 HTML 工程报告，可由浏览器打印/另存为 PDF。

## 核心原则

1. 解析正确、数据可信优先于可视化，确定性分析优先于 AI。
2. 前端不得直接理解不同厂商原始 MAP 格式，统一消费标准 WaferDataset。
3. LLM 是解释与辅助诊断层，不替代确定性统计，不得把假设包装为已确认根因。
4. 产品保持轻量单体，不主动扩展成 MES、SPC 全套系统或复杂企业平台。
5. 生产晶圆原始文件属于敏感数据，未经许可不得提交公开仓库。

## 技术栈

- Frontend: React + TypeScript + Vite + Ant Design + Apache ECharts + TanStack Router + TanStack Query
- Backend: Python + FastAPI + Pydantic + NumPy
- Persistence: SQLite + SQLAlchemy + Alembic；架构可迁移 PostgreSQL
- Test: Vitest + React Testing Library + pytest
- Delivery: Docker + GitHub Actions

## LLM 配置

AI 是可选能力；未配置时 Parser、确定性分析、Wafer Map、History 和 Lot compare 均正常工作。

服务端环境变量：

```text
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

API Key 不会返回前端，也不得写入 Git 或日志。

## 开发必读

- `AGENTS.md`：仓库级开发强制约束
- `docs/00_PRODUCT_REQUIREMENTS.md`：产品定位、MVP、非目标、成功标准
- `docs/01_PAGE_AND_INFORMATION_ARCHITECTURE.md`：页面、导航和信息架构
- `docs/02_UI_DESIGN_SYSTEM.md`：UI Design System、图表与 Wafer Map 规范
- `docs/03_TECHNICAL_ARCHITECTURE.md`：前后端架构、API、持久化、AI Provider、性能与安全
- `docs/04_DATA_MODEL_PARSING_AND_ANALYSIS.md`：WaferDataset、Parser、Validation、空间算法与 AnalysisSummary
- `docs/05_ENGINEERING_TEST_AND_DELIVERY.md`：工程、测试、CI、Docker、敏感数据与 DoD
- `docs/06_IMPLEMENTATION_ROADMAP.md`：实现顺序与阶段退出条件
- `docs/07_REFERENCE_PROJECTS_AND_ADOPTED_PRACTICES.md`：上游参考项目与采用边界
- `docs/08_DEMO_DATASET_AND_REGRESSION_GUIDE.md`：演示样本、Synthetic Fixture、作品验收与回归测试基线

## 实现优先级

```text
Parser / Validation
→ Canonical WaferDataset
→ Deterministic Analysis
→ Wafer Visualization
→ Persistence / History
→ Multi-Wafer / Lot
→ AI Explanation
→ Report / Delivery Polish
```

未经明确架构决策，不改变上述优先级。
