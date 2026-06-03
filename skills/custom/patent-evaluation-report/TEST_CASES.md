# 专利检索评价报告 - 测试用例

## 测试用例 1：氨纶专利评价（基于参考文档）

### 输入信息

- **专利号**: CN202310308960.3
- **申请日**: 2023-03-24
- **公开号**: CN116366980A
- **申请人**: 诸暨华海氨纶有限公司
- **发明名称**: 一种高弹性耐高温氨纶纤维及其制备方法
- **IPC 分类**: D01F1/10；D01F6/94；C08G18/48；C08G18/83
- **专利类型**: 发明

### 技术方案要点

1. 采用聚醚二醇作为软段，配合二异氰酸酯和扩链剂制备聚氨酯预聚体
2. 引入二氧化硅纳米颗粒增强纤维的热稳定性
3. 添加甲基丙烯酰氧基偏苯三酸酐作为交联剂提高弹性回复率
4. 使用水杨酰苯胺作为光稳定剂改善耐黄变性能
5. 采用干法纺丝工艺制备高弹性氨纶纤维

### 对比文件

| 编号 | 公开号 | 公开日期 | 标题 | 类型 |
|------|--------|----------|------|------|
| 对比文件1 | CN104073913A | 2014-10-01 | 一种高弹性氨纶纤维及其制备方法 | X |
| 对比文件2 | CN114164519B | 2022-08-30 | 一种耐高温氨纶纤维及其制备方法 | Y |
| 对比文件3 | CN108330676A | 2018-07-27 | 一种高弹性氨纶及其制备方法 | Y |
| 对比文件4 | CN108143634B | 2019-04-05 | 一种氨纶纤维的制备方法 | A |

### 检索关键词

**中文**: 氨纶；聚氨酯；聚醚二醇；二氧化硅；甲基丙烯酰氧基偏苯三酸酐；水杨酰苯胺；纺丝；高弹性；耐高温

**外文**: spandex; polyurethane; polyetherdiol; silica; methyl methacryloxy trimellitate; salicylanilide; spinning

### 预期输出

1. **新颖性评述**: 逐项对比4份对比文件，指出区别技术特征
2. **创造性评述**: 分析二氧化硅纳米颗粒与交联剂的协同效应
3. **实用性评述**: 确认可在产业上制造和使用
4. **五维度评价**:
   - 技术价值：分析创新性、技术复杂度、先进性
   - 法律价值：评估权利要求稳定性与保护范围
   - 市场价值：分析氨纶行业规模与竞争格局
   - 经济价值：评估成本效益与许可潜力
   - 战略价值：分析产业链地位与政策契合度

### MCP-ClickHouse 查询验证 ✅ 已验证

**CNKI 查询结果**（返回5条聚氨酯相关文献，最高被引92次）:
- 环氧改性水性聚氨酯乳液的制备及其膜性能 (2009, 被引92次)
- EG/MRP/DMMP协同阻燃硬质聚氨酯泡沫塑料的性能研究 (2015, 被引9次)
- 超软聚氨酯泡沫塑料的生产 (2014, 被引9次)
- 糖醇的功能和工业用途开发前景 (2010, 被引9次)
- 热塑性聚氨酯弹性体/氢氧化铝纳米复合材料的热性能分析 (2010, 被引9次)

**WOS 查询结果**（返回5条polyurethane相关论文，最高被引93次）:
- Characterization and mechanical performance comparison of multiwalled carbon nanotube/polyurethane composites (2013, TC=93)
- Study of geometric effects on nonpneumatic tire spoke structures (2022, TC=9)
- Agro-wastes and Inert Materials as Supports for Biosurfactants (2021, TC=9)
- A lab study to develop polyurethane concrete for bridge deck pavement (2022, TC=9)
- Self-repairing cement mortars with microcapsules (2020, TC=9)

```sql
-- CNKI 检索：氨纶/聚氨酯相关文献
SELECT title, abstract, keyword, creator, institute, year, cited_num
FROM CERS.CNKI
WHERE (title LIKE '%氨纶%' OR abstract LIKE '%聚氨酯%' OR keyword LIKE '%spandex%')
ORDER BY cited_num DESC
LIMIT 10;

-- WOS 检索：spandex/polyurethane 高被引论文
SELECT TI, AB, AU, SO, TC, PY, UT
FROM CERS.WOS
WHERE (TI LIKE '%spandex%' OR AB LIKE '%polyurethane%')
ORDER BY TC DESC
LIMIT 10;
```

---

## 测试用例 2：锂电池正极材料专利

### 输入信息

- **专利号**: CN202210123456.7（示例）
- **申请人**: 宁德时代新能源科技股份有限公司
- **发明名称**: 一种高镍三元正极材料及其制备方法
- **IPC 分类**: H01M4/1393；H01M4/36；H01M10/0525
- **专利类型**: 发明

### 技术方案要点

1. 采用 Ni-Co-Mn 三元体系，镍含量≥80%
2. 表面包覆氧化铝与钛酸锂复合层
3. 引入镁、铝共掺杂改善晶体结构稳定性
4. 采用喷雾干燥工艺控制颗粒形貌

### 预期输出

1. **新颖性评述**: 对比现有高镍正极材料专利
2. **创造性评述**: 分析复合包覆层与掺杂的协同效应
3. **市场价值**: 分析动力电池行业规模、竞争格局（CATL、LG、松下等）
4. **战略价值**: 分析在新能源汽车产业链中的地位

### MCP-ClickHouse 查询验证

```sql
-- CNKI 检索：锂电池正极材料
SELECT title, abstract, creator, institute, year, cited_num
FROM CERS.CNKI
WHERE (title LIKE '%锂电池%' OR abstract LIKE '%正极材料%')
ORDER BY cited_num DESC
LIMIT 10;
```

---

## 测试用例 3：生物医药专利

### 输入信息

- **专利号**: CN202110987654.3（示例）
- **申请人**: 恒瑞医药股份有限公司
- **发明名称**: 一种靶向 PD-1/PD-L1 的单克隆抗体药物
- **IPC 分类**: C07K16/28；A61K39/395；A61P35/00
- **专利类型**: 发明

### 技术方案要点

1. 人源化 IgG4 单克隆抗体
2. 靶向 PD-1 与 PD-L1 双重免疫检查点
3. 优化 Fc 段增强 ADCC 效应
4. 联合化疗药物的协同治疗方案

### 预期输出

1. **新颖性评述**: 对比现有 PD-1/PD-L1 抑制剂专利
2. **创造性评述**: 分析双重靶向与 Fc 优化的创新点
3. **市场价值**: 分析免疫治疗市场规模与竞争格局
4. **经济价值**: 评估药物专利许可与转让价值

### MCP-ClickHouse 查询验证

```sql
-- WOS 检索：PD-1/PD-L1 immunotherapy
SELECT TI, AB, AU, SO, TC, PY
FROM CERS.WOS
WHERE (TI LIKE '%PD-1%' OR AB LIKE '%immune checkpoint%')
ORDER BY TC DESC
LIMIT 10;
```

---

## 测试执行步骤

1. 准备测试输入（专利文件或元数据）
2. 执行专利文件解析
3. 运行 MCP-ClickHouse 学术文献检索
4. 生成评述与结论
5. 验证报告结构完整性
6. 检查五维度评价的逻辑性与数据支撑
7. 对比参考文档格式一致性

## 质量标准

| 检查项 | 标准 | 通过条件 |
|--------|------|---------|
| 结构完整性 | 包含 A/B/C/D/E/F 所有章节 | 所有章节存在且格式正确 |
| 新颖性评述 | 引用具体对比文件 | 至少引用2份对比文件 |
| 创造性评述 | 分析区别技术特征 | 明确列出区别特征与有益效果 |
| 学术文献检索 | 使用 MCP-ClickHouse | 查询语句正确且有结果 |
| 五维度评价 | 覆盖5个维度 | 每个维度有具体分析内容 |
| 评分合理性 | 1-10分制 | 评分有数据支撑 |
| 格式规范 | Markdown 格式 | 表格、标题、引用格式正确 |
