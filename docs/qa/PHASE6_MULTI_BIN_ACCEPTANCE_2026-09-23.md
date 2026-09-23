# Phase 6 单片多失效演示验收

## 用户反馈与结论

生产样例表明单片晶圆可能同时包含多个非零 Fail Soft Bin。原演示页虽然已有 `MULTI_PATTERN`（两个 Fail Bin）和随机多 Bin 的 PAT/CP fixture，却将单片入口主要组织成单一空间 Pattern；这不足以直观验收多类失效共存。

现新增独立 `MIXED_FAILURES` 合成单片入口。它使用固定 seed `20260924`，24 × 32 网格、512 颗有效 Die，展示 6 个 Fail Bin。Bin 是测试类别，Pattern 是该 Bin 的空间分布；同一 Bin 也可能触发多项确定性 Pattern 判断。

| Soft Bin | 合成描述 | Die 数 | 注入分布 |
| --- | --- | ---: | --- |
| 1 | PASS | 212 | 其余有效 Die |
| 18 | Pout_min | 165 | Edge |
| 20 | Pout_max | 60 | Center |
| 16 | BER_RESULT | 36 | Localized cluster |
| 22 | Pout_margin | 21 | Ring |
| 27 | GADC | 12 | Random |
| 28 | ICC_sleep | 6 | Random |

Tested 512、Pass 212、Fail 300、Yield 41.40625%。这些坐标、数量、比例、名称及元数据都是 Simulator 人工合成，不是生产文件的脱敏拷贝。原始生产 PAT/CP 未提交。

## 验收操作与结果

1. 在“新建分析”点击“生成单片多失效演示（6 个 Fail Bin）”。
2. 确认主图同时显示 6 类 Fail Bin，图例及前三个主 Fail Bin 小图显示各自数目。
3. 在 Overview 查看主要及其他 Fail Bin 的 count / fail share；在 Spatial 页查看各 Bin 的 Pattern 及证据。
4. 用合成 PAT/CP fixture 经真实 Parser 往返，核对所有 Die 坐标及 Bin 数守恒。

浏览器实测：1280 宽新建页、Overview、Spatial 和 390 宽新建页均加载成功；按钮生成后进入持久化分析；空间结果含 EDGE、CENTER、LOCALIZED_CLUSTER、RING；控制台及 HTTP 4xx/5xx 错误为 0；390 宽全局 scrollWidth 为 390。

## 测试与资产

- `backend/tests/fixtures/mixed_failures/DEMO.01.PAT`、`DEMO.CP1`、`expected.json`：固定 seed 的纯合成文件及预期事实。
- 后端 `ruff check backend`、`compileall`、`pytest backend/tests -q`：77 项通过；新增生成、参数拒绝、独立 Pattern 与 PAT/CP 往返验证。
- 前端 `npm run lint`、`npm run typecheck`、`npm test`（22 项）、`npm run build`：通过。
- [新建页，1280](assets/mixed-failures-upload-1280.png)、[多失效 Overview，1280](assets/mixed-failures-overview-1280.png)、[多失效 Spatial，1280](assets/mixed-failures-spatial-1280.png)、[新建页，390](assets/mixed-failures-upload-390.png)。

已知限制：这个固定合成场景仅验证多 Bin 共存与确定性空间分析，不能代表真实产品的失效率或根因。Pattern score 是算法特征置信度，不等于失效原因确认；一个 Bin 可能同时满足多个阈值。前端构建仍有主 bundle 超过 500 kB 的提示，与原 Phase 6 报告一致。
