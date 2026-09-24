# 06 — Implementation Roadmap

本路线用于控制实现顺序，不代表必须一次完成全部功能。

## Phase 0 — Foundation

目标：建立可持续开发基线。

- frontend / backend 目录；
- React + TS + Vite；
- Ant Design；
- TanStack Router / Query；
- FastAPI；
- SQLite + SQLAlchemy + Alembic；
- health / version；
- lint / typecheck / test；
- Docker；
- CI；
- design token；
- AppShell；
- error contract。

退出条件：空业务骨架可以前后端构建、测试、Docker build。

## Phase 1 — Wafer Data Core

目标：保证数据可信，并建立可扩展但不过度抽象的多源 Parser 边界。

### 1. Canonical contracts

- WaferDataset schema；
- SourceDescriptor；
- SourceParseResult（内部）；
- ParseResult；
- ValidationIssue + stage；
- stable parser error codes。

### 2. Detection / Parsing / Assembly

- Parser base；
- deterministic detector + detection evidence；
- PAT parser；
- CP parser；
- WaferAssembler；
- PAT + CP cross-file validation；
- canonical validation。

正式链路：

```text
Source File(s)
→ Detector
→ Source Parser(s)
→ SourceParseResult[]
→ WaferAssembler
→ WaferDataset
→ Canonical Validator
→ ParseResult
```

### 3. API

- `POST /api/v1/files/parse`；
- 文件大小 / 数量 / 扩展名 / 编码限制；
- ParseResult 返回 sources + validation；
- INVALID 数据不得进入后续 Analysis。

### 4. Fixture / Simulator v1

- 正常 PAT；
- 正常 CP；
- PAT + CP；
- 空文件；
- 编码异常；
- 缺行；
- 行长度异常；
- 未知 Bin；
- Bin Count mismatch；
- Tested mismatch；
- metadata mismatch；
- extension/content mismatch；
- ambiguous detector；
- cross-file conflict；
- golden `expected.json`；
- Simulator v1：固定 seed、基础 geometry/Bin、Canonical WaferDataset、最小脱敏 PAT/CP serializer。

Phase 1 **不实现** Edge / Center / Ring / Cluster 等 pattern injection；这部分随 Phase 2 空间算法实现。

### 5. Tests / invariants

- Parser regression tests；
- exact canonical facts；
- detector tests；
- cross-file assembly tests；
- validation code tests；
- Simulator → serialize → Parser → canonical facts round-trip；
- 既有 PAT/CP 文件仅用于确认格式结构；测试数据必须重新生成并脱敏，不把其具体 Wafer 数据作为产品真值或提交 Git。

### Phase 1 退出条件

必须同时满足：

1. PAT / CP / PAT+CP golden fixture 稳定得到预期 WaferDataset；
2. detector 不只依赖扩展名，错误/歧义均有明确错误码；
3. 多源字段冲突不会被静默覆盖；
4. tested / pass / fail / bin / rows / columns / notch 等 canonical facts 可回归；
5. Simulator round-trip invariant 通过；
6. 基于已知 PAT/CP 样例格式生成的独立 synthetic golden fixture 与预设事实一致；
7. backend tests、frontend existing tests、Docker build 全部 CI 通过。

明确不进入 Phase 1：

- STDF / ATDF；
- Rust / WASM；
- Wafer renderer；
- spatial pattern；
- DBSCAN；
- Lot analysis；
- AI。

## Phase 2 — Single Wafer Analysis

### Deterministic analysis

- AnalysisSummary v1；
- Yield / Bin / fail share；
- Center / Mid / Edge；
- Top / Bottom / Left / Right；
- Q1–Q4；
- Edge / Center / directional enrichment；
- 8-neighbor connected component；
- largest component / component count / cluster ratio；
- row / column concentration；
- Pattern v1：EDGE / CENTER / RING / directional / QUADRANT / LOCALIZED_CLUSTER / LINE / RANDOM；
- FACT / JUDGMENT typed findings；
- analysis limitations；
- `POST /api/v1/analysis`；
- analysis boundary canonical re-validation。

### Simulator / tests

演示数据与回归 Fixture 的构建、命名、安全边界和三套主演示基线必须遵循 `docs/08_DEMO_DATASET_AND_REGRESSION_GUIDE.md`。

- Edge；
- Center；
- Ring；
- Quadrant；
- Cluster；
- Line；
- 单片多 Fail Bin（不同 Bin 分别注入 Edge / Center / Cluster / Ring 等特征）；
- 生产规模合成单片（16 个 Fail Bin，主 Bin 局部聚集，其余包含离散长尾）；
- 固定 seed；
- region/bin count conservation；
- enrichment formula；
- connected component exact fixture；
- API invalid-dataset regression。

### Single Wafer UI

- 单 Wafer detail page（Phase 3 起正式入口改为 `/analyses/{id}`）；
- ECharts custom-series Canvas Wafer Map；
- stable Soft Bin colors；
- PASS / FAIL；
- multi-Bin 联合筛选；
- 非目标 Bin 灰化；
- zoom / pan / reset；
- Row / Column toggle；
- Notch indicator；
- Die click Drawer；
- Bin legend interaction；
- major Fail Bin Mini Wafer Map；
- Overview / Spatial / Bin；
- PNG / CSV export；
- desktop / notebook / mobile basic view。

Phase 2 曾使用 sessionStorage 保存临时“当前 Wafer 工作区”；Phase 3 已删除该持久化路径，正式详情统一从服务端分析 ID 恢复。

### Phase 2 退出条件

必须同时满足：

1. 无 AI 可完成单 Wafer 解析 → 确定性分析 → 交互查看；
2. Yield / Bin / Region / Enrichment / Cluster 有固定回归；
3. Edge / Center / Ring / Quadrant / Cluster / Line synthetic scenario 可被算法识别；
4. Pattern evidence 与 thresholds 随结果返回；
5. Wafer Map 支持 Die、Bin、PASS/FAIL、Tooltip/Drawer、zoom/pan、Notch、PNG/CSV；
6. 主要 Fail Bin 可生成 Mini Wafer Map；
7. invalid canonical dataset 无法进入 Analysis；
8. frontend lint/typecheck/test/build、backend lint/pytest、Docker CI 全绿。

明确不进入 Phase 2：

- 数据库历史；
- Lot compare；
- DBSCAN；
- Moran's I；
- arbitrary-angle scratch fitting；
- AI。

## Phase 3 — Persistence / History

### Backend persistence

- SQLAlchemy `AnalysisRecord`；
- Alembic `0002_analysis_history`；
- indexed summary columns；
- WaferDataset JSON snapshot；
- AnalysisSummary JSON snapshot；
- SourceDescriptor / ValidationIssue snapshot；
- Repository / Service / API 分层；
- server-side canonical re-validation；
- server-side deterministic analysis recomputation；
- main_fail_bin / main_pattern summary；
- Docker startup migration。

### History API

- `POST /api/v1/analyses`；
- `GET /api/v1/analyses`；
- `GET /api/v1/analyses/{id}`；
- `DELETE /api/v1/analyses/{id}`；
- Product / Lot / Wafer / date / yield / main bin / pattern filters；
- pagination；
- stable not-found / invalid-data errors。

### Frontend

- Upload → persist → `/analyses/{id}`；
- History filters stored in URL search；
- history table only consumes summary data；
- detail loads full WaferDataset / AnalysisSummary on demand；
- restore existing Wafer Map / Spatial / Bin page；
- delete with Ant Design confirmation；
- return to History；
- remove formal sessionStorage persistence path。

### Tests

- create / restore exact snapshots；
- list does not return full dataset；
- filter regression；
- pagination；
- delete / 404；
- invalid validation issue rejected；
- server-side analysis recomputation；
- frontend history query serialization；
- History empty state；
- Alembic fresh DB upgrade；
- Docker history endpoint smoke。

### Phase 3 退出条件

1. 新分析保存后刷新浏览器仍可从 History 恢复；
2. History 列表不传输完整 Die 明细；
3. Product / Lot / Wafer / date / yield / main bin / pattern 可筛选；
4. 详情恢复使用持久化 WaferDataset + AnalysisSummary；
5. 删除后 GET 返回稳定 `ANALYSIS_NOT_FOUND`；
6. 客户端不能伪造 AnalysisSummary 进入历史真值；
7. Docker 新库自动 migration 后 History API 可访问；
8. frontend/backend/Docker CI 全绿。

明确不进入 Phase 3：

- Lot aggregate / compare；
- AI report；
- raw PAT / CP body persistence；
- PostgreSQL；
- SSO / RBAC。

## Phase 4 — Multi Wafer / Lot

- compare API；
- compatibility check；
- Yield trend；
- Bin trend；
- Enrichment trend；
- Wafer Matrix；
- Mini Map grid；
- outlier detection；
- Lot summary。

## Phase 5 — AI

- OpenAI-compatible provider；
- config；
- connection test；
- AnalysisSummary prompt；
- Pydantic output；
- AI Panel；
- retry；
- limitations；
- optional image input。

AI 只能在 Phase 1–4 的确定性事实稳定后进入。

## Phase 6 — Report / Polish

- report export；
- enhanced simulator（不得退化为单 Pattern Demo，持续维护 `PRODUCTION_PROFILE_COMPACT` / `PRODUCTION_PROFILE_SCALE` / `PROFILE_DRIFT` 主演示基线；旧 `MIXED_FAILURES` / `LONG_TAIL_MULTI_BIN` / `EDGE_DRIFT` 继续作为算法回归）；
- more parser fixtures；
- Visual QA；
- performance profiling；
- packaging / release。

## P1 / P2 Deferred

后续再评估：

- 多 Lot 趋势；
- DBSCAN；
- Moran's I；
- radial trend；
- row / column pattern；
- 工艺参数关联；
- ML pattern classifier；
- PostgreSQL；
- 企业权限。

没有明确数据与场景前，不提前开发。
