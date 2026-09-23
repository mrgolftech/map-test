# 05 — 工程、测试与交付准则

## 1. 信息源优先级

判断项目现状按以下顺序：

1. 当前 `main` 实际代码；
2. schema / migration / workflow / 配置；
3. `AGENTS.md`；
4. `docs/` 当前规范；
5. README；
6. PR / Issue；
7. 聊天历史。

文档与代码冲突时，先判断是代码偏离规范还是规范已过期，不得盲目回退。

## 2. 分支工作流

除极小文档修复外：

```text
main
→ feature/fix/refactor/docs/ci branch
→ implementation
→ tests
→ review diff
→ PR
→ CI
→ squash merge
→ main
```

功能开发不得长期直接在 main 上堆提交。

## 3. 前端代码准则

- TypeScript strict；
- 禁止大量 `any`；
- Props / API DTO / domain type 分离；
- 页面只组合功能，不堆积底层实现；
- 图表配置与数据转换分离；
- Wafer renderer 与业务筛选逻辑分离；
- 不重复实现 Ant Design 已有成熟组件；
- 公共视觉模式进入 shared component；
- API 调用集中在 api layer；
- server state 使用 TanStack Query；
- 可恢复筛选优先 URL state。

## 4. 后端代码准则

- 全量类型提示；
- Pydantic 负责 API boundary；
- Parser / Analysis / Persistence / AI 解耦；
- Route 轻薄；
- domain calculation 尽量纯函数；
- 外部输入必须校验；
- DB schema 变化必须 migration；
- 错误码显式；
- 不捕获异常后静默继续；
- 不用 Pandas 解决简单循环 / 数组任务。

## 5. 测试金字塔

### Parser

必须覆盖：

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
- PAT / CP metadata mismatch。

### Analysis

使用固定 fixture 验证：

- Yield；
- Bin count；
- Center / Edge；
- Quadrant；
- Edge Enrichment；
- Center Enrichment；
- Cluster；
- Edge Pattern；
- Center Pattern；
- Ring；
- Quadrant；
- Line；
- Random 不误判。

### API

覆盖：

- upload validation；
- parse error mapping；
- create / list / get / delete；
- compare；
- AI unavailable；
- provider timeout；
- invalid AI JSON；
- health / version。

### Frontend

至少覆盖：

- page render；
- loading / empty / error；
- filter；
- Bin selection；
- History list；
- AI result type rendering；
- theme；
- key navigation。

### E2E

Playwright 覆盖主路径：

```text
上传 fixture
→ 解析成功
→ 打开 Wafer
→ 筛选 Fail Bin
→ 查看 Spatial
→ 保存历史
→ 历史恢复
→ 多 Wafer compare
```

## 6. 性能测试

至少验证：

- 10k Die；
- 20k Die（压力边界，非必须生产目标）；
- 10 / 50 / 100 Wafer 历史列表；
- 10–25 Wafer Lot compare；
- 图表切换与 Bin filter。

Wafer Map 交互性能不能依赖 DOM 为每颗 Die 创建节点。

## 7. 测试数据

真实生产文件：

- 不进入公开仓库；
- 原则上不进入任何 Git；
- 如需回归测试，脱敏并最小化。

测试优先使用 simulator 生成 fixture。

fixture 必须说明：

- seed；
- geometry；
- expected yield；
- injected pattern；
- expected main bin。

## 8. CI

GitHub Actions 至少执行：

### Frontend

```text
npm ci
lint
typecheck
test
build
```

### Backend

```text
install
lint
pytest
```

### Integration

- Docker build；
- 可选 smoke test `/api/v1/health`。

任何 Release 前 CI 必须全绿。

## 9. Docker

MVP 允许单镜像：

```text
build React
→ copy dist
→ FastAPI runtime
→ static + /api/v1
```

SQLite 与上传目录必须挂载持久卷。

禁止将真实 `.env` 和 API Key COPY 进镜像。

## 10. 配置与秘密

提交：

- `.env.example`；
- 默认非敏感值。

禁止提交：

- `.env`；
- LLM API Key；
- 真实生产 Token；
- 数据库运行文件；
- 生产晶圆文件。

## 11. Definition of Done

一个功能完成必须区分：

- code complete；
- unit tests complete；
- integration tests complete；
- frontend typecheck/build complete；
- backend pytest complete；
- diff reviewed；
- CI green；
- merged；
- released；
- deployed；
- user acceptance。

不得把“代码写完”描述成“发布完成”。

## 12. Bug 修复

实际 Bug 修复优先增加回归测试。

流程：

```text
reproduce
→ identify root cause
→ minimal fix
→ regression test
→ full relevant test
→ review unrelated change
```

不为了修一个 Bug 顺手大规模重构。

## 13. 文档同步

以下变化必须同步文档：

- Product scope；
- route / page；
- UI token / shared pattern；
- WaferDataset；
- AnalysisSummary；
- API；
- DB schema；
- Parser contract；
- AI schema；
- deployment。

如果设计决策与当前文档冲突，应先明确变更原因，再修改实现。

## 14. Review Checklist

每次 PR 至少检查：

- 是否修改了 canonical data semantics；
- 是否引入重复 UI；
- 是否有硬编码 Bin 颜色；
- 是否把计算移到了前端；
- 是否让 AI 替代确定性事实；
- 是否泄露原始文件 / Key；
- 是否吞掉 parser error；
- 是否有测试；
- 是否影响历史数据 schema；
- 是否可回滚。
