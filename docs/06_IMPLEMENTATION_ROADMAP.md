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

目标：保证数据可信。

- WaferDataset schema；
- Parser base / detector；
- PAT parser；
- CP parser；
- ValidationIssue；
- parse API；
- fixture；
- Simulator v1；
- parser regression tests。

退出条件：固定 PAT / CP 与模拟 fixture 均可得到可信标准数据。

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
