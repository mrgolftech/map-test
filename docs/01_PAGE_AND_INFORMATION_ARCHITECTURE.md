# 01 — 页面与信息架构

## 1. 导航结构

桌面端一级导航固定为：

```text
总览 Dashboard
新建分析 Upload
分析历史 History
Lot / 多 Wafer
系统设置 Settings
```

单 Wafer 详情、Lot 详情属于上下文页面，不在侧栏重复堆叠。

移动端保证 Dashboard、历史列表、Wafer 详情、Lot 详情基本查看；复杂筛选和批量操作可降级。

## 2. 全局 AppShell

### 桌面端

```text
┌──────────────────────────────────────────────────────┐
│ Product Brand / Breadcrumb          Theme / Settings │
├───────────────┬──────────────────────────────────────┤
│ Sidebar       │ PageHeader                           │
│               ├──────────────────────────────────────┤
│ Dashboard     │                                      │
│ Upload        │ Page Content                         │
│ History       │                                      │
│ Lot Analysis  │                                      │
│ Settings      │                                      │
└───────────────┴──────────────────────────────────────┘
```

规则：

- Sidebar 可折叠；
- PageHeader 统一提供 title / description / breadcrumbs / actions；
- 页面内容区最大化利用 1366–1920 宽度；
- 不在每个页面重新实现 Header、间距和操作区。

## 3. Dashboard

### 3.1 目标

回答“当前已分析的数据整体表现如何、哪里需要关注”。

### 3.2 第一屏 KPI

- Wafer 数；
- Lot 数；
- Avg Yield；
- 异常 Wafer 数；
- Main Fail Bin；
- 最近分析时间。

### 3.3 图表

- Yield Trend；
- Top Fail Bin Trend；
- Pattern Distribution；
- Yield Distribution；
- 最近异常 Wafer；
- 最近分析记录。

### 3.4 筛选

统一 FilterBar：

- Product；
- Lot；
- Date Range；
- Tester；
- Test Program；
- Probe Card。

Dashboard 只展示摘要，不承载复杂 Wafer 编辑操作。

## 4. 新建分析页

### 4.1 上传区

支持：

- 拖拽；
- 选择文件；
- PAT；
- CP；
- PAT + CP；
- 文件列表；
- 格式识别状态；
- 文件大小；
- 校验结果。

### 4.2 分析流程状态

```text
上传
→ 格式探测
→ Parser
→ 数据校验
→ 确定性分析
→ 保存
→ AI 分析（可选）
```

每一步必须有明确状态：

- pending；
- running；
- success；
- warning；
- error。

解析错误必须显示用户可理解的原因和文件位置，不允许只有 “500”。

### 4.3 成功结果

分析成功后直接进入单 Wafer 详情。

## 5. 单 Wafer 分析页

这是产品核心页面。

### 5.1 顶部 Header

显示：

- Product；
- Lot；
- Wafer；
- Flow；
- Yield；
- Tested / Pass / Fail；
- 数据校验状态；
- AI 状态。

主要操作：

- 重新 AI 分析；
- 导出 PNG；
- 导出 CSV；
- 返回 Lot；
- 删除记录（需确认）。

### 5.2 主工作区

桌面端采用大 Wafer Map + 右侧详情：

```text
┌──────────────────────────────────┬─────────────────────┐
│                                  │ Wafer Metadata      │
│                                  │                     │
│           Wafer Map              │ Bin Ranking         │
│                                  │                     │
│                                  │ Spatial Summary     │
│                                  │                     │
└──────────────────────────────────┴─────────────────────┘
```

Wafer Map 至少占主要可视区域的 60%。

### 5.3 Wafer Toolbar

统一操作：

- All；
- PASS；
- FAIL；
- Selected Bins；
- Reset View；
- Clear Selection；
- Show Coordinates；
- Show / Hide Notch；
- 导出 PNG。

### 5.4 Bin 面板

展示：

- Soft Bin；
- Char；
- Description；
- Count；
- Wafer Percentage；
- Fail Percentage；
- color；
- Filter checkbox。

支持搜索和排序。

### 5.5 分析 Tabs

统一四个 Tab：

1. Overview
2. Spatial
3. Bin
4. AI Analysis

#### Overview

- Wafer 基本信息；
- Yield；
- Bin Pareto；
- 主要结论；
- 数据校验。

#### Spatial

- Center / Mid / Edge；
- 上下 / 左右 / 四象限；
- Edge / Center Enrichment；
- Cluster；
- Pattern；
- 主 Fail Bin mini map。

#### Bin

- 全部 Bin 表；
- 单 Bin 统计；
- 单 Bin map；
- 与 PASS 空间差异。

#### AI Analysis

不做聊天窗口主导布局。使用工程报告布局：

- Executive Summary；
- Key Findings；
- Spatial Patterns；
- Possible Causes；
- Recommended Checks；
- Confidence；
- Limitations；
- 可选“继续追问”。

## 6. 分析历史页

### 6.1 列表字段

- Analysis Time；
- Product；
- Lot；
- Wafer；
- Flow；
- Yield；
- Main Fail Bin；
- Pattern；
- Validation；
- AI Status；
- Actions。

### 6.2 筛选

- Product；
- Lot；
- Wafer；
- Date Range；
- Yield Range；
- Pattern；
- Main Bin。

### 6.3 操作

- 打开；
- 选择多个 Wafer 进行比较；
- 删除；
- 导出摘要。

历史页必须支持 URL 可恢复筛选状态。

## 7. Lot / 多 Wafer 分析页

### 7.1 顶部摘要

- Product；
- Lot；
- Wafer Count；
- Avg Yield；
- Yield Std；
- Best / Worst；
- Main Fail Bin；
- 异常 Wafer Count。

### 7.2 图表

- Yield Trend；
- Fail Bin Trend；
- Edge Enrichment Trend；
- Center Enrichment Trend；
- Pattern Trend / Distribution。

### 7.3 Wafer Matrix

核心比较表：

```text
Wafer | Yield | Main Bin | Bin% | Edge | Center | Cluster | Pattern
```

支持按任意列排序、筛选与点击进入单片。

### 7.4 小型 Wafer Map 网格

支持同屏展示 4–12 片 Wafer 缩略图，用于观察批次空间模式重复性。

### 7.5 综合 AI

LLM 输入多 Wafer AnalysisSummary，不传完整海量 Die 列表。

输出必须关注：

- 持续恶化；
- 单片离群；
- Bin 漂移；
- Pattern 重复；
- 建议优先比较的 Tester / Probe / Program 等条件。

## 8. 设置页

MVP 只做必要设置：

### LLM

- Base URL；
- API Key；
- Model；
- Test Connection；
- multimodal capability flag（如需要）。

API Key 永不回显完整值，永不进入浏览器持久化明文。

### Analysis

- Yield threshold；
- Edge / Center 半径阈值；
- Pattern 参数（仅高级设置）；
- Bin palette。

### System

- Version；
- Backend health；
- DB status；
- Data directory。

## 9. 空状态与异常状态

所有页面必须设计：

- Empty；
- Loading；
- Error；
- Partial Warning；
- No Permission（未来需要时）；
- AI unavailable。

核心分析不得因为 AI 失败而进入整页 Error。
