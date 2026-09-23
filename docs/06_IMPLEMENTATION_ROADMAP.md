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
- 私有真实样例在受控环境做一次外部交叉验证，但不得提交 Git。

### Phase 1 退出条件

必须同时满足：

1. PAT / CP / PAT+CP golden fixture 稳定得到预期 WaferDataset；
2. detector 不只依赖扩展名，错误/歧义均有明确错误码；
3. 多源字段冲突不会被静默覆盖；
4. tested / pass / fail / bin / rows / columns / notch 等 canonical facts 可回归；
5. Simulator round-trip invariant 通过；
6. 私有实际样例的关键统计与既有人工/工具结果一致；
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

- Yield；
- Bin；
- region；
- enrichment；
- cluster；
- pattern v1；
- Wafer Map；
- Bin filtering；
- Die tooltip；
- PNG / CSV；
- 单片详情页。

退出条件：无 AI 也能完整完成一片 Wafer 的工程分析。

## Phase 3 — Persistence / History

- Analysis record；
- SQLite persistence；
- History API；
- History page；
- filtering；
- restore；
- deletion；
- migration tests。

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
- enhanced simulator；
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
