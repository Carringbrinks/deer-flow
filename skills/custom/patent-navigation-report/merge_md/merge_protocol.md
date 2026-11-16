# 专利导航报告合并协议

本协议定义专利导航报告的强制合并流程。执行第3步“整合输出”时，必须先读取本文件，并按本文件完成所有中间产物与最终文件。

## 路径约定

- **构建目录**：`/mnt/user-data/workspace/patent_navigation/`（所有过程文件）
- **交付目录**：`/mnt/user-data/outputs/`（仅最终文件，供 `present_files` 呈现）

严禁把 `parts/`、`merged/`、`assets/` 等过程内容写入交付目录。

## 核心原则

先分类合并（摘要 / 正文 / 参考文献）→ 生成中间汇总文件 → 再统一合并为最终报告。严禁跨步、跳过 `/mnt/user-data/workspace/patent_navigation/merged/` 或直接拼接最终报告。

## 输入与输出结构

```
/mnt/user-data/workspace/patent_navigation/      ← 构建目录（过程文件）
├── parts/                      ← 逐章生成产物
│   ├── part_01_chapter01.md
│   ├── part_01_chapter01_refs.md
│   ├── part_01_chapter01_abstract.md
│   ├── part_02_chapter02.md
│   ├── part_02_chapter02_refs.md
│   ├── part_02_chapter02_abstract.md
│   ├── ...
│   └── part_NN_chapterNN_abstract.md
│
├── assets/
│   ├── charts/                 ← 图表图片文件（PNG / SVG）
│   │   ├── fig_1_1_xxx.png
│   │   ├── fig_1_2_xxx.png
│   │   └── ...
│   └── data/                   ← 绘图原始数据（CSV / JSON）
│       ├── data_1_1_xxx.csv
│       ├── data_1_2_xxx.csv
│       └── ...
│
├── merged/                     ← 中间合并结果（强制生成）
│   ├── abstracts.md            ← 各章摘要整合后的全文摘要（初版）
│   ├── body.md                 ← 所有章节正文合并结果
│   └── references.md           ← 去重+重编号后的参考文献全集
│
└── final/                      ← 最终文件暂存区
    ├── report.md               ← 最终整合报告（摘要 + 正文 + 参考文献）
    ├── abstract.md             ← 最终润色后的全文摘要
    ├── refs.md                 ← 最终参考文献
    ├── search_strategy.md      ← 唯一检索记录文件（一个 Markdown 表格）
    └── report.docx             ← 可选（pandoc 可用时）

/mnt/user-data/outputs/         ← 交付目录（最后复制）
├── report.md
├── abstract.md
├── refs.md
├── search_strategy.md
└── report.docx                 ← 可选
```

## 标准化合并流程

### 步骤 A：合并章节摘要 → abstracts.md

输入来源：
- `/mnt/user-data/workspace/patent_navigation/parts/*_abstract.md`

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
- `/mnt/user-data/workspace/patent_navigation/merged/abstracts.md`

### 步骤 B：合并所有章节正文 → body.md

输入来源：
- `/mnt/user-data/workspace/patent_navigation/parts/part_XX_chapterXX.md`

处理规则：
1. 按章节编号顺序读取。
2. 原样拼接正文内容。
3. 保留原始 Markdown 标题结构。
4. 不插入摘要或参考文献。
5. 保留正文中的图表 Markdown 语法和引用标记。
6. ⚠️ **标题层级校验与自动修复**：合并前逐章扫描，确保每章正文以 `# `（一级标题）开头。若章节正文存在以下问题，必须执行自动修复：
   - **章节标题从二级开始**：若正文第一个标题为 `## 第X章` 或类似二级标题，将其提升为 `# `（一级标题），同时将本章内所有 `### ` 降级为 `## `、`#### ` 降级为 `### `，依此类推（全体降一级）。
   - **章节标题缺失**：若正文开头无 `# ` 标题，根据章节编号自动补充 `# 第X章 <章节名称>`（章节名称从 `template/report_template.md` 或领域 `report_outline.md` 中对应章节获取）。
   - **标题跳级**：若出现从 `# ` 直接跳到 `### `（跳过 `## `）的情况，在中间插入 `## ` 或将 `### ` 降为 `## `。
7. ⚠️ **图表路径校验**：确认所有图片链接均以 `/mnt/user-data/workspace/patent_navigation/assets/charts/` 开头，且目标文件存在；发现 `/mnt/user-data/outputs/`、相对路径或裸文件名时立即修正。

保存路径：
- `/mnt/user-data/workspace/patent_navigation/merged/body.md`

### 步骤 C：合并参考文献 → references.md

输入来源：
- `/mnt/user-data/workspace/patent_navigation/parts/*_refs.md`

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
- `/mnt/user-data/workspace/patent_navigation/merged/references.md`

### 步骤 D：生成最终文件

必须按以下顺序生成：

1. 将 `/mnt/user-data/workspace/patent_navigation/merged/abstracts.md` 复制或同步为 `/mnt/user-data/workspace/patent_navigation/final/abstract.md`，可在不改变事实依据的前提下进行最终润色。
2. 将 `/mnt/user-data/workspace/patent_navigation/merged/references.md` 复制或同步为 `/mnt/user-data/workspace/patent_navigation/final/refs.md`。
3. 保留并最后核对 `/mnt/user-data/workspace/patent_navigation/final/search_strategy.md`；该文件由检索阶段生成，核心内容应为一个 Markdown 表格，逐行包含数据库/检索源、检索用途和检索式或筛选条件。
4. 按以下顺序拼接生成 `/mnt/user-data/workspace/patent_navigation/final/report.md`：
   - `/mnt/user-data/workspace/patent_navigation/final/abstract.md`
   - `/mnt/user-data/workspace/patent_navigation/merged/body.md`
   - `/mnt/user-data/workspace/patent_navigation/final/refs.md`

可使用以下命令（在沙箱内执行）：

```bash
cd /mnt/user-data/workspace/patent_navigation/final
{ cat abstract.md; printf '\n\n'; cat ../merged/body.md; printf '\n\n'; cat refs.md; } > report.md
```

`report.md` 必须仅由摘要、正文、参考文献三部分组成，不得混入章节草稿、临时说明、评估记录或其他过程性文本。`search_strategy.md` 作为独立检索记录交付，不并入 `report.md`。

### 步骤 E：生成 Word（可选）并复制到交付目录

Word 转换依赖 pandoc。先检查是否可用，不可用时只交付 Markdown，并在最终回复中说明：

```bash
cd /mnt/user-data/workspace/patent_navigation/final

test -s search_strategy.md || {
  echo "search_strategy.md 缺失或为空，禁止交付"
  exit 1
}

if command -v pandoc >/dev/null 2>&1; then
  pandoc report.md -o report.docx --resource-path=. --toc
else
  echo "pandoc 不可用，跳过 Word 生成；仅交付 Markdown"
fi

mkdir -p /mnt/user-data/outputs
cp report.md abstract.md refs.md search_strategy.md /mnt/user-data/outputs/
if [ -f report.docx ]; then
  cp report.docx /mnt/user-data/outputs/
fi
```

复制完成后必须调用 `present_files` 呈现 `/mnt/user-data/outputs/report.md`、`abstract.md`、`refs.md`、`search_strategy.md`（以及可选的 `report.docx`）。

> 若 pandoc 无法解析报告中的 `/mnt/user-data/...` 图片绝对路径，可将 `report.md` 临时复制到 `assets/charts/` 的上级目录并使用相对图片路径转换，转换完成后不要修改交付版 `report.md` 的链接。

## 强约束规则

- 必须先生成 `/mnt/user-data/workspace/patent_navigation/merged/abstracts.md`、`merged/body.md`、`merged/references.md`。
- 摘要必须整合生成，禁止简单拼接。
- 正文必须按章节顺序完整拼接。
- 参考文献必须去重并统一编号。
- `/mnt/user-data/workspace/patent_navigation/final/report.md` 必须由 `final/abstract.md`、`merged/body.md`、`final/refs.md` 拼接得到。
- 五类默认必备图必须通过文件存在性、中文字体可读性和数据来源检查；只有某类图确实没有数据支撑时方可缺少，并在检索表的“结果/备注”列说明。
- `final/search_strategy.md` 必须包含数据库来源与检索式表格；缺失、为空或仍有未替换的模板内容时禁止交付。
- 交付目录 `/mnt/user-data/outputs/` 只能包含 `report.md`、`abstract.md`、`refs.md`、`search_strategy.md` 和可选的 `report.docx`，不得出现过程文件。
- 合并完成后必须进入“评估”阶段逐项检查，并调用 `present_files` 完成交付。
