# 04 — 数据模型、解析与分析规范

## 1. Canonical WaferDataset

所有外部格式最终转换为统一模型。

概念结构：

```text
WaferDataset
├─ metadata
│  ├─ product_id
│  ├─ lot_id
│  ├─ wafer_id
│  ├─ flow_id
│  ├─ subcon
│  ├─ tester
│  ├─ test_program
│  ├─ probe_card
│  ├─ start_time
│  ├─ stop_time
│  ├─ notch
│  ├─ rows
│  └─ columns
├─ dies[]
│  ├─ row
│  ├─ column
│  ├─ source_char
│  ├─ soft_bin
│  ├─ hard_bin?
│  ├─ result
│  ├─ description
│  └─ test_values?
├─ bins[]
│  ├─ bin
│  ├─ char
│  ├─ description
│  ├─ count
│  └─ percentage
└─ summary
   ├─ tested_die
   ├─ pass_die
   ├─ fail_die
   └─ yield
```

约束：

- Row / Column 使用源文件真实坐标语义；
- 数组索引、Die Grid 坐标、显示旋转、物理坐标是不同概念；Phase 1 至少保留源坐标与 Notch，不能因 UI 需要改写；
- API 是否展示 0-based / 1-based 必须显式定义，内部推荐统一 0-based；
- source_char 必须保留；
- result 枚举固定 PASS / FAIL / UNKNOWN；
- 未测试 / 晶圆外区域不能伪造为 FAIL；
- 不存在的数据用 null，不编造默认值。

## 2. Parser / Assembly 数据契约

### 2.1 SourceDescriptor

每个上传源文件必须产生 SourceDescriptor：

```text
SourceDescriptor
├─ filename
├─ size
├─ sha256
├─ detected_format
├─ parser_id
├─ role: metadata | map | combined | unknown
└─ detection_evidence[]
```

禁止保存客户端绝对路径。

### 2.2 SourceParseResult

单个 Parser 输出内部 SourceParseResult：

```text
SourceParseResult
├─ source
├─ extracted_metadata
├─ map_rows / dies?
├─ bin_definitions?
└─ parser_issues[]
```

SourceParseResult 是内部模型，不作为前端领域契约。它允许信息不完整，以支持 PAT + CP 等多文件组合。

### 2.3 ParseResult

WaferAssembler 完成关联、合并和 canonical validation 后，API 返回：

```text
ParseResult
├─ dataset?
├─ sources[]
├─ validation_issues[]
└─ status: VALID | WARNING | INVALID
```

只有 VALID / WARNING 且不存在阻断性 ERROR 时，dataset 才可进入后续正式分析。

### 2.4 ValidationIssue

```text
severity: INFO | WARNING | ERROR
stage: DETECT | PARSE | ASSEMBLE | CANONICAL
code
message
source_file?
line?
row?
column?
details?
```

ERROR 表示结果不可信；WARNING 可以继续但 UI 必须可见。

Parser / Assembler 不输出前端 ViewModel。

## 3. 必要一致性校验

至少验证：

1. Map 实际行数 vs rows；
2. 每行长度 vs columns；
3. 已知字符映射；
4. Map 字符统计 vs Bin Count；
5. tested = pass + fail；
6. dies[].result 的实际 PASS / FAIL 数量必须与 summary 一致，UNKNOWN 不得混入 tested die；
7. pass / fail 不重复；
8. PAT / CP 关联时 Product / Lot / Wafer 等关键字段；
9. Notch 合法性；
10. 坐标唯一；
11. 空文件 / 无 Die；
12. detector 内容证据与扩展名矛盾；
13. 多源字段合并冲突；
14. SourceDescriptor checksum / size 合法；
15. map 外空白与 tested die 不混淆。

禁止为了“跑通”自动删除、填补或篡改异常 Die。

字段冲突时必须保留冲突双方和来源，不允许使用“后解析文件覆盖前文件”的隐式策略。

## 4. 基础统计

定义：

```text
yield = pass_die / tested_die
fail_rate = fail_die / tested_die
bin_rate = bin_count / tested_die
bin_fail_share = bin_count / fail_die
```

边界：

- tested_die = 0 时禁止除零，yield 为 null；
- 百分比统一由原始数值计算，显示层负责格式化；
- 后端不保存字符串 “36.10%” 作为唯一真值。

## 5. 几何归一化

空间分析需要定义晶圆有效 Die 的几何中心和归一化半径。

推荐：

- 使用有效 Die 坐标 bounding box / centroid 建立归一化坐标；
- notch 方向不改变源坐标，只影响方向语义；
- 半径 `r` 以统一归一化方式计算。

默认区域：

```text
center: r < 0.45
mid:    0.45 <= r < 0.75
edge:   r >= 0.75
```

这些参数必须配置化并写入 AnalysisSummary，避免未来改变阈值后无法解释历史结果。

## 6. Enrichment

不要使用“该 Bin 有多少比例落在 Edge”代替 Edge 异常判断。

定义：

```text
whole_bin_rate =
  bin_count / whole_tested_die

edge_bin_rate =
  edge_bin_count / edge_tested_die

edge_enrichment =
  edge_bin_rate / whole_bin_rate
```

Center 同理。

必须同时输出：

- 区域 Die 总数；
- 区域 Bin 数；
- region rate；
- whole rate；
- enrichment。

当分母太小或 0 时返回 null + limitation，不强行产生极大值。

## 7. 上下左右与象限

统一按归一化中心划分：

- Top / Bottom；
- Left / Right；
- Q1 / Q2 / Q3 / Q4。

方向必须结合 notch 元数据展示，不能在算法层偷偷旋转原始坐标。

## 8. 聚集分析

MVP 优先实现可解释算法：

- 4-neighbor 或 8-neighbor connected component；
- largest component；
- number of components；
- cluster ratio；
- average component size。

可选后续：

- DBSCAN；
- Moran's I。

Pattern 判断必须使用确定阈值和统计证据。

## 9. Pattern 结果

统一结构：

```text
PatternResult
├─ pattern
├─ score
├─ evidence[]
├─ thresholds
└─ limitations[]
```

例如：

```json
{
  "pattern": "EDGE",
  "score": 0.88,
  "evidence": [
    "edge_enrichment=2.31",
    "edge_bin_rate=0.097",
    "whole_bin_rate=0.042"
  ]
}
```

score 是算法置信度，不等于根因置信度。

Phase 2 Pattern v1 的实现范围：

- EDGE：Edge enrichment 达阈值；
- CENTER：Center enrichment 达阈值；
- RING：Mid enrichment 高，同时 Center / Edge enrichment 不高；
- TOP / BOTTOM / LEFT / RIGHT：目标半区 enrichment 高且对侧不高；
- QUADRANT：象限 enrichment 高并满足最小样本量；
- LOCALIZED_CLUSTER：8-neighbor connected component + cluster ratio；
- LINE：行/列集中度；
- RANDOM：未满足上述确定性阈值的 fallback。

默认阈值必须随 AnalysisSummary 一起返回，不得只存在代码中。

## 10. Line / Scratch

MVP 可以用轻量启发式：

- Fail 点线性拟合残差；
- 行 / 列集中；
- connected component 长宽比；
- principal direction。

只有满足阈值才标记 Line，不能凭图片肉眼判断。

Phase 2 仅实现行/列方向 Line detection。任意角度直线拟合、PCA principal direction 与更完整 scratch detection 暂缓，AnalysisSummary limitations 必须明确这一点。

## 11. AnalysisSummary

LLM、Lot 比较、报告统一消费 AnalysisSummary。

建议：

```text
AnalysisSummary
├─ schema_version = "1.0"
├─ metadata
├─ summary
├─ validation
├─ config
│  ├─ center_radius
│  ├─ edge_radius
│  ├─ neighbor_mode
│  ├─ enrichment_threshold
│  ├─ cluster_ratio_threshold
│  ├─ min_cluster_size
│  ├─ directional_enrichment_threshold
│  └─ line_concentration_threshold
├─ bin_stats[]
├─ region_stats
├─ spatial_by_bin[]
├─ patterns[]
├─ top_findings[]
│  ├─ kind: FACT | JUDGMENT
│  └─ text
└─ limitations[]
```

必须版本化 `schema_version`。

## 12. 多 Wafer 可比性

比较前进行 compatibility check。

优先要求：

- product_id 相同；
- flow_id 相同；
- map geometry 可兼容；
- Bin 定义可解释。

Test Program / Tester / Probe Card 不同可以比较，但必须作为条件变量显示，不得隐藏。

不可比数据可以展示，但综合统计必须给出 limitation。

## 13. Lot 统计

至少计算：

- wafer_count；
- avg_yield；
- median_yield；
- std_yield；
- min / max；
- per-bin mean / std；
- per-bin trend；
- enrichment trend；
- outlier flags。

MVP 离群值算法使用透明方法，例如 IQR / z-score，并记录规则。

## 14. 模拟数据

Simulator 不能直接写测试期望结果。

正确模式：

```text
配置 pattern
→ 生成 die/bin 数据
→ 走真实 AnalysisEngine
→ 测试算法是否识别预期模式
```

固定 fixture 必须有 seed 与 expected facts。

单片多失效合成场景必须保留每个 Fail Bin 的 Die 数、占比和独立空间统计；
Bin 是测试分类，Pattern 是空间特征，同一晶圆可以有多个 Bin 和多个 Pattern。
演示数据只借鉴多 Bin 共存这一业务语义，不拷贝生产晶圆的坐标、计数或标识。
生产规模合成 fixture 可借鉴网格尺寸、失效类别数量与头部长尾特征，
但所有 Die 坐标、Bin 计数、标识、描述必须独立生成；回归测试用 PAT/CP 走实际 Parser。

## 15. LLM 输入边界

禁止默认发送：

- 整个原始 PAT / CP 文本；
- 数万条完整 Die；
- API Key；
- 本地路径；
- 与诊断无关的敏感元数据。

优先发送压缩后的 AnalysisSummary。

生产规模多 Bin 场景中，Pattern 输入优先按对应 Bin 数量与确定性证据选取，
确保主 Fail Bin 的 Cluster 等结论不会被小样本高分 Pattern 挤出截取窗口。
可保留少量主要 RANDOM Bin 作为对照；小样本 Pattern 必须伴随 Bin 数量与局限性。
Cluster Ratio 与象限富集是不同聚合统计；输入未提供最大簇的精确位置时，
AI 不得声称最大簇位于某一象限。
当前 OpenAI-compatible 默认输出上限为 8192 tokens，以容纳模型内部推理与完整 JSON。
若上游返回 `finish_reason=length`，按截断响应报错，不把残缺 JSON 作为正常诊断。
对已保存的同 Product、同 Lot 多片晶圆，单片 AI 分析会附带兼容的 Lot
确定性比较摘要（Yield 趋势、离群标识、主 Bin 聚集比）；报告仍保存于当前分析记录。
只传结构化数字和限制，不传 Lot Mini Map 或逐 Die 坐标。

报告追问输入已保存 AIReport、当前 AnalysisSummary 的确定性指标白名单，以及最近 12 条
对话。多 Wafer / Lot 追问输入兼容性结果、确定性比较摘要和各片的 Bin / Pattern 指标；
不传完整 Die 列表或晶圆渲染图。回答返回 citation IDs，服务端只接受当前上下文白名单
中的引用，并将已解析的标签和值与问答一起保存。未知引用被剔除并触发证据不足标记。
聊天回答使用纯文本，不依赖 Markdown 库。

## 16. LLM 输出校验

模型返回必须经过 Pydantic schema 校验。
AIReport 的所有顶层字段都必须存在；数组允许为空但不能缺失。

解析失败：

- 保存原始 provider error metadata；
- 不覆盖上一次成功报告；
- UI 显示 AI Failed；
- 允许重试。

模型给出的 possible_causes 必须呈现为假设。


## 17. Analysis API 数据可信边界

`POST /api/v1/analysis` 接收 WaferDataset 时，必须再次执行 canonical validation。

原因：即使 Pydantic 类型合法，客户端仍可能提交逻辑不一致的数据，例如：

- tested_die 与 dies[] 数量不一致；
- tested != pass + fail；
- Bin Count 与 Die 不一致；
- 重复坐标；
- 坐标越界。

存在 canonical ERROR 时返回 `ANALYSIS_DATASET_INVALID`，不得进入空间统计。

## 18. Phase 2 当前坐标算法

当前几何使用 tested-die bounding box：

1. 取 tested die 的 min/max row/column；
2. 中点作为归一化中心；
3. x/y 分别按半宽、半高归一化；
4. radius 使用 x/y 欧氏距离，并按当前 tested die 最大 radius 再归一化至 0–1；
5. Top 定义为源 row 较小方向，Right 定义为源 column 较大方向；
6. Notch 只用于方向展示，不旋转源坐标。

该方法适用于当前 Map 分析，但不是物理 mm 坐标。将来若文件提供 Die pitch / wafer diameter / origin，可新增 physical geometry adapter，不能静默改变已有 AnalysisSummary 语义。
