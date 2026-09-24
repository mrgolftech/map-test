# 生产参考 Synthetic Demo Suite 验收基线

## 1. 来源与边界

本套数据根据一组用户提供的生产 PAT + CP1 文件观察到的**非敏感聚合轮廓**构造。

只保留以下特征：

- 晶圆网格约为 88 × 128；
- Yield 位于 30%–40% 区间；
- 同片存在十余个非零 Fail Soft Bin；
- 主 Fail Bin 约占全部 Fail 的六成；
- 第二、第三 Fail Bin 快速衰减，之后形成明显长尾；
- 主 Fail Bin 有可检测的局部聚集成分；
- 多数较大的其他 Fail Bin 更接近离散分布；
- 少量小 Bin 可能出现 Center / Ring / Quadrant 等局部统计特征。

没有进入仓库的内容：

- 原始生产 PAT / CP；
- Product / Lot / Wafer 标识；
- 生产测试程序、设备、Probe Card 和时间；
- 原始 Die 坐标；
- 精确生产 Bin histogram；
- 能够重建生产晶圆的其他细节。

所有 Synthetic 数据均使用独立 metadata、固定 seed 和重新生成的坐标。

## 2. 主演示 A：PRODUCTION_PROFILE_COMPACT

用途：作品视频中快速展示“一张晶圆、多种 Fail Bin、不同空间性质”。

固定基线：

- seed: 20260924
- geometry: 24 × 32
- tested: 512
- pass: 190
- fail: 322
- yield: 37.109375%
- non-zero Fail Bin: 8

头部长尾：

| Bin | Count | Synthetic Description | 预期主要性质 |
| --- | ---: | --- | --- |
| 18 | 187 | RF_LOW | LOCALIZED_CLUSTER |
| 20 | 55 | RF_HIGH_A | distributed |
| 16 | 27 | BER_CHECK | distributed |
| 22 | 18 | RF_HIGH_B | distributed |
| 27 | 16 | ADC_CHECK | distributed |
| 28 | 8 | SLEEP_CURRENT | small-sample |
| 32 | 7 | DEEPSLEEP_CURRENT | CENTER / Q2 |
| 36 | 4 | MEMORY_CHECK | RING |

Bin18 采用少量局部注入 + 大量离散点，而不是画一个规则实心圆；目标 cluster ratio 为 0.25–0.40。

## 3. 主演示 B：PRODUCTION_PROFILE_SCALE

用途：验证生产规模复杂度、8k+ Die 渲染、多 Bin 筛选和真实 Parser round-trip。

固定基线：

- seed: 20260924
- geometry: 88 × 128
- tested: 8844
- pass: 3284
- fail: 5560
- yield: ~37.13%
- non-zero Fail Bin: 16

主要 Bin：

- Bin18 = 3180，Cluster + distributed；
- Bin20 = 950；
- Bin16 = 450；
- Bin22 = 300；
- Bin27 = 270；
- 其余 11 个 Bin 继续形成长尾，最低到个位数。

回归重点：

- Bin18 必须识别 LOCALIZED_CLUSTER；
- Bin18 cluster ratio 保持 0.25–0.40；
- Bin20 / 16 / 22 / 27 / 28 主要保持 RANDOM；
- Bin32 保留 CENTER；
- Bin36 保留 RING；
- 8844 颗 Die 经 Serializer → PAT/CP → real Parser 后坐标与 Soft Bin 必须逐颗一致。

## 4. 主演示 C：PROFILE_DRIFT

用途：展示 Lot 级良率趋势、主故障增强、IQR Outlier 与下钻。

5 片晶圆：

| Wafer | Fail | Yield（约） | 主 Bin cluster 注入比例 |
| --- | ---: | ---: | ---: |
| 01 | 4900 | 44.60% | 0.18 |
| 02 | 5100 | 42.33% | 0.20 |
| 03 | 5300 | 40.07% | 0.22 |
| 04 | 5560 | 37.13% | 0.27 |
| 05 | 6600 | 25.37% | 0.35 |

验收要求：

1. 5 片 compatibility = true；
2. Yield 按 Wafer01 → 05 单调下降；
3. Wafer05 稳定触发 IQR Yield Outlier；
4. 主 Fail Bin 为 Bin18；
5. Wafer05 的主 Bin cluster ratio 高于 Wafer01；
6. Lot 页面可下钻 Wafer05 查看主 Bin 及空间证据。

## 5. 与旧 Demo 的关系

- MIXED_FAILURES：保留，用于一张 Wafer 同时验证多个“教材式” Pattern；
- LONG_TAIL_MULTI_BIN：保留，作为通用大规模长尾回归；
- EDGE_DRIFT：保留，作为透明的 Edge + IQR 算法回归；
- PRODUCTION_PROFILE_* / PROFILE_DRIFT：作为最终作品的生产参考主演示。

## 6. 回归链路

所有生产参考 Synthetic Dataset 必须经过：

```text
fixed seed
→ Synthetic WaferDataset
→ deterministic AnalysisEngine
→ PAT / CP serializer
→ real Parser / Assembler / Canonical Validator
→ exact fact comparison
→ persistence
→ Lot compare（适用时）
→ Visual QA
```

AI 不参与 fixture 真值生成，也不能决定测试是否通过。
