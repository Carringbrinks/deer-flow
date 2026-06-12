
# 专利导航报告合并协议

本协议定义专利导航报告的强制合并流程。执行第3步“整合输出”时，必须先读取本文件，并按本文件完成所有中间产物与最终交付文件。

## 核心原则

先分类合并（摘要 / 正文 / 参考文献）→ 生成中间汇总文件 → 再统一合并为最终报告。严禁跨步、跳过 `/mnt/user-data/outputs/merged/` 或直接拼接最终报告。

## 输入与输出结构

合并阶段必须使用以下输出范式：

```
/mnt/user-data/outputs/
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
    ├── abstract.md             ← 最终润色后的全文摘要（可基于 merged/abstracts.md 再优化）
    └── refs.md                 ← 最终参考文献（来自 merged/references.md）
```

## 标准化合并流程

### 步骤 A：合并章节摘要 → abstracts.md

输入来源：
- `/mnt/user-data/outputs/parts/*_abstract.md`

处理规则：
1. 按章节编号顺序读取（chapter01 → chapterNN）。
2. ⚠️ **去除章节标题**：扫描每章摘要，删除所有形式的章节标题、编号和标签，包括但不限于：`### 本章摘要`、`# 第一章`、`第X章`、`一、`、`1.1` 等。
3. 提取关键信息并压缩整合，禁止简单拼接。
4. 统一语言风格，形成连贯的全文摘要。
5. 合并后的摘要不得保留小标题或章节划分，必须是一个整体段落或几个连续段落，禁止分章展示。
6. 不得包含图片语法或 `[citation:...]` 标记。

输出格式：

```markdown
# 摘要

<整合后的全文摘要（3000-5000字）>
```

保存路径：
- `/mnt/user-data/outputs/merged/abstracts.md`

### 步骤 B：合并所有章节正文 → body.md

输入来源：
- `/mnt/user-data/outputs/parts/part_XX_chapterXX.md`

处理规则：
1. 按章节编号顺序读取。
2. 原样拼接正文内容。
3. 保留原始 Markdown 标题结构。
4. 不插入摘要或参考文献。
5. 保留正文中的图表 Markdown 语法和引用标记。
6. ⚠️ **标题层级校验与自动修复**：合并前逐章扫描，确保每章正文以 `# `（一级标题）开头。若章节正文存在以下问题，必须执行自动修复：
   - **章节标题从二级开始**：若正文第一个标题为 `## 第X章` 或类似二级标题，将其提升为 `# `（一级标题），同时将本章内所有 `### ` 降级为 `## `、`#### ` 降级为 `### `，依此类推（全体降一级）。
   - **章节标题缺失**：若正文开头无 `# ` 标题，根据章节编号自动补充 `# 第X章 <章节名称>`（章节名称从 `template/report_template.md` 中对应章节获取）。
   - **标题跳级**：若出现从 `# ` 直接跳到 `### `（跳过 `## `）的情况，在中间插入 `## ` 或将 `### ` 降为 `## `。

保存路径：
- `/mnt/user-data/outputs/merged/body.md`

### 步骤 C：合并参考文献 → references.md

输入来源：
- `/mnt/user-data/outputs/parts/*_refs.md`

处理规则：
1. 读取所有 `.md` 文件中的内容，仅提取 `1. [...]` 格式的编号列表条目；忽略所有非列表内容（标题行、分隔线、空行、说明文字等）。
2. ⚠️ **强制去除标题与分组**：删除所有章节标题（如 `## 第一章 参考文献`）、分组标签（如 `### 中文文献`、`### 英文文献`）和任何非列表文本。只保留纯净的编号列表条目。
3. 执行去重：优先按 URL 去重；无 URL 时按名称去重。
4. 保留首次出现项。
5. 全局重新编号（1 → N）。
6. 输出格式：纯净的 `1. [名称](URL)` 或 `1. 文献名称` 列表，不含任何标题、分组或说明。

输出格式：

```markdown
# 参考文献

1. [文献A](URL)
2. [文献B](URL)
```

保存路径：
- `/mnt/user-data/outputs/merged/references.md`

### 步骤 D：生成最终交付文件

必须按以下顺序生成最终交付文件：

1. 将 `/mnt/user-data/outputs/merged/abstracts.md` 复制或同步为 `/mnt/user-data/outputs/final/abstract.md`，可在不改变事实依据的前提下进行最终润色。
2. 将 `/mnt/user-data/outputs/merged/references.md` 复制或同步为 `/mnt/user-data/outputs/final/refs.md`。
3. 按以下顺序拼接生成 `/mnt/user-data/outputs/final/report.md`：
   - `/mnt/user-data/outputs/final/abstract.md`
   - `/mnt/user-data/outputs/merged/body.md`
   - `/mnt/user-data/outputs/final/refs.md`

`/mnt/user-data/outputs/final/report.md` 必须仅由摘要、正文、参考文献三部分组成，不得混入章节草稿、临时说明、评估记录或其他过程性文本。

根据您的逻辑，以下是完善后的 Word 转换说明：

## 强约束规则

- 必须先生成 `/mnt/user-data/outputs/merged/abstracts.md`、`/mnt/user-data/outputs/merged/body.md`、`/mnt/user-data/outputs/merged/references.md`。
- 摘要必须整合生成，禁止简单拼接。
- 正文必须按章节顺序完整拼接。
- 参考文献必须去重并统一编号。
- `/mnt/user-data/outputs/final/report.md` 必须由 `/mnt/user-data/outputs/final/abstract.md`、`/mnt/user-data/outputs/merged/body.md`、`/mnt/user-data/outputs/final/refs.md` 拼接得到。
