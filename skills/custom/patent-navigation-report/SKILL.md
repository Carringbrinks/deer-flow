---
name: patent-navigation-report
description: 撰写专业级专利导航报告（Patent Navigation Report），面向特定行业与区域。本技能深度融合《专利导航指南》（GB/T 39551—2020）系列国家标准，采用**模块化架构**——从 `domain_knowledge/` 加载领域专属子模块，实现行业定制化分析。当用户请求撰写、生成、起草专利导航报告、专利景观分析、专利战略报告或政府/企业专利情报报告时触发。也适用于专利分析、技术专利布局、行业专利竞争情报、专利战略决策等场景。触发词：“专利导航”、“专利分析”、“patent navigation”、“专利景观”、“patent landscape”，或任何要求分析专利数据以支持战略决策的请求。
---

# 专利导航报告 — 模块化框架

本技能提供严格遵循《专利导航指南》（GB/T 39551）系列国家标准的专业级专利导航报告**模块化生成框架**。核心框架编码了从项目启动、实施到成果产出的全生命周期规范。领域专属知识将从 `domain_knowledge/` 下的子模块动态加载。

本框架深度融合 **GB/T 39551.1-2020《总则》** 的核心要求：以专利数据为核心，深度融合产业、科技、经济等多维数据资源，全景式分析区域发展定位、产业竞争格局、企业经营决策和技术创新方向，最终服务于创新资源的有效配置和决策精准度的提升。

## 架构

```
patent-navigation-report/
├── SKILL.md                          ← 你在这里（主框架）
├── template/
│   └── report_template.md            ← 通用报告模板
├── methodology/
│   └── general_methodology.md        ← 通用数据采集与分析方法论
├── writing_style/
│   └── guidelines.md                 ← 语体、规范和论证模式
├── plotting/
│   └── chart_specification.md        ← 图表类型、格式和配色方案
├── merge_md/
│   └── merge_protocol.md             ← 合并协议与最终交付文件生成规范
├── domain_knowledge/
│   ├── carbon-fiber/                 ← 碳纤维领域子模块
│   │   ├── domain_knowledge.md       ← 行业术语、IPC、企业、区域
│   │   ├── methodology.md            ← 领域专属分析框架
│   │   └── report_outline.md         ← 领域专属章节大纲
│   └── industrial-textiles/          ← 产业用纺织品领域子模块
│       ├── domain_knowledge.md
│       ├── methodology.md
│       └── report_outline.md
```

## 渐进式加载协议

1.  **阅读本 SKILL.md** — 掌握融合了国标的核心工作流、专利导航模型与通用规范。
2.  **加载领域模块** — 阅读 `domain_knowledge/{domain}/domain_knowledge.md` 获取行业背景、关键技术与核心竞合主体。
3.  **加载领域方法论** — 阅读 `domain_knowledge/{domain}/methodology.md` 获取领域专属的产业链分解与分析框架。
4.  **加载领域大纲** — 阅读 `domain_knowledge/{domain}/report_outline.md` 获取定制化的章节与重点内容布局。
5.  **按需加载**：
    *   `template/report_template.md` — 通用模板，在没有特定领域大纲或者领域大纲文件为空时作为后备框架。
    *   `methodology/general_methodology.md` — 通用方法论，用于补充领域专属方法论中未尽的通用分析范式。
    *   `writing_style/guidelines.md` — 遵循决策支持导向的写作规范与表达要求。
    *   `plotting/chart_specification.md` — 标准化图表绘制与配色方案。
    *   `merge_md/merge_protocol.md` — 报告最终整合的合并协议（执行第3步时必须加载）。

## 可用领域模块

当前可用领域：

| 领域 | 路径 | 覆盖范围 |
|------|------|----------|
| 碳纤维 | `domain_knowledge/carbon-fiber/` | PAN基碳纤维、复合材料、纺织融合 |
| 产业用纺织品（高端面料） | `domain_knowledge/industrial-textiles/` | 战略新材料、医疗卫生、生态环保三大子领域 |

添加新领域：在 `domain_knowledge/` 下创建子文件夹，包含三个必需文件（`domain_knowledge.md`、`methodology.md`、`report_outline.md`）。

## 核心原则

专利导航报告本质上是**以专利数据为核心的决策支持文件**，绝非单纯的专利信息罗列或学术论文。其核心价值在于全景式分析区域发展定位、产业竞争格局或企业经营决策方向，以服务创新资源有效配置和提高决策精准度。每个分析发现都必须满足：

*   **数据锚定**：与具体的定量证据（专利族数量、增长率、集中度等）紧密挂钩。
*   **因果解释**：不仅展示数据趋势，更要深入解释其背后的技术、市场或政策动因。
*   **战略可执行**：分析结论必须与具体、可落地的“导航”建议相连接（如产业布局结构优化路径、企业整合引进培育路径等）。
*   **多层级透视**：严格遵循**全球 → 国家 → 区域 → 地方**的四级递进分析逻辑。
*   **多维数据融合**：以专利数据为核心，深度融合产业、科技、经济、法律、政策等信息资源。
*   **过程规范**：严格遵循“信息采集 → 数据处理 → 专利导航分析”的实施流程。
*   **逻辑严密**：遵循各类型专利导航的分析模型。例如，产业规划类遵循“方向—定位—路径”模型；区域规划类遵循“竞争力—匹配度”模型。
*   **成果可用**：提供结论清晰、建议可操作的分析报告与数据集。

报告遵循**四段式架构**：

1. **背景与战略定位** — 产业概述、战略重要性
2. **政策比较分析** — 跨国/跨区域政策比较
3. **专利数据分析** — 多维度定量专利分析
4. **战略建议** — 问题-解决结构的政策指导

---

## 工作流

### 第0步：确认需求

在开始撰写前，向用户确认以下信息：

1.  **目标领域**：导航涉及的技术或行业边界。
2.  **导航类型**（与国标5类对应）：
    *   **区域规划类专利导航**：支撑区域规划决策。
    *   **产业规划类专利导航**：支撑产业创新发展规划决策。
    *   **企业经营类专利导航**：支撑企业投资并购、上市、技术创新、产品开发等经营活动决策。
    *   **研发活动类专利导航**：支撑研发立项评价、辅助研发过程决策。
    *   **人才管理类专利导航**：支撑人才遴选、人才评价等人才管理决策。
3.  **地理范围**：需要覆盖的行政或经济区域层级。
4.  **细分领域**：需要深入剖析的具体技术分支。
5.  **对标对象**：需重点分析的创新主体或人才团队。
6.  **报告用途**：指导政策制定、嵌入企业管理、支撑研发或人才方案等。
7.  **时间范围**：数据检索的历史时段。
8.  **报告篇幅**：综合型（~25万字）还是聚焦型（~15-20万字）。

**领域模块选择：**
根据第0步确认的目标领域，加载对应的领域知识文件，为精准的信息采集和分析提供支撑。

### 第1步：加载领域模块

根据目标领域，加载对应的领域知识模块：
```
domain_knowledge/{domain_name}/domain_knowledge.md
domain_knowledge/{domain_name}/methodology.md
domain_knowledge/{domain_name}/report_outline.md
```

### 第2步：增量生成正文（先正文，后摘要）

**核心原则：逐章生成正文 → 生成本章图表 → 提取本章参考文献 → 生成本章摘要。严禁跨越步骤。**

---

### 2.1 创建输出目录结构

首先在 `/mnt/user-data/` 下创建以下目录结构：

```
outputs/
├── parts/                      ← 存放所有中间过程文件（逐章生成产物）
├── assets/                     ← 图表与数据资源
│   ├── charts/                 ← 图表图片文件（PNG / SVG）
│   └── data/                   ← 绘图原始数据（CSV / JSON）
├── merged/                     ← 中间合并结果（强制生成）
└── final/                      ← 最终交付文件夹（仅存最终成果）
```

### 2.2 章节生成标准化循环（A-B-C-D 流程）

对于第1章至最后一章，每一章的生成必须严格遵循以下四个连续步骤：

#### **步骤 A：生成本章正文内容**
*   **指令下达**：仅向大模型发送本章的生成指令。
*   **图表占位**：在正文中需要插入图表的位置，直接生成标准化的 Markdown 图片语法。路径必须指向(绝对路径) `/mnt/user-data/outputs/assets/charts/`，命名必须规范。
    *   *示例：`![图3-1 全球碳纤维专利申请量趋势](/mnt/user-data/outputs/assets/charts/fig_3_1_patent_trend.png)`*
*   **文献内联**：引用文献时直接在正文中打上标记 `[citation:文献名称](URL)`。
*   **保存文件**：将生成的正文单独保存，例如 `/mnt/user-data/outputs/parts/part_01_chapter01.md`。

#### **步骤 B：生成本章配套图表（正文完成后立即执行）**
*   **占位符提取**：扫描刚刚生成的正文 Markdown 文件，提取所有 `![图X-X...](...)` 占位符。
*   **数据准备**：准备这些图表所需的绘图原始数据，保存为 `/mnt/user-data/outputs/assets/data/data_X_X_name.csv`。
*   **图表生成**：调用图表生成工具，生成对应的图片文件，并严格按照正文中占位符的路径和文件名保存至 `/mnt/user-data/outputs/assets/charts/fig_X_X_name.png`。

#### **步骤 C：提取并保存本章参考文献**
*   **标记扫描**：扫描刚刚生成的正文 Markdown 文件，提取所有 `[citation:文献名称](URL)` 标记， 没有引用链接的可以不放置URL。
*   **格式整理**：将这些引用整理成带编号的 Markdown 列表格式（例如：`1. [文献名称](URL)`）。
*   **独立保存**：将该列表保存为独立的参考文献文件，命名与章节对应，例如 `/mnt/user-data/outputs/parts/part_01_chapter01_refs.md`。

#### **步骤 D：生成并保存本章摘要**

*   **前置条件**：必须在完成步骤 A、B、C 后执行，严禁提前。
*   **内容来源**：仅基于当前章节正文（`part_XX_chapterXX.md`）。
*   **摘要要求**：
    * 长度：300–500 字（可按需调整）
    * 内容：涵盖核心观点、关键数据、方法或结论
    * 风格：客观、信息密度高、避免冗余
    * 禁止：不得包含图片语法或 `[citation:...]` 标记
    * 严禁凭空编造摘要数据，必须与正文内容完全锚定。
*   **保存路径**：将生成的摘要保存为 `/mnt/user-data/outputs/parts/part_XX_chapterXX_abstract.md`。

#### 2.3 逐章生成正文（第1章至最后章）

**每次只生成一章**，不得跨章混合生成。

章节顺序与内容结构由领域模块中的 `report_outline.md` 或 `template/report_template.md` 定义。生成时须严格遵循模板规定的章节编号、标题和层级，不得自行增减或调整顺序。

通用生成要求：
- 每章正文不少于10,000字，核心分析章建议15,000-20,000字
- 各章独立保存为 `/mnt/user-data/outputs/parts/part_XX_chapterXX.md`


### 第3步：整合输出

在`/mnt/user-data`工作目录下操作：

合并阶段必须读取并严格执行 `merge_md/merge_protocol.md`。

**核心原则：先分类合并（摘要 / 正文 / 参考文献）→ 生成中间汇总文件 → 再统一合并为最终报告。严禁跨步、跳过中间文件或直接拼接最终报告。**

合并协议负责规定：
- 输入文件结构与命名规范
- `outputs/merged/` 三个中间文件的生成规则
- `outputs/final/` 最终交付文件的生成规则
- 参考文献去重、重编号与最终报告拼接顺序
- Word 文档转换参考命令

执行合并前必须确认 `outputs/parts/`、`outputs/assets/`、`outputs/merged/`、`outputs/final/` 已按协议创建；执行合并后必须进入“评估”阶段检查输出格式是否合规。


## 特殊注意事项

### 专利专属约定
- 使用**专利族**（非单个专利）作为计数单位
- 始终明确统计的是申请还是授权
- 显著标注数据截止时间
- 区分申请日与公开日分析

### 地理递进分析
四级地理分析不可省略——这是专利导航报告的标志性特征：
1. **全球**：建立全球竞争格局
2. **国家**：聚焦目标国家（通常为中国）
3. **省份**：缩小至省份或重点区域
4. **城市/地方**：聚焦报告服务的目标城市

### 政策分析深度
政策章节不是政策文件的简单罗列。每个政策分析必须：
- 映射政策强度随时间的演变
- 通过产出指标评估政策效果
- 跨国比较政策路径差异
- 提炼对目标区域可迁移的经验

### 篇幅控制
- 综合型报告目标：250,000中文字符
- 单章最低不少于10000字
- 核心分析章（专利全景、细分领域）建议15,000-20,000字
- 图表不计入字数

## 评估

只有当目录结构、文件命名、合并产物与最终交付文件全部符合以下范式时，才视为通过。

### 输出范式（强制）

```
outputs/
├── parts/                      ← 存放所有中间过程文件（逐章生成产物）
│   ├── part_01_chapter01.md
│   ├── part_01_chapter01_refs.md
│   ├── part_01_chapter01_abstract.md
│   ├── part_02_chapter02.md
│   ├── part_02_chapter02_refs.md
│   ├── part_02_chapter02_abstract.md
│   ├── ...
│   └── part_NN_chapterNN_abstract.md
│
├── assets/                     ← 图表与数据资源
│   ├── charts/                 ← 图表图片文件（PNG / SVG）
│   │   ├── fig_1_1_xxx.png
│   │   ├── fig_1_2_xxx.png
│   │   ├── fig_2_1_xxx.png
│   │   └── ...
│   │
│   └── data/                   ← 绘图原始数据（CSV / JSON）
│       ├── data_1_1_xxx.csv
│       ├── data_1_2_xxx.csv
│       ├── data_2_1_xxx.csv
│       └── ...
│
├── merged/                     ← 中间合并结果（强制生成）
│   ├── abstracts.md            ← 各章摘要整合后的全文摘要（初版）
│   ├── body.md                 ← 所有章节正文合并结果
│   └── references.md           ← 去重+重编号后的参考文献全集
│
└── final/                      ← 最终交付文件夹（仅存最终成果）
    ├── report.md               ← 最终整合报告（摘要 + 正文 + 参考文献）
    ├── report.docx             ← Word版本（由 report.md 转换）
    ├── abstract.md             ← 最终润色后的全文摘要（可基于 merged/abstracts.md 再优化）
    └── refs.md                 ← 最终参考文献（来自 merged/references.md）
```

### 格式检查清单

- `outputs/parts/` 中每个章节必须同时存在正文、参考文献、摘要三个文件：`part_XX_chapterXX.md`、`part_XX_chapterXX_refs.md`、`part_XX_chapterXX_abstract.md`。
- 章节编号必须连续且按两位数字命名，例如 `part_01`、`chapter01`。
- `outputs/assets/charts/` 仅存放图表图片文件，文件名应符合 `fig_X_X_name.png` 或 `fig_X_X_name.svg`。
- `outputs/assets/data/` 仅存放图表原始数据，文件名应符合 `data_X_X_name.csv` 或 `data_X_X_name.json`。
- `outputs/merged/` 必须包含且只包含合并中间产物：`abstracts.md`、`body.md`、`references.md`。
- `outputs/final/` 必须包含最终交付文件：`report.md`、`report.docx`。
- `outputs/final/report.md` 必须按“摘要 → 正文 → 参考文献”的顺序组织，且不得包含临时说明、检查记录或过程性文本。
- 所有路径必须统一使用 `outputs/`；正文中的图表链接必须指向 `/mnt/user-data/outputs/assets/charts/`。

### 评估结果输出

评估完成后，不通过的根据修改建议进行修改：

```markdown
## 格式规范检查

- 检查结果：通过 / 未通过
- 不合规项：
  1. <如无则写“无”>
- 修正建议：
  1. <如无则写“无”>
```
