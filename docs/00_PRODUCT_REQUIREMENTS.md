# 00 — 产品需求基线

## 1. 产品定位

map-test 是一个轻量级的 **Wafer Map 智能可视化与良率分析平台**，服务于晶圆 CP / MAP 测试数据的解析、可视化、统计、空间异常识别、多 Wafer / Lot 对比与工程辅助诊断。

产品目标不是替代 MES、完整 SPC 或企业级良率管理系统，而是提供一个工程师可以快速使用的分析工作台：

```text
原始 PAT / CP / MAP 文件
→ 格式探测与解析
→ 标准 WaferDataset
→ 确定性统计与空间分析
→ Wafer / Lot 可视化
→ 分析记录留存
→ LLM 辅助解释与排查建议
```

### 1.1 核心价值

系统必须回答以下问题：

- 这片 Wafer 的 Tested / Pass / Fail / Yield 是多少？
- 主要 Fail Bin 是什么，占比多少？
- Fail 是否存在 Edge、Center、Ring、Quadrant、Cluster、Line 等空间模式？
- 异常是单片随机问题，还是同 Lot 多 Wafer 的持续趋势？
- 哪些 Wafer、Bin、区域最值得优先排查？
- 基于确定性数据，可能有哪些原因与下一步验证动作？

## 2. 目标用户

MVP 面向：

- 晶圆测试 / 产品工程师；
- 良率 / 失效分析工程师；
- 研发与制造质量相关人员；
- 需要快速查看 CP/MAP 测试结果的工程人员。

MVP 不做复杂用户权限、多租户、企业组织架构与审批流。

## 3. P0 / MVP 范围

### 3.1 文件导入与解析

必须支持：

- 单文件上传；
- PAT；
- CP1 / 类 CP Map；
- PAT + CP 成对上传并尝试关联；
- 多源文件先独立探测/解析，再关联组装为唯一 WaferDataset；
- 文件格式自动探测，并向用户返回探测依据与源文件角色；
- 编码异常、空文件、缺行、行长度异常、未知 Bin 等明确报错；
- 原始 Row / Column 保留；
- 晶圆外空白区域保留语义；
- Notch 识别；
- Map 行列校验；
- Bin Count 与 Map 字符数量交叉校验；
- Tested = Pass + Fail 校验；
- 多文件 Product / Lot / Wafer / geometry 冲突校验；
- 每个源文件保留 filename / size / sha256 / detected format 等 provenance。

禁止静默修正无法解释的数据错误，也禁止通过解析顺序覆盖冲突字段。

### 3.2 标准数据模型

所有 Parser 输出统一为 WaferDataset。前端、统计模块、数据库和 LLM 不得直接依赖厂商原始文件格式。

核心结构：

```text
WaferDataset
├─ metadata
├─ dies[]
├─ bins[]
└─ summary
```

字段详见 `04_DATA_MODEL_PARSING_AND_ANALYSIS.md`。

### 3.3 单 Wafer 可视化

必须支持：

- 每颗 Die 独立色块；
- PASS / FAIL；
- Soft Bin 稳定颜色映射；
- Tooltip：Row、Column、Char、Bin、Description、PASS/FAIL；
- 点击 Die 查看详情；
- Zoom / Pan；
- Notch；
- Row / Column 坐标；
- 仅 PASS；
- 仅 FAIL；
- 单 Bin；
- 多 Bin 联合筛选；
- 非目标 Bin 灰化；
- Bin 图例联动；
- 主 Fail Bin 小型 Wafer Map；
- PNG 导出；
- Die CSV 导出。

### 3.4 确定性统计与空间分析

至少实现：

- Yield；
- Bin 排名；
- Fail Bin 占比；
- Center / Mid / Edge；
- Top / Bottom；
- Left / Right；
- Q1 / Q2 / Q3 / Q4；
- Edge Fail Rate；
- Center Fail Rate；
- Edge Enrichment；
- Center Enrichment；
- Largest Cluster；
- Cluster Ratio；
- 基础空间聚集程度；
- 典型模式分类：Random / Edge / Center / Ring / Top / Bottom / Left / Right / Quadrant / Localized Cluster / Line。

空间判断必须给出数字依据。

### 3.5 历史记录

分析完成后必须可以保存和恢复：

- 原始文件基本信息；
- WaferDataset；
- AnalysisSummary；
- AI 报告；
- 分析时间；
- Product / Lot / Wafer；
- Yield / 主要 Fail Bin；
- 文件校验状态。

支持按 Product、Lot、Wafer、时间筛选与检索。

### 3.6 多 Wafer / Lot 分析

支持一次选择多个历史 Wafer 或同 Lot Wafer，输出：

- Yield 趋势；
- Tested / Pass / Fail；
- Top Fail Bin 趋势；
- 各 Bin 占比趋势；
- Edge / Center Enrichment 趋势；
- Pattern 对比；
- Wafer 对比矩阵；
- 最佳 / 最差 Wafer；
- Lot 平均值、标准差、离群 Wafer；
- 结构化综合分析摘要。

MVP 重点是同 Product / 同测试条件下的多 Wafer 比较，不强行比较不可比的数据。

### 3.7 AI 辅助诊断

LLM 只消费结构化事实，默认不直接依赖大图识别。

输入优先为：

- metadata；
- summary；
- Bin 排名；
- 空间统计；
- Pattern 结果；
- 多 Wafer 趋势；
- 数据校验告警。

如 API 支持多模态，可附加 Wafer Map PNG 作为辅助上下文，但数值事实仍以算法计算为准。

AI 输出必须结构化：

```json
{
  "executive_summary": "",
  "key_findings": [],
  "spatial_patterns": [],
  "possible_causes": [],
  "recommended_checks": [],
  "confidence": 0.0,
  "limitations": []
}
```

展示时明确区分：

- 【事实】数据直接计算；
- 【判断】算法 / 统计模式结论；
- 【假设】可能原因；
- 【建议】下一步验证动作。

禁止输出“已确认根因”，除非输入中存在可验证证据。

## 4. Wafer Simulator

模拟器属于正式测试能力，不是临时脚本。

至少生成以下 fixture：

- normal_random；
- edge_fail；
- center_fail；
- ring_fail；
- top_fail；
- quadrant_fail；
- cluster_fail；
- scratch_line_fail；
- multi_pattern；
- mixed_failures：单片晶圆同时含多个 Fail Soft Bin，展示不同 Bin 的空间分布；
- long_tail_multi_bin：大尺寸单片、主要失效 Bin 与多个长尾 Bin 共存；
- yield_drift_lot。

模拟器最终必须支持：

- Row / Column；
- wafer shape；
- Notch；
- PASS 基线；
- 多个 Soft Bin；
- Pattern 参数；
- Fail Rate；
- 随机种子；
- Lot / Wafer 序号；
- 输出标准 WaferDataset；
- 可选生成脱敏 PAT / CP fixture。

Phase 1 的 Simulator v1 只要求：可重复生成合法 WaferDataset、基础 Bin/geometry，并可生成最小 PAT / CP 解析 fixture；Edge/Ring/Cluster 等 Pattern 注入在 Phase 2 随空间算法实现。

固定 seed 的 fixture 必须可重复。

## 5. 非目标

MVP 明确不做：

- MES 全功能；
- 全套 SPC；
- 多租户 SaaS；
- SSO / LDAP；
- 复杂 RBAC；
- 消息队列；
- 微服务；
- Kubernetes；
- 实时设备采集；
- 工艺参数自动关联；
- ML 根因模型；
- 自动工艺决策；
- 大规模数据湖。

任何新增范围必须先说明业务价值、数据来源与测试方式。

## 6. 产品成功标准

MVP 被视为成立至少满足：

1. PAT / CP fixture 可稳定解析；
2. 同一 Wafer 的关键统计与源文件一致；
3. 1 万 Die 级 Wafer Map 可流畅交互；
4. 典型空间 fixture 可由算法稳定识别；
5. 历史分析可保存、检索、恢复；
6. 多 Wafer / Lot 可形成趋势与比较；
7. LLM 输出严格基于 AnalysisSummary；
8. LLM 不可用时平台核心分析仍完整可用；
9. 前后端测试与 Docker 构建通过。
