-- =====================================================
-- ClickHouse: 企业科创属性评价模型（AI 数据）
-- 基于 t_patent_data_ai（AI 专利数据）
-- 逻辑与 enterprise_eval_ch.sql 完全一致，临时表和结果表均以 _ai 后缀区分
-- 输出表：XiaoSu.enterprise_eval_result_ai（独立于 CCB）
-- =====================================================

-- ============ Step 1: 结果表 ============
DROP TABLE IF EXISTS XiaoSu.enterprise_eval_result_ai;

CREATE TABLE XiaoSu.enterprise_eval_result_ai
(
    enterprise_name  String,
    patent_count     UInt64,
    span_years       Float64,
    density          Float64,
    recent_ratio     Float64,
    qty_score        Float64,
    quality_score    Float64,
    layout_score     Float64,
    commercial_score Float64,
    rd_score         Float64,
    legal_score      Float64,
    qual_score       Float64,
    total_score      Float64,
    eval_date        Date DEFAULT today()
)
ENGINE = MergeTree()
ORDER BY total_score;

-- ============ Step 2: 拆解企业名称 ============
DROP TABLE IF EXISTS XiaoSu.tmp_enterprise_patent_ai;

CREATE TABLE XiaoSu.tmp_enterprise_patent_ai
ENGINE = MergeTree()
ORDER BY (enterprise_name)
AS SELECT
    enterprise_name,
    `专利类型`,
    `申请日` AS apply_date,
    `被引用数量` AS cited,
    `引用数量` AS refs,
    `申请人数量` AS applicant_cnt,
    `发明人数量` AS inventor_cnt,
    `权利要求数` AS claims,
    `同族专利数` AS family,
    `许可次数` AS license_cnt,
    `转让次数` AS transfer_cnt,
    `质押次数` AS pledge_cnt,
    `诉讼次数` AS lawsuit_cnt,
    `复审次数` AS reexam_cnt,
    `无效次数` AS invalid_cnt,
    `专利状态`,
    `IPC分类号`,
    `战略性新兴产业`,
    `企业类型`,
    `科技型企业`,
    `企业规模`,
    `上市状态`,
    `数字经济核心产业`,
    `绿色低碳技术`
FROM XiaoSu.t_patent_data_ai
ARRAY JOIN arrayDistinct(arrayFilter(
    x -> x != '' AND length(x) > 1,
    arrayMap(x -> trim(x), arrayConcat(
        splitByString(';', `申请人`),
        splitByString(';', `专利权人`)
    ))
)) AS enterprise_name;

-- ============ Step 3: 拆解 IPC 大类 ============
DROP TABLE IF EXISTS XiaoSu.tmp_ipc_classes_ai;

CREATE TABLE XiaoSu.tmp_ipc_classes_ai
ENGINE = MergeTree()
ORDER BY (enterprise_name)
AS SELECT DISTINCT
    enterprise_name,
    substring(trim(ipc_raw), 1, 4) AS ipc_class
FROM (
    SELECT enterprise_name, arrayJoin(splitByString(';', `IPC分类号`)) AS ipc_raw
    FROM XiaoSu.tmp_enterprise_patent_ai
    WHERE `IPC分类号` != ''
)
WHERE substring(trim(ipc_raw), 1, 4) != '';

-- ============ Step 4: 拆解战略性新兴产业 ============
DROP TABLE IF EXISTS XiaoSu.tmp_strategic_ai;

CREATE TABLE XiaoSu.tmp_strategic_ai
ENGINE = MergeTree()
ORDER BY (enterprise_name)
AS SELECT DISTINCT
    enterprise_name,
    trim(si_raw) AS si
FROM (
    SELECT enterprise_name, arrayJoin(splitByString(';', `战略性新兴产业`)) AS si_raw
    FROM XiaoSu.tmp_enterprise_patent_ai
    WHERE `战略性新兴产业` != ''
)
WHERE trim(si_raw) != '';

-- ============ Step 5a: IPC 计数表（按企业聚合） ============
DROP TABLE IF EXISTS XiaoSu.tmp_ipc_count_ai;

CREATE TABLE XiaoSu.tmp_ipc_count_ai
ENGINE = MergeTree()
ORDER BY enterprise_name
AS SELECT enterprise_name, count(*) AS cnt
    FROM XiaoSu.tmp_ipc_classes_ai
GROUP BY enterprise_name;

-- ============ Step 5b: 战略性新兴产业计数表（按企业聚合） ============
DROP TABLE IF EXISTS XiaoSu.tmp_strategic_count_ai;

CREATE TABLE XiaoSu.tmp_strategic_count_ai
ENGINE = MergeTree()
ORDER BY enterprise_name
AS SELECT enterprise_name, count(*) AS cnt
    FROM XiaoSu.tmp_strategic_ai
GROUP BY enterprise_name;

-- ============ Step 5c: 聚合计算（写入 enterprise_eval_result_ai）============
INSERT INTO XiaoSu.enterprise_eval_result_ai
SELECT
    enterprise_name,
    total AS patent_count,
    dateDiff('day', earliest, today()) / 365.25 + 0.5 AS span_years,
    total / (dateDiff('day', earliest, today()) / 365.25 + 0.5) AS density,
    recent_cnt / total AS recent_ratio,
    least(density * 20, 100) * 0.5 + least(patent_type_cnt * 20, 100) * 0.3 + (recent_cnt / total * 100) * 0.2 AS qty_score,
    least(total_cited * 2, 100) * 0.3 + least(avg_claims * 5, 100) * 0.25 + least(avg_family * 20, 100) * 0.25 + least(total_refs, 100) * 0.2 AS quality_score,
    least(ipc_class_cnt * 5, 100) * 0.3 + least(strategic_cnt * 20, 100) * 0.25 + multiIf(digital_flag > 0, 100, 0) * 0.25 + multiIf(green_flag > 0, 100, 0) * 0.2 AS layout_score,
    least(total_transfer * 10, 100) * 0.35 + least(total_license * 10, 100) * 0.30 + least(total_pledge * 10, 100) * 0.35 AS commercial_score,
    least(avg_inventor * 10, 100) * 0.5 + least(avg_applicant * 20, 100) * 0.5 AS rd_score,
    least(active_cnt / total * 100, 100) * 0.4 + greatest(100 - least(total_reexam * 20, 100), 0) * 0.2 + greatest(100 - least(total_invalid * 20, 100), 0) * 0.2 + greatest(100 - least(total_lawsuit * 20, 100), 0) * 0.2 AS legal_score,
    multiIf(tech_ent != '' AND tech_ent != '0', 100, 0) * 0.3 + multiIf(listed = '上市', 100, listed != '', 50, 0) * 0.25 + multiIf(ent_scale = '大型', 100, ent_scale = '中型', 70, ent_scale = '小型', 50, 0) * 0.25 + multiIf(ent_type LIKE '%高新技术%', 100, ent_type != '', 50, 0) * 0.2 AS qual_score,
    (least(density * 20, 100) * 0.5 + least(patent_type_cnt * 20, 100) * 0.3 + (recent_cnt / total * 100) * 0.2) * 0.15
    + (least(total_cited * 2, 100) * 0.3 + least(avg_claims * 5, 100) * 0.25 + least(avg_family * 20, 100) * 0.25 + least(total_refs, 100) * 0.2) * 0.20
    + (least(ipc_class_cnt * 5, 100) * 0.3 + least(strategic_cnt * 20, 100) * 0.25 + multiIf(digital_flag > 0, 100, 0) * 0.25 + multiIf(green_flag > 0, 100, 0) * 0.2) * 0.15
    + (least(total_transfer * 10, 100) * 0.35 + least(total_license * 10, 100) * 0.30 + least(total_pledge * 10, 100) * 0.35) * 0.15
    + (least(avg_inventor * 10, 100) * 0.5 + least(avg_applicant * 20, 100) * 0.5) * 0.10
    + (least(active_cnt / total * 100, 100) * 0.4 + greatest(100 - least(total_reexam * 20, 100), 0) * 0.2 + greatest(100 - least(total_invalid * 20, 100), 0) * 0.2 + greatest(100 - least(total_lawsuit * 20, 100), 0) * 0.2) * 0.10
    + (multiIf(tech_ent != '' AND tech_ent != '0', 100, 0) * 0.3 + multiIf(listed = '上市', 100, listed != '', 50, 0) * 0.25 + multiIf(ent_scale = '大型', 100, ent_scale = '中型', 70, ent_scale = '小型', 50, 0) * 0.25 + multiIf(ent_type LIKE '%高新技术%', 100, ent_type != '', 50, 0) * 0.2) * 0.15 AS total_score,
    today() AS eval_date
FROM (
    SELECT
        ep.enterprise_name AS enterprise_name,
        count(*) AS total,
        countDistinct(`专利类型`) AS patent_type_cnt,
        min(apply_date) AS earliest,
        max(apply_date) AS latest,
        countIf(apply_date >= today() - INTERVAL 3 YEAR) AS recent_cnt,
        sum(cited) AS total_cited,
        sum(refs) AS total_refs,
        avg(claims) AS avg_claims,
        avg(family) AS avg_family,
        avg(inventor_cnt) AS avg_inventor,
        avg(applicant_cnt) AS avg_applicant,
        sum(transfer_cnt) AS total_transfer,
        sum(license_cnt) AS total_license,
        sum(pledge_cnt) AS total_pledge,
        sum(reexam_cnt) AS total_reexam,
        sum(invalid_cnt) AS total_invalid,
        sum(lawsuit_cnt) AS total_lawsuit,
        countIf(`专利状态` IN ('有效', '审查中')) AS active_cnt,
        any(`企业类型`) AS ent_type,
        any(`科技型企业`) AS tech_ent,
        any(`企业规模`) AS ent_scale,
        any(`上市状态`) AS listed,
        countIf(`数字经济核心产业` != '') AS digital_flag,
        countIf(`绿色低碳技术` != '') AS green_flag,
        max(ipc.cnt) AS ipc_class_cnt,
        max(si.cnt) AS strategic_cnt
    FROM XiaoSu.tmp_enterprise_patent_ai AS ep
    LEFT JOIN XiaoSu.tmp_ipc_count_ai AS ipc ON ep.enterprise_name = ipc.enterprise_name
    LEFT JOIN XiaoSu.tmp_strategic_count_ai AS si ON ep.enterprise_name = si.enterprise_name
    GROUP BY ep.enterprise_name
) AS agg;

-- ============ Step 6: 清理中间表（可选） ============
-- DROP TABLE IF EXISTS tmp_enterprise_patent_ai;
-- DROP TABLE IF EXISTS tmp_ipc_classes_ai;
-- DROP TABLE IF EXISTS tmp_strategic_ai;
-- DROP TABLE IF EXISTS tmp_ipc_count_ai;
-- DROP TABLE IF EXISTS tmp_strategic_count_ai;
