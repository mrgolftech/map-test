# 07 — 参考项目与采纳原则

> 最后核对：2026-09-23。参考项目用于验证设计方向、借鉴成熟工程实践与测试思路；不得因为“别人这样做”而自动引入依赖、改变技术栈或扩大当前阶段范围。

## 1. 参考优先级

### 1.1 wafertools/wafermap

仓库：https://github.com/wafertools/wafermap  
许可证：MIT  
定位：浏览器端 Wafer Map 渲染、空间统计、Cluster、Lot 趋势、Gallery。

重点采纳：

- **数据 / 统计 / 渲染分层**：core、stats、renderer、canvas-adapter/worker 各自独立；
- Wafer Map 与业务页面解耦，renderer 不负责 Parser；
- Bin 颜色稳定、PASS/FAIL 显示一致；
- Cluster / Pattern / Regions / Yield / Lot Trend 均有独立测试；
- 使用性能测试与 safety invariants 防止 Wafer Map 交互退化；
- Canvas 相关主题、Tooltip、Selection、Viewport 单独处理；
- 多 Wafer Gallery 与单 Wafer renderer 复用同一数据语义。

map-test 的对应约束：

```text
Parser / WaferDataset
        ↓
Deterministic Analysis
        ↓
View Model Adapter
        ↓
ECharts / Canvas Renderer
```

严禁在 React 页面组件中混合 Parser、统计和渲染实现。

### 1.2 wafertools/tsmap

仓库：https://github.com/wafertools/tsmap  
许可证：MIT  
定位：完整 Wafer Viewer / Lot Gallery，支持多种半导体测试文件格式。

重点采纳：

- 文件输入先经过 Parser，再进入统一内部数据模型；
- 多格式支持通过独立 Parser 扩展，不让 UI 理解格式差异；
- 单 Wafer、Lot Gallery、Insights、Report 使用相同领域数据；
- 完整应用中的“文件 → 标准数据 → Viewer → Insights → Lot”链路与 map-test 目标一致。

明确不采纳：

- 当前阶段不引入 Rust/WASM/Tauri；
- Phase 1 不增加 STDF / ATDF / Parquet 等格式；
- 不为了对齐 tsmap 而改变 React + FastAPI 技术路线。

### 1.3 Semi-ATE/STDF

仓库：https://github.com/Semi-ATE/STDF  
许可证：MIT  
定位：Python STDF 解析库。

重点采纳其 Parser 工程原则：

- 工业测试数据可能存在不完整、错误或边界情况；
- Parser 应显式检查格式与记录一致性；
- 原始信息优先保留，不以“能继续跑”为理由静默修正；
- 格式解析、合法性校验、标准化应有清晰边界；
- 错误信息必须可定位、可测试。

明确不采纳：

- Phase 1 不实现 STDF；
- 不将 STDF Record 模型硬套到 PAT / CP；
- 仅借鉴 Parser 的严格性与测试方法。

### 1.4 cap1tan/wafermap

仓库：https://github.com/cap1tan/wafermap  
许可证：MIT  
定位：Python Wafer geometry / map plotting。

重点采纳：

- Die Grid、Wafer Shape、Notch、Origin、Offset 是不同几何概念；
- 空间分析不得把数组索引直接等价为物理晶圆坐标；
- 源 Row / Column 必须保留；
- 坐标方向、Notch 与显示旋转必须分离；
- 后续 Edge / Center / Scratch 分析需要明确几何语义。

明确不采纳其 Python UI / plotting 作为 Web 渲染核心。

### 1.5 wafer-defect-analyzer

仓库：https://github.com/Hassankusow/wafer-defect-analyzer  
定位：DBSCAN、systematic / random defect、yield model。

仅作为后续空间算法参考：

- DBSCAN；
- Cluster density；
- systematic vs random defect；
- defect/yield modeling。

**不进入 Phase 1。** 在 Phase 2/P2 是否采用，必须基于固定 fixture 与可解释性评估。

### 1.6 semiconductor_test_toolkit

仓库：https://github.com/mstarefinaktar/semiconductor_test_toolkit  
定位：STDF、Wafer Map、Yield、Shmoo、统计与异常检测。

参考用途：

- 后续 Cp/Cpk、outlier、test-value analysis；
- 对照半导体测试工程常见功能。

不作为 map-test 架构来源，不自动引入其依赖或算法。

## 2. 参考项目使用纪律

开发涉及 Parser、Wafer Renderer、空间统计或 Lot 分析前，可检查上述项目当前源码与测试，但必须遵守：

1. **当前 map-test 需求和实际生产文件优先于参考项目。**
2. 只借鉴与当前任务直接相关的模式，不做“功能追平”。
3. 新依赖必须有本项目独立理由，不能仅因为参考项目使用。
4. 复制代码前必须确认许可证与 attribution 要求；无明确许可证的仓库默认只参考思路，不复制代码。
5. 不复制参考项目的领域假设来解释 PAT / CP 私有格式。
6. 参考代码进入本项目后必须符合 map-test 的类型、测试、错误码和目录规范。
7. 上游项目更新不会自动触发同步；只有能解决实际问题或降低风险时才评估。

## 3. 对 Phase 1 的直接设计结论

参考上述项目后，Phase 1 调整为：

```text
Source Files
    ↓
Format Detector
    ↓
Source Parser(s)
    ↓
SourceParseResult[]
    ↓
Wafer Assembler
    ↓
Canonical WaferDataset
    ↓
Canonical Validation
    ↓
ParseResult
```

关键原因：

- PAT 与 CP 可能分别提供不同信息，不能假设每个 Parser 都能独立构造完整 WaferDataset；
- 需要保留“哪个字段来自哪个源文件”的来源信息；
- 单文件格式和多文件组合格式必须共用同一 API；
- 新格式以后只新增 Parser / assembler rule，不修改前端和分析核心。

### 3.1 Phase 1 新增的内部概念

#### SourceDescriptor

至少包含：

- filename；
- size；
- sha256；
- detected_format；
- parser_id；
- role（metadata / map / combined / unknown）；
- detection_evidence[]。

不得保存客户端绝对路径。

#### SourceParseResult

Parser 的内部输出，包含：

- source descriptor；
- format-specific extracted metadata；
- map rows / die records（如该源提供）；
- bin definitions（如该源提供）；
- parser issues[]。

SourceParseResult 是内部模型，不暴露给前端作为领域契约。

#### WaferAssembler

负责：

- 将一个或多个 SourceParseResult 关联；
- 处理字段来源；
- 检测 PAT / CP metadata 冲突；
- 生成唯一 Canonical WaferDataset；
- 不进行空间模式分析。

#### ParseResult

API 返回的解析结果：

```text
ParseResult
├─ dataset?
├─ sources[]
├─ validation_issues[]
└─ status: VALID | WARNING | INVALID
```

ERROR 存在时默认 status=INVALID；不得把不可信 dataset 当作正式分析输入。

## 4. Phase 1 不增加的范围

参考项目虽然已有更多能力，但当前阶段明确不增加：

- STDF / ATDF；
- Rust / WASM Parser；
- DBSCAN；
- Moran's I；
- Pattern Classification；
- Lot Trend；
- Wafer Renderer；
- AI；
- test-value statistical analysis。

这些能力继续按现有 Roadmap 进入后续阶段。


## 5. PAT / CP 样例格式与 synthetic 数据原则

已知 PAT / CP 文件仅作为**格式样例**使用，用于确认：

- PAT 的头部字段组织、Notch 表达和定长字符 Map；
- CP 的 `[BOF]`、`[SOFT BIN]`、`[SOFT BIN MAP]`、`[EXTENSION]`、`[EOF]` 段结构；
- Soft Bin 单字符编码方式；
- PAT 使用 `.` 表示外部空白、CP Map 使用空格表示外部空白；
- CP Map 行号与固定列宽的排版方式。

仓库测试不得复制原始 Wafer 的 Product/Lot/Wafer、完整 Map 或具体统计结果。

正确做法：

```text
已知样例格式
→ 自定义 synthetic wafer facts
→ Simulator
→ synthetic PAT / CP
→ Parser / Assembler
→ 与预设 facts 比较
```

Synthetic fixture 应明确标识 `DEMO` / `SYNTHETIC`，并使用固定 seed。Phase 2 起再增加 Edge / Center / Ring / Cluster / Scratch 等带预期空间结论的场景。
