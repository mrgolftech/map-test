# 生产文件参考下的合成测试集验收

## 参考边界

用户提供的一组生产 PAT/CP 在本地经现有 Parser 关联，返回 `VALID`、无 ValidationIssue。
用它观察到的是大尺寸晶圆、同片多个 Fail Soft Bin、一个占比较大的主 Bin 与多个长尾 Bin。
确定性分析提示主 Bin 有局部聚集成分，而数个其他大 Bin 更接近离散分布。

这与先前用于验证算法的 512 Die / 6 Fail Bin 的 Edge + Center + Ring 演示用途不同。
因此另增 `LONG_TAIL_MULTI_BIN` 固定 seed 合成场景，专门覆盖大尺寸和头部长尾分布。
输入生产文件未进入仓库、fixture、测试快照或截图；合成数据没有复用生产坐标、Bin 数量或生产标识。

## 合成数据事实

| 指标 | 结果 |
| --- | ---: |
| 网格 | 88 × 128 |
| Tested | 8844 |
| Pass / Fail | 3284 / 5560 |
| 非零 Fail Bin | 16 |
| 主 Bin | Bin 18，2700 Die，局部聚集 + 离散点 |
| 后续 Bin | Bin 20 为 1100、Bin 16 为 560、Bin 22 为 370；其余 12 个 Bin 从 300 递减至 10 |

所有 Soft Bin 对应一个明确的 description、char、Die count 与 percentage。
分布由 `seed=20260924` 和 Simulator 算法生成，非原始生产图的改名副本。

## 复现与验收

- 在“新建分析”选择“生成生产规模多 Bin 测试集（16 个 Fail Bin）”，查看 Wafer 主图、Bin 图例、主要 Fail Bin 小图、Spatial 与 Bin 页。
- 或上传 `backend/tests/fixtures/long_tail_multibin/DEMO_SCALE.01.PAT` 和 `DEMO_SCALE.CP1`，对照同目录 `expected.json`。
- 回归测试固定 seed、Bin count 守恒、主 Bin 的 `LOCALIZED_CLUSTER`、其他常见 Bin 的 `RANDOM`，以及 PAT/CP 经真实 Parser 往返时每颗 Die 的坐标和 Bin 一致性。
- Chromium 浏览器点击生成后，核对 8844 Tested、3284 Pass、5560 Fail、16 个 Fail Bin；Canvas 分帧绘制结束后确认主图和主要 Bin 小图完整。Spatial 页显示主 Bin 局部聚集；浏览器 JS 与 HTTP 错误均为 0。
- [1280 宽 Overview 截图](assets/long-tail-overview-1280.png)。
- 该场景用于解析、渲染和分析验收；算法给出的 Pattern 是空间统计，不是根因诊断。
