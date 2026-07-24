---
name: patent-evaluation
description: >
  企业专利成果综合评价技能——对指定企业专利数据表进行深度调查、多维度评分和行业排名。

  【必触发规则】用户只要表达了以下意图之一，必须立即激活此技能：
  - "专利成果数据" + 任何评价/分析/调查/排名/评估类词汇
  - "企业专利" + "调查/分析/评价/评估/排名/对比/实力/能力/成果"
  - "科创属性" / "专利实力" / "专利质量" / "专利布局" / "技术实力" + 企业
  - "行业排名" / "行业位阶" / "行业地位" / "行业对比" + 专利
  - 任何要求对企业做专利方面的综合分析、深度调查、成果评价的请求

  【必须反问】如果用户没有明确指定要分析的数据表名，必须反问用户要分析哪张表。
  例如："请问要分析数据库中的哪张企业专利表？例如 patent_data_ccb、t_patent_data_ai 等。"

  【三阶段流程】行业基准模型 → 企业科创属性评分 → 行业位阶排名。
  命令: cd skills/custom/patent-evaluation/scripts && python run_all.py --datasets 表名:标签
---

# 企业专利成果深度调查与综合评价

## 概述

本技能对专利数据进行系统性的**企业科创属性评价**和**行业位阶分析**，结合二者形成对企业专利实力的综合评价。分为三个阶段：

| 阶段 | 脚本 | 说明 |
|------|------|------|
| 第一阶段 | step1_industry_benchmark.py | 构建全球和中国行业基准（基于 `t_patent_data`） |
| 第二阶段 | step2_enterprise_eval.py | 企业多维度科创属性评分（参数化，支持任意表） |
| 第三阶段 | step3_industry_rank.py | 计算企业行业位阶排名（参数化，支持任意表） |

三个阶段必须按顺序执行：先建基准 → 再评价企业科创属性 → 最后算行业位阶，综合二者得出企业在行业中的定位。

## 快速开始

通过 `--datasets` 参数指定要分析的企业专利数据表：

```bash
cd /mnt/skills/custom/patent-evaluation/scripts

# 单表
python3 run_all.py --datasets patent_data_ccb:ccb

# 多表（逗号分隔）
python3 run_all.py --datasets patent_data_ccb:ccb,t_patent_data_ai:ai

# 自定义表（自动推导后缀）
python3 run_all.py --datasets my_patent_data

# 混合：指定表名 + 自定义标签
python3 run_all.py --datasets patent_data_ccb:ccb,my_table:custom
```

`--datasets` 格式：`表名[:标签],表名[:标签],...`
- **表名**：源表名，可不带 `XiaoSu.` 前缀（自动补全）
- **标签**：可选，用于命名输出表。省略时从表名自动推导（去掉 `patent_data_/t_patent_data_` 前缀）
- 例：`patent_data_ccb` → `_ccb`、`t_patent_data_ai` → `_ai`

### 沙箱环境说明

本技能运行在 AIO Sandbox 容器中：

环境变量已预配置：
- `CLICKHOUSE_HOST=dev.heidutech.cn`
- `CLICKHOUSE_PORT=31123`
- `CLICKHOUSE_DATABASE=XiaoSu`
- `CLICKHOUSE_USER=su`
- `CLICKHOUSE_PASSWORD=s2026u`

**依赖要求**：沙箱中必须安装 `clickhouse-connect`、`loguru`：
```bash
pip install clickhouse-connect loguru
```

如遇 `import clickhouse_connect`、`import loguru` 失败，先验证：
```bash
python3 -c "import clickhouse_connect; import loguru; print('OK: clickhouse-connect and loguru available')"
```

## 数据库说明

所有脚本通过 `clickhouse-connect` 直接连接 ClickHouse，无需 MCP 工具。连接参数从环境变量读取，默认值与 `extensions_config.json` 中 `mcp-clickhouse-hzq` 的配置一致。

核心调用模式（`common.py` 封装）：
```python
import clickhouse_connect
client = clickhouse_connect.get_client(
    host="dev.heidutech.cn", port=31123,
    username="su", password="s2026u",
    database="XiaoSu",
)
result = client.query("SELECT ...")
```

### 固定表

| 表名 | 用途 |
|------|------|
| `XiaoSu.t_patent_data` | 全球专利数据（行业基准用，始终不变） |
| `XiaoSu.industry_quantile` | 输出：行业基准分位数（step1 产出） |

### 参数化表（按 `{suffix}` 命名）

用户通过 `--datasets` 指定源表，脚本自动按以下命名规则生成临时表和结果表：

| 表名模式 | 用途 |
|----------|------|
| `XiaoSu.{source_table}` | 输入：企业专利数据源表（用户指定） |
| `XiaoSu.tmp_enterprise_patent{suffix}` | 临时：拆解企业名称 |
| `XiaoSu.tmp_ipc_classes{suffix}` | 临时：拆解 IPC 大类 |
| `XiaoSu.tmp_strategic{suffix}` | 临时：拆解战略性新兴产业 |
| `XiaoSu.tmp_ipc_count{suffix}` | 临时：IPC 计数 |
| `XiaoSu.tmp_strategic_count{suffix}` | 临时：战略性新兴产业计数 |
| `XiaoSu.enterprise_eval_result{suffix}` | 输出：企业科创属性评价结果 |
| `XiaoSu.tmp_ent_subclass_metrics{suffix}` | 临时：企业×小类指标 |
| `XiaoSu.tmp_ent_top3_subclass{suffix}` | 临时：前3小类 |
| `XiaoSu.tmp_ent_subclass_pct{suffix}` | 临时：企业×小类×scope×百分位 |
| `XiaoSu.enterprise_industry_rank{suffix}` | 输出：企业行业位阶排名 |

### 源表字段要求

所有企业专利数据源表必须具有相同的字段结构：
`专利类型`、`申请日`、`被引用数量`、`引用数量`、`申请人数量`、`发明人数量`、
`权利要求数`、`同族专利数`、`许可次数`、`转让次数`、`质押次数`、`诉讼次数`、
`复审次数`、`无效次数`、`专利状态`、`IPC分类号`、`战略性新兴产业`、`企业类型`、
`科技型企业`、`企业规模`、`上市状态`、`数字经济核心产业`、`绿色低碳技术`、
`申请人`、`专利权人`

临时表以 `tmp_` 开头，每次运行会自动清理重建。

## 评价体系详解

### 第一阶段：行业基准（step1_industry_benchmark.py）

对每个 IPC 小类（前4位），分 `global` 和 `china` 两个范围，计算五维99分位数：

| 维度 | 说明 |
|------|------|
| density_dist | 企业在该小类的专利数量分布 |
| cited_dist | 专利被引用次数分布 |
| family_dist | 同族专利数分布 |
| claims_dist | 权利要求数分布 |
| value_dist | 专利价值评分分布 |

参考 SQL: `references/industry_benchmark_optimized.sql`

### 第二阶段：企业科创属性评价（step2_enterprise_eval.py）

对指定的企业专利数据表进行 7 维度加权评分（各维度 0-100 分）：

| 维度 | 权重 | 指标 |
|------|------|------|
| 数量实力 | 15% | 专利密度、类型多样性 |
| 质量水平 | 20% | 被引次数、权利要求数、同族数 |
| 布局广度 | 15% | IPC覆盖、战略性新兴产业、数字经济、绿色低碳 |
| 商业价值 | 15% | 转让、许可、质押次数 |
| 研发能力 | 10% | 发明人规模、申请人规模 |
| 法律状态 | 10% | 有效专利占比、复审无效诉讼风险 |
| 资质属性 | 15% | 科技型/高新技术企业、上市状态、企业规模 |

SQL 模板: `references/enterprise_eval_template.sql`（通过 `{source_table}` 和 `{suffix}` 参数化）

### 第三阶段：行业位阶（step3_industry_rank.py）

**结合企业科创属性评分和行业基准**，计算行业位阶排名：

1. 取每家企业专利数量最多的前3个IPC小类
2. 对照 `industry_quantile` 分位数插值得到百分位
3. 按专利数量加权计算三维综合百分位
4. 结合科创属性评分和行业位阶百分位，按综合百分位分档：

| 百分位 | 档位 |
|--------|------|
| ≥ 90 | 行业领先 |
| ≥ 70 | 行业优秀 |
| ≥ 50 | 行业中上 |
| ≥ 30 | 行业平均 |
| ≥ 10 | 行业落后 |
| < 10 | 行业底部 |

SQL 模板: `references/enterprise_industry_rank_template.sql`（通过 `{suffix}` 参数化）

## 综合评价报告模板（固定格式，不可变更）

**核心约束：以下模板是唯一合法的综合评价输出格式。每次完成数据分析后，必须严格按此模板组织报告，不得增删维度、调换顺序或改变结构。所有维度、子指标、评分等级均来自 SQL 模板代码的实际计算逻辑。**

### 数据来源映射

| 数据 | 来源表 | 说明 |
|------|--------|------|
| 科创属性7维得分 | `XiaoSu.enterprise_eval_result{suffix}` | 第二阶段产出，每家企业一行 |
| 行业位阶排名 | `XiaoSu.enterprise_industry_rank{suffix}` | 第三阶段产出，每家企业 global/china 各一行 |

### 统一评分等级标准（适用全部7个维度）

| 分数区间 | 等级 | 标识 |
|----------|------|------|
| ≥ 80 | 强 | 🟢 |
| 60–79 | 良好 | 🔵 |
| 40–59 | 一般 | 🟡 |
| < 40 | 待提升 | 🔴 |

### 行业位阶等级标准（6档制）

| 综合百分位 | 位阶等级 |
|-----------|----------|
| ≥ 90 | 行业领先 |
| ≥ 70 | 行业优秀 |
| ≥ 50 | 行业中上 |
| ≥ 30 | 行业平均 |
| ≥ 10 | 行业落后 |
| < 10 | 行业底部 |

---

### 报告固定结构（5部分，顺序不可变）

---

### 一、综合评价总览

从 `enterprise_eval_result{suffix}` 和 `enterprise_industry_rank{suffix}` 提取以下固定字段，形成总览表：

| 指标 | 字段来源 | 说明 |
|------|----------|------|
| 综合评分 | `total_score` | 0–100分，7维度加权总分 |
| 专利总量 | `patent_count` | 企业专利总件数 |
| 专利密度 | `density` | 年均专利产出（件/年） |
| 时间跨度 | `span_years` | 专利申请跨越年数 |
| 近三年活跃度 | `recent_ratio` | 近3年专利数 / 专利总量 |
| 全球行业位阶 | `level` WHERE scope='global' | 6档：行业领先/优秀/中上/平均/落后/底部 |
| 中国行业位阶 | `level` WHERE scope='china' | 6档：行业领先/优秀/中上/平均/落后/底部 |
| 全球综合百分位 | `pct_composite` WHERE scope='global' | 三维加权（密度+引用+家族） |
| 中国综合百分位 | `pct_composite` WHERE scope='china' | 三维加权（密度+引用+家族） |

---

### 二、科创属性七维分析（固定7维度，不可增删改）

从 `enterprise_eval_result{suffix}` 逐维度展示得分和等级。**每个维度必须展开子指标**（子指标与 `enterprise_eval_template.sql` Step 5c 中的计算公式一一对应）：

**维度1：数量实力**（权重15%，字段 `qty_score`）

| 子指标 | SQL来源 | 计算方式 |
|--------|---------|----------|
| 专利密度 | `density` | `total / span_years` |
| 专利类型多样性 | `patent_type_cnt` | `countDistinct(专利类型)` |
| 近三年占比 | `recent_ratio` | `recent_cnt / total` |

得分公式：`least(density*20,100)*0.5 + least(patent_type_cnt*20,100)*0.3 + recent_ratio*100*0.2`

**维度2：质量水平**（权重20%，字段 `quality_score`）

| 子指标 | SQL来源 | 计算方式 |
|--------|---------|----------|
| 被引总数 | `total_cited` | `sum(cited)` |
| 平均权利要求数 | `avg_claims` | `avg(claims)` |
| 平均同族专利数 | `avg_family` | `avg(family)` |
| 引用总数 | `total_refs` | `sum(refs)` |

得分公式：`least(total_cited*2,100)*0.3 + least(avg_claims*5,100)*0.25 + least(avg_family*20,100)*0.25 + least(total_refs,100)*0.2`

**维度3：布局广度**（权重15%，字段 `layout_score`）

| 子指标 | SQL来源 | 计算方式 |
|--------|---------|----------|
| IPC小类覆盖数 | `ipc_class_cnt` | `count(DISTINCT substring(IPC,1,4))` |
| 战略性新兴产业数 | `strategic_cnt` | `count(DISTINCT 战略性新兴产业)` |
| 是否涉及数字经济 | `digital_flag` | `countIf(数字经济核心产业 != '')` |
| 是否涉及绿色低碳 | `green_flag` | `countIf(绿色低碳技术 != '')` |

得分公式：`least(ipc_class_cnt*5,100)*0.3 + least(strategic_cnt*20,100)*0.25 + (digital_flag>0?100:0)*0.25 + (green_flag>0?100:0)*0.2`

**维度4：商业价值**（权重15%，字段 `commercial_score`）

| 子指标 | SQL来源 | 计算方式 |
|--------|---------|----------|
| 转让次数 | `total_transfer` | `sum(transfer_cnt)` |
| 许可次数 | `total_license` | `sum(license_cnt)` |
| 质押次数 | `total_pledge` | `sum(pledge_cnt)` |

得分公式：`least(total_transfer*10,100)*0.35 + least(total_license*10,100)*0.30 + least(total_pledge*10,100)*0.35`

**维度5：研发能力**（权重10%，字段 `rd_score`）

| 子指标 | SQL来源 | 计算方式 |
|--------|---------|----------|
| 平均发明人数 | `avg_inventor` | `avg(inventor_cnt)` |
| 平均申请人数 | `avg_applicant` | `avg(applicant_cnt)` |

得分公式：`least(avg_inventor*10,100)*0.5 + least(avg_applicant*20,100)*0.5`

**维度6：法律状态**（权重10%，字段 `legal_score`）

| 子指标 | SQL来源 | 计算方式 |
|--------|---------|----------|
| 有效专利占比 | `active_cnt / total` | `countIf(专利状态 IN ('有效','审查中')) / total` |
| 复审风险 | `total_reexam` | `sum(reexam_cnt)` |
| 无效风险 | `total_invalid` | `sum(invalid_cnt)` |
| 诉讼风险 | `total_lawsuit` | `sum(lawsuit_cnt)` |

得分公式：`least(active_ratio*100,100)*0.4 + max(0,100-reexam*20)*0.2 + max(0,100-invalid*20)*0.2 + max(0,100-lawsuit*20)*0.2`

**维度7：资质属性**（权重15%，字段 `qual_score`）

| 子指标 | SQL来源 | 计算方式 |
|--------|---------|----------|
| 科技型企业 | `tech_ent` | `科技型企业 != '' AND != '0'` → 100，否则0 |
| 上市状态 | `listed` | 上市→100，非上市但有值→50，无→0 |
| 企业规模 | `ent_scale` | 大型→100，中型→70，小型→50，无→0 |
| 高新技术企业 | `ent_type` | 含"高新技术"→100，有值→50，无→0 |

得分公式：`(tech_ent有值?100:0)*0.3 + (上市?100:有值?50:0)*0.25 + (大型?100:中型?70:小型?50:0)*0.25 + (高新?100:有值?50:0)*0.2`

**七维度展示格式要求：** 每个维度用统一表格呈现：

```
| 维度 | 得分 | 等级 | 权重 | 关键子指标（实际值） |
|------|------|------|------|---------------------|
| 数量实力 | xx.x | 🟢/🔵/🟡/🔴 | 15% | 密度x.x件/年, 类型x种, 近三年占比x% |
| 质量水平 | xx.x | 🟢/🔵/🟡/🔴 | 20% | 被引x次, 权利要求均值x, 同族均值x |
| 布局广度 | xx.x | 🟢/🔵/🟡/🔴 | 15% | IPCx类, 战略新兴产业x类, 数字x/绿色x |
| 商业价值 | xx.x | 🟢/🔵/🟡/🔴 | 15% | 转让x次, 许可x次, 质押x次 |
| 研发能力 | xx.x | 🟢/🔵/🟡/🔴 | 10% | 发明人均值x人, 申请人均值x人 |
| 法律状态 | xx.x | 🟢/🔵/🟡/🔴 | 10% | 有效占比x%, 复审x次, 无效x次, 诉讼x次 |
| 资质属性 | xx.x | 🟢/🔵/🟡/🔴 | 15% | 科技型x, 上市x, 规模x, 高新x |
```

---

### 三、行业位阶分析

从 `enterprise_industry_rank{suffix}` 提取全球（scope='global'）和中国（scope='china'）两个范围的数据，**必须分别展示**：

**全球范围：**

| 指标 | SQL字段 | 值 |
|------|---------|-----|
| 主要IPC小类 | `main_subclass` | xxxx（专利数最多的IPC小类） |
| 前3小类 | `top3_subclasses` | [xxxx, xxxx, xxxx] |
| 前3小类专利数 | `top3_counts` | [x, x, x] |
| 密度百分位 | `pct_density` | xx.x% |
| 引用百分位 | `pct_cited` | xx.x% |
| 家族百分位 | `pct_family` | xx.x% |
| 综合百分位 | `pct_composite` | xx.x% |
| 位阶等级 | `level` | 行业领先/优秀/中上/平均/落后/底部 |

**中国范围：**（同上格式，scope='china'）

**全球 vs 中国对比分析：** 用表格对比4个百分位（密度/引用/家族/综合），分析企业在国内 vs 国际的相对位置差异。

---

### 四、综合诊断

基于7维得分和行业位阶，按固定结构给出诊断：

**4.1 核心优势**（取得分最高的2个维度）：

| 排名 | 维度 | 得分 | 等级 | 一句话解读 |
|------|------|------|------|-----------|
| 1 | xxx | xx.x | 🟢 | （该维度为什么强，对企业的意义） |
| 2 | xxx | xx.x | 🟢/🔵 | （同上） |

**4.2 主要短板**（得分 < 40 的维度全部列出；若无则显示得分最低的2个）：

| 维度 | 得分 | 等级 | 一句话解读 |
|------|------|------|-----------|
| xxx | xx.x | 🔴/🟡 | （该维度为什么弱，对企业的影响） |

**4.3 风险提示**（固定检查项，命中则报告）：

| 检查项 | 触发条件 | 状态 |
|--------|----------|------|
| 专利失效/诉讼风险 | 法律状态得分 < 50 | ⚠️有风险 / ✅正常 |
| 创新持续性风险 | 近三年活跃度 < 20% | ⚠️有风险 / ✅正常 |
| 技术领域集中风险 | 布局广度得分 < 40 | ⚠️有风险 / ✅正常 |
| 商业化不足 | 商业价值得分 < 30 | ⚠️有风险 / ✅正常 |

---

### 五、改进建议

按优先级排序，针对短板维度给出可操作建议。每个建议包含：优先级、针对维度、问题描述、具体措施。

| 优先级 | 针对维度 | 问题描述 | 具体措施 |
|--------|----------|----------|----------|
| 🔴 高 | （得分最低的维度） | （一句话描述问题） | （1-2条可操作措施） |
| 🟡 中 | （得分次低的维度） | （一句话描述问题） | （1-2条可操作措施） |
| 🟢 低 | （其余 < 40 的维度） | （一句话描述问题） | （1-2条可操作措施） |

**建议方向速查表（针对各维度的典型改进路径）：**

| 薄弱维度 | 建议方向 |
|----------|----------|
| 数量实力 | 加大研发投入、优化专利激励机制、提高年度专利申请量 |
| 质量水平 | 注重核心专利布局、提高权利要求撰写质量、关注高被引技术领域 |
| 布局广度 | 拓展技术领域覆盖、关注战略性新兴产业/数字经济/绿色低碳方向 |
| 商业价值 | 推动专利运营和成果转化、增加许可转让、探索专利质押融资 |
| 研发能力 | 引进高端技术人才、扩大研发团队规模、加强产学研合作 |
| 法律状态 | 加强专利维护和续费管理、降低诉讼和无效风险、建立风险预警机制 |
| 资质属性 | 申报科技型中小企业/高新技术企业认定、推进上市进程 |

## 用户交互指引

| 用户问法（自然语言） | 执行动作 | 说明 |
|----------------------|----------|------|
| 分析 patent_data_ccb 表的专利数据 | `run_all.py --datasets patent_data_ccb:ccb` | 指定数据源 |
| 帮我看看 t_patent_data_ai 的专利实力 | `run_all.py --datasets t_patent_data_ai:ai` | — |
| 评估多张表的科创属性和行业地位 | `run_all.py --datasets 表1:标1,表2:标2` | 多表分析 |
| 分析一下专利数据 | 反问用户要分析哪张表 | 未指定表名时必须反问 |
| 做一次专利成果调查 | 反问用户要分析哪张表 | 未指定表名时必须反问 |

## 注意事项

1. 所有 SQL 通过 `clickhouse-connect` 直接连接 ClickHouse 执行，无需 MCP 工具
2. 运行前确保 ClickHouse 服务可用（`dev.heidutech.cn:31123`）且网络可达
3. 每次运行自动清理临时表
4. 第一阶段数据量大，耗时较长
5. 参考 SQL 在 `references/` 目录；模板文件 `enterprise_eval_template.sql` 和 `enterprise_industry_rank_template.sql` 是实际使用的版本
6. **新增数据源**：只要新表字段结构与现有表一致，通过 `--datasets 表名:标签` 即可加入分析，无需修改任何脚本或 SQL
7. **如果用户未明确指定表名，必须反问**："请问要分析数据库中的哪张企业专利表？"
8. 如果报告中需要绘图，必须在沙箱中安装中文字体，否则图表中的中文会显示为乱码。安装方法：
```bash
apt-get update && apt-get install -y fonts-noto-cjk fonts-wqy-microhei
```
