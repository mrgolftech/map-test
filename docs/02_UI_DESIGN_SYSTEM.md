# 02 — UI Design System

## 1. 设计目标

产品视觉定位：

**专业半导体测试 / 工程分析工作台**

关键词：

- 高信息密度；
- 数据优先；
- 层级清晰；
- 克制；
- 工程感；
- 异常醒目但不过度使用警告色。

不采用炫酷大屏、霓虹工业风、强渐变营销风。

## 2. UI 技术基线

统一使用：

- Ant Design：主 UI 组件库；
- Apache ECharts：统计图；
- ECharts Custom Series / Canvas：Wafer Map；
- Lucide React：补充业务图标；
- TanStack Router；
- TanStack Query。

规则：

- 不自行重复实现 Button / Input / Select / Table / Modal / Drawer / Form；
- 只有 Wafer、Yield、Bin、Pattern 等领域组件允许自定义；
- 不再引入第二套完整 UI 框架；
- 页面私有 CSS 尽量少。

## 3. 设计 Token

所有业务 UI 禁止直接散落硬编码颜色和尺寸。

至少维护：

### Color

```text
appBg
surface
surfaceRaised
surfaceSoft
border
borderStrong
text
textSecondary
textTertiary
primary
success
warning
danger
info
```

### Radius

```text
control: 6–8
card: 10–12
panel: 12–16
```

工程平台避免过度大圆角。

### Spacing

以 4px 为基础节奏：

```text
4 / 8 / 12 / 16 / 20 / 24 / 32
```

推荐：

- Page padding: 20–24；
- Card gap: 12–16；
- Card padding: 16；
- Section gap: 16–24。

### Typography

推荐：

- Page title: 22–24；
- Section title: 16–18；
- Body: 14；
- Table: 13–14；
- Auxiliary: 12；
- KPI: 24–32。

数字优先使用 tabular number。

## 4. Light / Dark

必须同时支持 Light 和 Dark。

Ant Design 主题通过统一 ConfigProvider 管理；自定义 token 与主题同步。

Dark Mode：

- 改变 App / Card / Grid / Text / Tooltip 等；
- Wafer Bin 语义颜色不随主题重新随机映射；
- 图表坐标、grid、legend、tooltip 必须同步；
- Canvas 背景与坐标文本必须同步。

## 5. Wafer Palette

Wafer Bin Palette 与 UI Theme 分离。

原则：

1. PASS 使用稳定绿色；
2. FAIL Bin 颜色稳定；
3. 同一个 Product + Soft Bin 在历史记录中保持相同颜色；
4. Light / Dark 下颜色含义不变；
5. 不允许刷新页面后随机变化；
6. 不允许只依赖颜色表达状态，图例必须包含 Bin / Char / Description。

## 6. 状态语义

### 通用状态

- success：正常完成；
- warning：数据可用但存在校验或质量风险；
- danger：确定错误 / 明显异常；
- info：说明性信息。

红色仅用于真正错误和明确异常。

### AI 语义

UI 对 AI 输出分层：

- FACT：事实；
- JUDGMENT：判断；
- HYPOTHESIS：假设；
- RECOMMENDATION：建议。

不得用同一种视觉样式混淆事实与推测。

## 7. 页面级公共组件

必须提供并优先复用：

```text
AppShell
PageContainer
PageHeader
PageActions
SectionCard
MetricCard
ChartCard
FilterBar
StatusTag
EmptyState
LoadingState
ErrorState
ValidationAlert
```

领域组件：

```text
WaferMap
WaferToolbar
BinLegend
BinTable
DieTooltip
MiniWaferMap
YieldTrendChart
BinTrendChart
PatternTag
AIAnalysisPanel
```

页面如果发现重复视觉模式，应先抽象公共组件再复制。

## 8. 表格规范

分析历史、Bin、Wafer Matrix 统一使用 Ant Design Table。

要求：

- Header sticky；
- 数字右对齐；
- Row hover；
- 主键列固定（需要时）；
- 长文本 Tooltip；
- Yield / Count 使用 tabular number；
- 表格筛选与页面 FilterBar 含义明确；
- 关键筛选应可恢复到 URL search；
- 大数据量不一次渲染无限行。

## 9. 图表规范

ECharts 图表必须：

- 有单位；
- 有明确 Tooltip；
- axis label 可读；
- legend 不遮挡数据；
- 不使用 3D；
- 不滥用面积渐变；
- 趋势图保持统一时间 / Wafer 顺序；
- 多系列颜色稳定；
- 告警阈值可显示 reference line；
- 空数据明确展示 EmptyState。

## 10. Wafer Map 规范

Wafer Map 是领域核心，不得退化为普通 Heatmap。

必须：

- Die 独立矩形；
- 保留晶圆实际 shape；
- 外空白不视为 Die；
- 坐标可显示；
- Notch 可见；
- zoom / pan；
- hover / selected / filtered 状态明确；
- 1 万 Die 交互流畅；
- 大比例缩放后格线可见；
- PASS / FAIL / Bin 过滤不会修改原始数据；
- mini map 与主图共用相同坐标和 palette。

## 11. 响应式

至少验证：

- 390px；
- 768px；
- 1280px；
- 1440px；
- 1920px。

桌面优先。

移动端：

- Sidebar → Drawer；
- 复杂双栏 → 单栏；
- Wafer Map 保留基本 zoom / pan；
- 大型表格允许横向滚动；
- 不强求在手机执行复杂批量比较。

## 12. 交互反馈

所有异步操作必须有状态：

- upload；
- parse；
- analyze；
- save；
- ai；
- export。

禁止点击后无反馈。

危险操作统一使用确认对话框，不使用 `window.confirm()`。

Toast / Message 用于短反馈；结构化错误使用 Alert / Result / ErrorState。

## 13. 可访问性

- focus-visible；
- 键盘可操作；
- 颜色不是唯一信息载体；
- icon-only button 必须有 accessible name；
- Tooltip 不承载唯一关键信息；
- 主要触控区域目标建议 ≥ 40px。


## 14. Wafer 专业工具参考原则

Wafer Map 与工程 UI 可参考 `wafertools/wafermap` / `wafertools/tsmap` 的成熟交互经验，但 map-test 继续以 Ant Design 为主 UI 组件库。

采纳：

- UI chrome 颜色统一走 design token，不在业务组件散落硬编码；
- Canvas 绘制的轴线、网格、Tooltip、Selection 也必须响应 Light / Dark；
- Renderer、Selection、Viewport、Tooltip 分离，避免一个组件同时处理所有状态；
- Keyboard、focus-visible、ARIA、Escape close 等交互遵循成熟组件行为；
- Wafer Map 性能与交互行为需要独立测试；
- 单 Wafer 与 Mini Wafer / Gallery 共用 palette、坐标和 renderer 语义。

不采纳：

- 不重写 Ant Design 已有 Menu / Modal / Drawer / Select / Tooltip；
- 不复制参考项目的手写 DOM UI；
- 不为了保持一致而放弃本项目既定的 React + Ant Design 设计系统。

参考项目只提供工程经验，不构成新的 UI 依赖。


## 15. Phase 2 Wafer Map 实现约束

当前 Wafer Map 使用 Apache ECharts custom series + Canvas renderer。

必须保持：

- renderer 只消费 WaferDataset，不依赖 PAT / CP；
- xAxis=Column，yAxis=Row，y 轴按 Map 行方向 inverse；
- 每颗 tested Die 独立 rectangle；
- PASS 使用固定绿色，Fail Bin 颜色由 Soft Bin 稳定映射；
- selectedBins 非空时非目标 Bin 灰化，而不是改变其 Bin 颜色映射；
- PASS / FAIL 模式可以隐藏非目标结果；
- tooltip / click detail 必须展示 Row、Column、Char、Bin、Description、Result；
- 坐标轴可关闭，但源 Row/Column 不改变；
- zoom / pan 不改变数据语义；
- Notch 以独立 overlay 表达，不通过旋转数据伪造；
- 主 Fail Bin Mini Map 复用同一 WaferMap renderer；
- PNG export 从当前 renderer 导出；
- CSV export 从 WaferDataset 导出，不从 ECharts data 反推。

性能策略：

- Canvas renderer；
- animation=false；
- progressive rendering；
- 轴范围由 metadata.rows / columns 固定，不依赖当前过滤结果；
- 禁止一个 Die 创建一个 React DOM 节点。
