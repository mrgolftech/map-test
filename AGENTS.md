# AGENTS.md — map-test 仓库开发约束

本文件是 ChatGPT / Codex / 其他代码 Agent / 开发者进入仓库时必须优先读取的操作规范。

## 1. 信息源优先级

判断“当前已经实现什么”严格按：

1. 当前 `main` 实际代码；
2. DB schema / migration / workflow / 配置；
3. 本 `AGENTS.md`；
4. `docs/` 当前规范；
5. README；
6. PR / Issue；
7. 聊天历史与旧方案。

聊天说明意图，main 说明事实。不得脱离源码凭空假设仓库状态。

## 2. 开发前必须阅读

按任务读取：

1. `docs/00_PRODUCT_REQUIREMENTS.md`
2. `docs/01_PAGE_AND_INFORMATION_ARCHITECTURE.md`
3. `docs/02_UI_DESIGN_SYSTEM.md`
4. `docs/03_TECHNICAL_ARCHITECTURE.md`
5. `docs/04_DATA_MODEL_PARSING_AND_ANALYSIS.md`
6. `docs/05_ENGINEERING_TEST_AND_DELIVERY.md`
7. `docs/06_IMPLEMENTATION_ROADMAP.md`
8. `docs/07_REFERENCE_PROJECTS_AND_ADOPTED_PRACTICES.md`

产品、架构、数据契约或 UI 基线发生变化时，必须同步相应文档。

## 3. 产品定位

map-test 是轻量 Wafer Map 智能可视化与良率分析平台。

核心链路：

```text
PAT / CP / MAP
→ Parser
→ WaferDataset
→ deterministic analysis
→ visualization / history / lot comparison
→ LLM explanation
```

禁止无需求扩展成 MES、完整 SPC、多租户 SaaS、微服务平台或复杂 ML 系统。

## 4. 核心优先级

任何功能冲突时遵循：

```text
解析正确
> 数据可信
> 确定性统计
> Wafer 可视化
> 多 Wafer / Lot 比较
> AI 解释
```

AI 不能替代 Parser、统计或空间算法。

## 5. Canonical Data

不同厂商源文件必须通过 Parser 转换为统一 WaferDataset。

前端、数据库展示、Lot compare、AI 均消费标准模型。

禁止：

- 前端解析 PAT / CP；
- 页面根据 source_char 猜 Bin；
- AI 从图片反推权威 Yield；
- 将未知数据静默当 PASS / FAIL；
- 自动篡改不完整源数据使其“看起来正确”。

## 6. Parser 强制规则

Parser 使用 plugin + assembler 模式：

```text
Source File(s)
→ detector.py
→ pat_parser.py / cp_parser.py / future parser
→ SourceParseResult[]
→ assembler.py
→ WaferDataset
→ canonical validation
→ ParseResult
```

目录至少包含：

```text
base.py
detector.py
pat_parser.py
cp_parser.py
assembler.py
```

不得假设单个源文件一定包含构造完整 WaferDataset 所需的全部信息；PAT / CP 应先独立解析，再由 assembler 关联。

必须保留：

- Row / Column；
- source_char；
- Soft Bin；
- 晶圆外空白；
- Notch；
- source metadata。

必须校验：

- rows / columns；
- line length；
- Bin Count；
- Tested = Pass + Fail；
- PAT / CP 关键 metadata；
- unknown char。

异常必须显式返回 ValidationIssue。

格式探测必须给出可解释 evidence；扩展名只能作为证据之一。检测结果冲突或歧义时必须显式报错，不得猜测。

Parser 不直接承担空间统计、Renderer 或持久化职责。

## 7. Analysis 强制规则

空间结论必须来自确定性算法和数字证据。

至少支持：

- Yield；
- Bin ranking；
- Center / Mid / Edge；
- Top / Bottom；
- Left / Right；
- Quadrant；
- Edge / Center Enrichment；
- Cluster；
- Pattern。

不要仅根据“看图感觉”生成 Edge / Ring / Cluster 结论。

算法参数与阈值必须可追踪并进入 AnalysisSummary。

## 8. AI 强制规则

LLM 是解释层。

默认输入：

- metadata；
- summary；
- bin stats；
- spatial stats；
- patterns；
- trends；
- limitations。

默认不发送巨大原始 Map / 完整 Die 列表。

输出必须区分：

- FACT；
- JUDGMENT；
- HYPOTHESIS；
- RECOMMENDATION。

possible cause 永远是待验证假设，除非输入中已有确认性证据。

LLM 不可用时核心产品必须正常。

## 9. 前端基线

统一：

- React；
- TypeScript strict；
- Vite；
- Ant Design；
- ECharts；
- TanStack Router；
- TanStack Query；
- Lucide React。

Zustand 仅在确有跨页面客户端状态时使用。

UI 修改必须先读 `docs/02_UI_DESIGN_SYSTEM.md`。

禁止：

- 再引入第二套完整 UI 框架；
- 自研 Ant Design 已有基础组件；
- 多个页面复制不同 Page Header / Card / Filter；
- 业务组件散落硬编码颜色；
- DOM 一 Die 一节点渲染大 Wafer；
- 页面自行计算权威 Yield / Spatial 指标。

Wafer Bin palette 与系统 light/dark theme 解耦并保持稳定。

## 10. 后端基线

统一：

- Python 3.12+；
- FastAPI；
- Pydantic v2；
- NumPy；
- SQLAlchemy 2；
- Alembic；
- SQLite；
- pytest。

Route 轻薄，Parser / Analysis / AI / Persistence 解耦。

外部输入全部不可信，必须在 API / Parser 边界校验。

## 11. 数据库

MVP SQLite。

schema 修改必须 migration。

高频查询字段结构化存储，WaferDataset / AnalysisSummary 可 JSON 持久化。

架构需允许未来迁移 PostgreSQL，但不得为了未来可能性提前复杂化。

## 12. 敏感数据

未经用户明确许可，禁止将真实生产晶圆文件提交 GitHub。

禁止提交：

- LLM API Key；
- .env；
- Token / Cookie；
- 运行数据库；
- 原始生产 PAT / CP / MAP；
- 含敏感生产信息的日志。

回归测试优先使用脱敏 fixture / simulator。

## 13. 分支和 PR

除极小文档修正外：

```text
main
→ task branch
→ code
→ test
→ review
→ PR
→ CI
→ squash merge
```

推荐：

- `feature/...`
- `fix/...`
- `refactor/...`
- `docs/...`
- `ci/...`
- `deploy/...`

功能分支合并后删除。

## 14. 开始任务前

至少检查：

```bash
git status
git branch
git log -5 --oneline
git pull
```

使用 GitHub 工具时直接读取当前源码、PR、Actions，不凭记忆猜测。

## 15. 前端完成条件

至少：

```bash
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

涉及 UI：

- 390 / 1280 / 1920；
- light / dark；
- loading / empty / error；
- 必要 Playwright / visual QA。

## 16. 后端完成条件

至少：

```bash
python -m compileall
pytest
lint
```

涉及 Parser / Analysis 必须运行固定 fixture 回归。

涉及 schema 必须验证 fresh DB + migration。

## 17. Bug 修复

优先：

```text
reproduce
→ root cause
→ minimal fix
→ regression test
→ relevant full test
```

不要为一个实际 Bug 大范围重构正常代码。

## 18. 完成后的报告

每次开发后必须报告：

1. 修改内容；
2. 关键文件；
3. 测试结果；
4. 已知风险；
5. 下一步建议。

并明确区分：

- 代码完成；
- 测试完成；
- CI 完成；
- 合并；
- Release；
- 部署；
- 用户验收。

## 19. 架构变更纪律

以下属于重大变更，不能作为顺手优化：

- 更换前端框架 / UI library；
- 更换后端框架；
- 修改 WaferDataset；
- 修改 AnalysisSummary；
- 改 Parser contract；
- 更换数据库；
- 引入消息队列 / 微服务；
- 改 AI 输出 schema；
- 改 Pattern 定义；
- 改空间区域算法定义。

如确需修改，先说明问题、影响、迁移方式和测试计划，再同步文档与实现。


## 20. 参考项目使用纪律

实现 Parser、Wafer Renderer、空间分析或 Lot 比较前，可参考 `docs/07_REFERENCE_PROJECTS_AND_ADOPTED_PRACTICES.md` 中登记的上游项目。

强制规则：

- map-test 实际需求、源码与真实文件语义优先；
- 参考项目只用于借鉴成熟工程实践、测试方法和领域概念；
- 不因为参考项目已有某功能就扩大当前阶段范围；
- 不自动引入其依赖、框架或技术栈；
- 复制代码前必须确认许可证；无明确许可证默认只参考思路；
- PAT / CP 私有格式不得根据公开 STDF/ATDF 项目猜测字段语义。
