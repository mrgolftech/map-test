# Phase 6 浏览器视觉与功能验收

## 基线与结论

- 基线：`main` 提交 `b2b74f40f011b81433391dfe2f6d8ce8c071de95`。
- 方法：从上述 GitHub 文件树取得完整源码；安装锁定前端依赖和后端开发依赖；SQLite 空库执行 Alembic 至 head；构建前端，由 FastAPI 提供构建产物；用本地 Chromium + Playwright 操作实际页面。
- 数据：仅使用仓库内 `backend/tests/fixtures/synthetic_demo/` 的合成 PAT/CP 和 Simulator。无生产数据、无真实 LLM 密钥。
- 结果：主要用户链路通过；修复 Wafer 布局越界及重复生成演示 Lot 混批。浏览器未记录 JS 异常或 HTTP 4xx/5xx。

## 验收矩阵

| 场景 | 操作与核对 | 结果 |
| --- | --- | --- |
| 空状态 | 空库打开总览，展示引导提示 | 通过 |
| PAT + CP 上传 | 同时选择 `SYNTH001.01.PAT` 和 `SYNTH001_20260101090000.CP1`，解析为 VALID，保存进入分析 | 通过；512 Tested、358 Pass、154 Fail、69.92% Yield |
| 单片 Simulator | EDGE 场景创建分析；查看 Map、Bin 图例、确定性结论 | 通过；512 Tested、464 Pass、48 Fail、90.62% Yield |
| Wafer 交互 | Spatial、Bin、AI 标签切换；FAIL / 全部筛选；明暗主题 | 通过；AI 显示未配置状态 |
| 导出 | 从 Wafer 页点击 CSV、HTML 工程报告、PNG | 通过；均触发对应文件下载 |
| 历史 | 检索页加载已保存记录，窄屏表格可横向浏览 | 通过 |
| Lot | EDGE_DRIFT 生成、趋势、异常、Matrix、Mini Map | 通过；5 片、平均 Yield 88.59%、异常 1 片 |
| 重复生成 | 连续生成相同场景，检查两个 Lot ID 与每批 5 片 | 通过；不会混为 10 片同批数据 |
| 设置 | 查看 LLM 服务端配置状态，未配置时连接测试不可用 | 通过 |
| 响应布局 | 390、1280、1920 宽；亮色和暗色；390 Wafer 页全局无横向溢出 | 通过 |

## 视觉修复

1. `frontend/src/styles/globals.css`：原 `.wafer-main-grid .ant-card { height: 100%; }` 同时撑满右侧 Bin 卡片，Notch 提示进入下一节区域；限制为左侧主 Map 卡片。手机宽度下 Map 卡片标题和操作区改为换行，标题完整可读。
2. `frontend/src/features/upload/UploadPage.tsx`：每次生成演示 Lot 时添加短随机后缀，同次生成的 5 片共享新 Lot ID，重复点击不会污染上一批趋势。
3. `frontend/src/features/history/HistoryPage.test.tsx`：历史页 Ant Design 表单在当前 CI 类环境中约需 7 秒渲染，单用例超时由 5 秒调整为 15 秒，断言不变。

## 本地检查

- 前端：`npm ci`、`npm run lint`、`npm run typecheck`、`npm test`（14 文件、22 用例）、`npm run build` 均通过。
- 后端：`python -m compileall -q app`、`python -m ruff check .`、`python -m pytest`（74 用例）通过；空库迁移至 `0003_ai_report_persistence` 通过。
- 浏览器：实际 HTTP 接口与 UI 操作通过；页面 JS / console error 数为 0，HTTP 4xx/5xx 数为 0。
- 构建提示：前端主 bundle 约 2.43 MB，Vite 提醒超过 500 kB；属于后续按路由拆包的性能优化项。

## 截图证据

- [空总览，1280 亮色](assets/dashboard-empty-1280-light.png)
- [合成 PAT/CP 解析，1280 亮色](assets/pat-cp-parse-1280-light.png)
- [Wafer EDGE，1280 亮色](assets/wafer-edge-1280-light.png)
- [Wafer，390 暗色](assets/wafer-390-dark.png)
- [Lot 对比，1280 暗色](assets/lot-1280-dark.png)
- [历史，390 暗色](assets/history-390-dark.png)
- [上传，390 暗色](assets/upload-390-dark.png)
- [设置，390 暗色](assets/settings-390-dark.png)
- [Lot 列表，1920 暗色](assets/lot-1920-dark.png)

截图浏览器额外加载了测试环境中文字体，以弥补容器缺少中文字库；该字体没有加入产品包。用户浏览器若本身缺中文字体，仍需系统提供字体回退。

## 验收边界

- 本轮未接入真实 OpenAI-compatible LLM，因此没有验证实际模型响应质量、时延和 AI 报告持久化的在线路径；Mock 单元测试仍通过。
- 未用生产 PAT/CP 或其他厂商格式验证 Parser；本轮结论仅对仓库合成 fixture 与 Simulator 成立。
- 截图和下载来自本地 Chromium，未部署到公网，也不代表生产环境的网络与权限配置。
