# Production Profile Demo Fixtures

本目录定义最终作品使用的三套生产参考 Synthetic 演示数据。

> Synthetic / Not Production Data

这些数据仅参考生产样例的聚合特征，例如大尺寸、多 Fail Bin、头部长尾和主 Bin 局部聚集。仓库中不包含用户提供的原始生产 PAT / CP，不复用生产坐标、精确生产 Bin histogram、Product/Lot/Wafer ID、测试程序、设备或时间。

## 正式主演示

1. `PRODUCTION_PROFILE_COMPACT`
   - 用户名：典型多失效晶圆（生产参考）
   - 24 × 32
   - 512 Tested
   - 8 个非零 Fail Bin
   - 用于快速展示单片多失效、Bin 下钻和空间分析。

2. `PRODUCTION_PROFILE_SCALE`
   - 用户名：生产规模多 Bin 晶圆
   - 88 × 128
   - 8844 Tested
   - 16 个非零 Fail Bin
   - 用于生产规模 Wafer Map、多 Bin 筛选、Parser round-trip 和性能验收。

3. `PROFILE_DRIFT`
   - 用户名：批次良率异常追踪
   - 5 × 8844 Tested
   - Yield 逐片下降，主 Bin 聚集增强
   - Wafer05 设计为 IQR Yield Outlier。

## 数据真值

`manifest.json` 是演示数据的仓库级 expected baseline，固定：

- seed；
- geometry；
- Tested / Pass / Fail / Yield；
- Bin count；
- Pattern；
- Lot wafer 数；
- Outlier 预期。

修改这些字段属于 Demo Baseline 变更，必须同步 Simulator、测试和 `docs/08_DEMO_DATASET_AND_REGRESSION_GUIDE.md`。

## 生成可上传 PAT / CP

在 `backend/` 目录执行：

```bash
python -m app.simulator.demo_assets --output ./generated/production_profile_demo
```

会生成：

```text
production_profile_compact/
  PROFILE_COMPACT.01.PAT
  PROFILE_COMPACT.CP1

production_profile_scale/
  PROFILE_SCALE.01.PAT
  PROFILE_SCALE.CP1

production_profile_lot/
  PROFILE_DRIFT.01.PAT
  PROFILE_DRIFT_01.CP1
  ...
  PROFILE_DRIFT.05.PAT
  PROFILE_DRIFT_05.CP1
```

这些文件可直接用于产品上传演示，也可由测试代码在临时目录重建。

## 回归原则

CI 不信任生成器自身的返回值。正式回归链路是：

```text
manifest expected
→ fixed-seed generator
→ PAT / CP serializer
→ real FileParseService
→ Parser / Assembler / Canonical Validator
→ AnalysisEngine
→ Lot compare
→ compare expected facts
```

因此 Parser、Analysis 或 Simulator 任一侧发生不兼容时，测试应显式失败。
