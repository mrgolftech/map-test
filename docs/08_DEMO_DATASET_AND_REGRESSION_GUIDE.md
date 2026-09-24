# 08 — 演示样本数据与回归测试基线

## 1. 目的

本文件定义 map-test 的演示数据、Synthetic Fixture、作品验收样本与回归测试准则。

它解决两个问题：

1. **作品演示要接近真实晶圆分析逻辑**：一张晶圆通常可能同时存在多个 Fail Soft Bin，不应把最终 Demo 简化成“一张 Wafer 只有一种故障 Pattern”。
2. **演示数据必须可重复、可验证、可回归**：所有展示结论都必须能由 Parser 与确定性 AnalysisEngine 重算得到，而不是为了画面效果直接写死结果。

后续新增或修改 Simulator、Golden Fixture、Visual QA、作品视频样本、Lot 演示数据时，必须遵守本文。

---

## 2. 核心原则

优先级：

```text
数据可信
> 可重复生成
> 确定性分析可验证
> 接近真实复杂度
> 演示效果
> AI 解释
```

强制规则：

- 演示数据必须为独立 Synthetic 数据，不得把生产 PAT / CP 改名后提交；
- 可参考生产数据的**聚合特征**，例如大尺寸、多 Bin、头部长尾、局部聚集，但不得复用生产坐标、精确 Bin 计数、产品标识或敏感元数据；
- 固定场景必须固定 seed；
- Simulator 只负责注入数据分布，不直接写 AnalysisEngine 的预期结论；
- Synthetic Dataset 必须走真实 `AnalysisEngine`；
- PAT / CP Fixture 必须经过真实 Serializer → Parser → Assembler → Canonical Validation；
- Pattern 是某个 Fail Bin 的空间分布判断，不是整张 Wafer 唯一标签；
- Pattern score 是算法特征置信度，不是根因置信度；
- AI 根因描述只能作为 HYPOTHESIS，不能成为 fixture 的“标准答案”。

---

## 3. 测试集分层

### L1 — Algorithm Golden Set

用途：验证单个确定性算法，不作为最终作品的主要演示内容。

必须保留独立固定场景：

- EDGE
- CENTER
- RING
- TOP
- BOTTOM
- LEFT
- RIGHT
- QUADRANT
- CLUSTER / LOCALIZED_CLUSTER
- LINE
- RANDOM

每个场景至少固定：

- seed；
- rows / columns；
- tested / pass / fail；
- Soft Bin；
- 预期 Pattern；
- Pattern evidence 的关键数值或允许范围；
- 使用的 AnalysisConfig / threshold。

L1 的目标是回答：

> 算法是否真的能识别已知空间分布？

不得仅通过截图肉眼判断。

---

### L2 — 单片多失效主演示集

作品单 Wafer 演示的默认主场景为：

```text
PRODUCTION_PROFILE_COMPACT
```

该场景不是生产文件的缩小版，而是根据生产样例中可复用的**聚合轮廓**重新生成：

- Yield 位于 30%–40% 区间；
- 一个主 Fail Bin 约占全部 Fail 的六成；
- 第二、第三 Fail Bin 快速衰减；
- 主 Fail Bin 有可识别的局部聚集；
- 多数较大 Fail Bin 仍接近离散分布；
- 少量小 Bin 可出现 Center / Ring 等局部模式。

当前 Synthetic 基线：

| Soft Bin | Synthetic Description | Die Count | 设计特征 |
| --- | --- | ---: | --- |
| 1 | PASS | 190 | Remaining tested dies |
| 18 | RF_LOW | 187 | Cluster + distributed |
| 20 | RF_HIGH_A | 55 | RANDOM |
| 16 | BER_CHECK | 27 | RANDOM |
| 22 | RF_HIGH_B | 18 | RANDOM |
| 27 | ADC_CHECK | 16 | RANDOM |
| 28 | SLEEP_CURRENT | 8 | RANDOM |
| 32 | DEEPSLEEP_CURRENT | 7 | Q2 / CENTER |
| 36 | MEMORY_CHECK | 4 | RING |

固定事实：

```text
seed = 20260924
grid = 24 × 32
tested = 512
pass = 190
fail = 322
yield = 37.109375%
non-zero fail bins = 8
```

核心回归断言：

- Bin18 必须识别为 LOCALIZED_CLUSTER，cluster ratio 保持在 0.25–0.40；
- Bin32 必须包含 CENTER；
- Bin36 必须包含 RING；
- Bin20 / Bin16 等主要次头部 Bin 不应被人为强制成规则 Pattern；
- 所有 Fail Bin count 之和等于 fail_die；
- 每颗 tested Die 只属于一个 Soft Bin；
- Main Wafer Map、Bin Legend、主要 Fail Bin Mini Map 和 Spatial 页面应能同时呈现多类失效。

原 `MIXED_FAILURES` 保留，用于“一张 Wafer 同时验证 EDGE / CENTER / CLUSTER / RING”的算法展示，但不再作为生产参考主演示。

---

### L3 — 生产规模多 Bin 压力与真实性演示集

默认场景：

```text
PRODUCTION_PROFILE_SCALE
```

设计只保留生产样例的聚合特征，不复用真实坐标、精确 Bin histogram 或生产标识。

当前 Synthetic 基线：

```text
seed = 20260924
grid = 88 × 128
tested = 8844
pass = 3284
fail = 5560
yield ≈ 37.13%
non-zero fail bins = 16
```

Fail Bin 基线：

| Soft Bin | Description | Count |
| --- | --- | ---: |
| 18 | RF_LOW | 3180 |
| 20 | RF_HIGH_A | 950 |
| 16 | BER_CHECK | 450 |
| 22 | RF_HIGH_B | 300 |
| 27 | ADC_CHECK | 270 |
| 28 | SLEEP_CURRENT_LV | 130 |
| 30 | SLEEP_CURRENT_HV | 80 |
| 32 | DEEPSLEEP_CURRENT | 50 |
| 35 | LOGIC_CHECK | 40 |
| 19 | TX_CURRENT | 30 |
| 36 | MEMORY_CHECK | 25 |
| 21 | RF_HIGH_C | 20 |
| 33 | WAKE_CHECK | 15 |
| 23 | DEVIATION_CHECK | 10 |
| 26 | CURRENT_CHECK | 5 |
| 12 | MODE_CHECK | 5 |

设计要求：

- Bin18 由约 27% 注入局部 Cluster、其余重新随机分布组成；
- Bin18 AnalysisEngine cluster ratio 应稳定在 0.25–0.40；
- Bin20 / Bin16 / Bin22 / Bin27 / Bin28 应保持主要为 RANDOM；
- Bin32 必须包含 CENTER；
- Bin36 必须包含 RING；
- 不能要求所有长尾 Bin 都得到显著 Pattern，小样本偶发方向/象限命中必须结合样本量解释；
- 该场景用于 8k+ Die 渲染、筛选、Mini Map、CSV / PNG、Spatial/Bin 页与 Parser round-trip 回归；
- 另保留独立 10k / 20k Die 性能测试，不用修改本场景来凑性能数字。

原 `LONG_TAIL_MULTI_BIN` 继续作为通用长尾多 Bin 回归，不再承担生产参考真值。

---

### L4 — Lot 趋势与异常主演示集

最终作品的生产参考 Lot 主场景：

```text
PROFILE_DRIFT
```

5 片 Wafer 使用相同 88 × 128 geometry 和同一长尾 Bin family，仅改变 Fail 总量与主 Bin 聚集强度：

| Wafer | Fail Die | Yield（约） | 主 Bin 注入 cluster fraction |
| --- | ---: | ---: | ---: |
| 01 | 4900 | 44.60% | 0.18 |
| 02 | 5100 | 42.33% | 0.20 |
| 03 | 5300 | 40.07% | 0.22 |
| 04 | 5560 | 37.13% | 0.27 |
| 05 | 6600 | 25.37% | 0.35 |

目标：

- 展示 Yield trend 持续恶化；
- 展示主 Fail Bin 数量与 cluster ratio 同步增强；
- 第 5 片必须触发当前 IQR Yield Outlier；
- 支持从 Lot Overview 下钻 Wafer05，再定位到主 Bin18 与 LOCALIZED_CLUSTER；
- 所有 Wafer 必须通过 compatibility check；
- Lot 中各片坐标都重新生成，不能由单片生产 Map 直接复制或做简单比例缩放。

辅助 Lot 场景继续保留：

- `EDGE_DRIFT`：透明验证 IQR 和 Edge enrichment 的算法 Golden；
- `MIXED_PATTERNS`：不同 Wafer 分别注入 EDGE / CENTER / RING / CLUSTER / LINE；
- `STABLE_RANDOM`：无明显异常，用于验证系统不会必然制造 Outlier。

---

## 4. 最终作品演示只突出三套数据

正式演示、截图与视频默认突出：

1. **典型多失效晶圆** → `PRODUCTION_PROFILE_COMPACT`
2. **生产规模多 Bin 晶圆** → `PRODUCTION_PROFILE_SCALE`
3. **批次良率异常追踪** → `PROFILE_DRIFT`

L1 的 EDGE / CENTER / RING 等单 Pattern 场景继续保留，但主要用于算法验证和开发调试，不应占据最终作品的大量演示时间。

推荐作品叙事：

```text
PAT / CP
→ 自动格式识别和交叉校验
→ canonical WaferDataset
→ 一片晶圆拆解多个 Fail Bin
→ 每个 Bin 独立空间统计和 Pattern 识别
→ 数字证据 / enrichment / cluster
→ AI 基于事实生成假设和排查建议
→ Lot 趋势发现异常 Wafer
→ 下钻到具体 Bin 和空间分布
```

---

## 5. Fixture 构建规范

每个正式 Demo Scenario 应优先提供：

```text
backend/tests/fixtures/<scenario>/
├─ *.PAT
├─ *.CP1
└─ expected.json
```

`expected.json` 至少包含：

- scenario；
- seed；
- geometry；
- product / lot / wafer（Synthetic 标识）；
- tested / pass / fail / yield；
- Bin count；
- 关键 Pattern 期望；
- 关键 enrichment / cluster 允许范围（适用时）；
- Parser status；
- expected ValidationIssue；
- schema / fixture version。

不得只保存截图作为测试真值。

---

## 6. Round-trip 回归

正式 Synthetic Fixture 必须验证：

```text
Scenario config
→ Synthetic WaferDataset
→ PAT / CP serializer
→ real Parser
→ WaferAssembler
→ Canonical Validator
→ WaferDataset
→ AnalysisEngine
→ expected facts / patterns
```

至少校验：

- source rows / columns；
- Die 坐标；
- source_char；
- Soft Bin；
- Bin Count；
- tested / pass / fail；
- Yield；
- Notch；
- PAT / CP metadata 一致性；
- Pattern；
- 关键 Pattern evidence。

如果 Serializer / Parser round-trip 后坐标或 Bin 发生变化，测试必须失败，禁止静默修正。

---

## 7. 回归测试矩阵

### Parser

三套主演示至少验证：

- PAT only（适用时）；
- CP only（适用时）；
- PAT + CP；
- canonical exact facts；
- Bin Count conservation；
- no unexpected ValidationIssue。

### Analysis

必须验证：

- 单 Bin Golden Pattern；
- 单片多 Bin 独立 Pattern；
- Random 不被强制解释；
- region count conservation；
- enrichment 公式；
- connected component；
- Pattern evidence / thresholds；
- 生产规模数据不会因 Bin 数量增加而丢失统计。

### Persistence / History

主演示数据创建 Analysis 后必须能：

- 刷新恢复；
- History 查询；
- 下钻详情；
- 删除；
- 恢复同一 AnalysisSummary snapshot。

### Lot

`PROFILE_DRIFT` 必须验证：

- compatibility；
- wafer_count = 5；
- yield trend 单调恶化；
- 第 5 片 IQR outlier；
- 主 Bin18 fail count / cluster ratio 的跨片变化；
- Bin / enrichment trend；
- Wafer Matrix / Mini Map。

`EDGE_DRIFT` 继续保留为 IQR + Edge 的透明算法 Golden。

### AI

CI 使用 Mock Provider。

必须验证：

- 输入来自 AnalysisSummary，不依赖原始 PAT / CP；
- 输出 schema 合法；
- FACT / JUDGMENT / HYPOTHESIS / RECOMMENDATION 边界；
- provider unavailable 时不影响确定性分析；
- 不把 Pattern 自动等同于已确认根因。

---

## 8. Visual QA 基线

涉及 Wafer UI 或 Simulator 修改时，至少用 L2 和 L3 做浏览器验收。

建议视口：

- 390 px；
- 1280 px；
- 1920 px。

至少检查：

- 主 Wafer Map 完整；
- Notch 和坐标方向；
- Soft Bin 颜色稳定；
- PASS / FAIL / 多 Bin 筛选；
- 非目标 Bin 灰化；
- Tooltip / Die Drawer；
- 主要 Fail Bin Mini Map；
- Overview / Spatial / Bin；
- 多 Bin 图例无截断；
- 8k+ Die Canvas 绘制完成后无缺块；
- JS error / HTTP 4xx / 5xx 为 0（预期错误场景除外）。

UI 截图可作为验收证据，但不能替代数值回归。

---

## 9. 用户可见命名

内部 Scenario ID 保持稳定，便于 API 与测试引用；最终产品入口优先使用用户能理解的名称：

| Internal ID | 推荐用户可见名称 |
| --- | --- |
| PRODUCTION_PROFILE_COMPACT | 典型多失效晶圆（生产参考） |
| PRODUCTION_PROFILE_SCALE | 生产规模多 Bin 晶圆 |
| PROFILE_DRIFT | 批次良率异常追踪 |
| MIXED_FAILURES | 多 Pattern 单片算法演示 |
| LONG_TAIL_MULTI_BIN | 通用长尾多 Bin 回归 |
| EDGE_DRIFT | Edge / IQR 算法回归 |
| MIXED_PATTERNS | 多空间模式 Lot |
| STABLE_RANDOM | 稳定基线 Lot |

不要让最终作品主要依赖开发术语解释场景价值。

---

## 10. 变更控制

以下修改视为 Demo Baseline 变化：

- seed；
- geometry；
- Die count；
- Bin ID / description / count；
- 注入 Pattern；
- expected Pattern；
- Lot wafer 数；
- Outlier 设计；
- expected.json schema。

修改时必须同步：

1. Simulator；
2. Fixture；
3. expected.json；
4. backend regression；
5. frontend / Visual QA（受影响时）；
6. 本文基线；
7. 相关 QA 报告。

禁止为了让测试通过而只修改 expected 结果；必须说明基线为什么需要变化。

---

## 11. 数据安全边界

生产文件只允许用于：

- 确认 Parser 格式语义；
- 观察非敏感聚合特征；
- 本地问题复现（经授权）。

默认禁止进入 Git 的内容：

- 原始生产 PAT / CP / MAP；
- 真实 Product / Lot / Wafer ID；
- 精确生产坐标集合；
- 可反推出具体批次的 Bin histogram；
- 生产测试程序、设备、时间等敏感元数据。

如需构造“生产参考 Synthetic Dataset”，必须重新生成：

- ID；
- 坐标；
- Bin count；
- 比例；
- 时间；
- metadata。

并在文档中明确标记：

```text
Synthetic / Not Production Data
```

---

## 12. 验收结论模板

每个主演示 Scenario 完成后，验收报告至少回答：

1. **事实**：Tested / Pass / Fail / Yield / Bin Count 是否符合 expected；
2. **Parser**：PAT / CP 是否通过真实解析与交叉校验；
3. **Analysis**：预期空间特征是否由确定性算法识别；
4. **Evidence**：关键 enrichment / cluster / concentration 数值是什么；
5. **UI**：主图、筛选、小图、Spatial/Bin 页面是否正确；
6. **Performance**：规模场景是否流畅且无缺块；
7. **AI**：是否严格基于结构化事实，是否把原因保持为假设；
8. **安全**：是否确认无生产原始数据进入仓库。

只有上述链路一致时，才能称为“演示样本通过回归验收”。
