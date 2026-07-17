-- =====================================================
-- ClickHouse: 全球 & 中国行业基准（IPC 小类级）
-- 计算各 IPC 小类（前4位）的均值、分位数
-- 输出：industry_quantile（密度/引用/家族/权利要求/价值 5 维）
-- =====================================================

-- ============ Step 1: 去重中间表 ============
DROP TABLE IF EXISTS XiaoSu.tmp_patent_dedup;

CREATE TABLE XiaoSu.tmp_patent_dedup
ENGINE = MergeTree()
ORDER BY (ipc_subclass, application_num)
AS SELECT
    substring(`ipc_main`, 1, 4) AS ipc_subclass,
    `application_num`,
    toInt32OrNull(nullIf(`cited_count`, '')) AS cited,
    toInt32OrNull(nullIf(`family_count`, '')) AS family,
    toInt32OrNull(nullIf(`claims_num`, '')) AS claims,
    toInt32OrNull(nullIf(`patent_value_score`, '')) AS value_score,
    `applicants_normal_stat`,
    `country_name_stat_CH`
FROM XiaoSu.t_patent_data
WHERE toYear(parseDateTimeBestEffortOrNull(`application_date`)) >= 2000
  AND `application_date` != ''
ORDER BY `application_num`
LIMIT 1 BY `application_num`;

-- ============ Step 2: 建基准结果表 ============
DROP TABLE IF EXISTS XiaoSu.industry_quantile;

CREATE TABLE XiaoSu.industry_quantile
(
    scope              String,
    ipc_subclass       String,
    patent_count       UInt64,
    enterprise_count   UInt64,
    avg_cited          Float64,
    avg_family         Float64,
    avg_claims         Float64,
    avg_value          Float64,
    avg_density        Float64,
    density_dist       Array(Float64),
    cited_dist         Array(Float64),
    family_dist        Array(Float64),
    claims_dist        Array(Float64),
    value_dist         Array(Float64)
)
ENGINE = MergeTree()
ORDER BY (scope, ipc_subclass);

-- ============ Step 3: 临时表：企业密度（全球） ============
DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_global;

CREATE TABLE XiaoSu.tmp_ent_subclass_global
ENGINE = MergeTree()
ORDER BY (applicant_name, ipc_subclass)
AS SELECT
    arrayJoin(
        arrayFilter(x -> x != '', arrayMap(x -> trim(x), splitByString(',', `applicants_normal_stat`)))
    ) AS applicant_name,
    ipc_subclass,
    count(*) AS patent_cnt
FROM XiaoSu.tmp_patent_dedup
WHERE ipc_subclass != ''
GROUP BY applicant_name, ipc_subclass;

-- ============ Step 4: 全球基准 ============
INSERT INTO XiaoSu.industry_quantile
SELECT
    'global' AS scope,
    p.ipc_subclass,
    p.patent_count,
    d.enterprise_count,
    p.avg_cited, p.avg_family, p.avg_claims, p.avg_value,
    d.avg_density,
    d.density_dist,
    p.cited_dist,
    p.family_dist,
    p.claims_dist,
    p.value_dist
FROM (
    SELECT
        ipc_subclass,
        count(*) AS patent_count,
        avg(cited) AS avg_cited,
        avg(family) AS avg_family,
        avg(claims) AS avg_claims,
        avg(value_score) AS avg_value,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(cited) AS cited_dist,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(family) AS family_dist,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(claims) AS claims_dist,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(value_score) AS value_dist
    FROM XiaoSu.tmp_patent_dedup
    WHERE ipc_subclass != ''
    GROUP BY ipc_subclass
) p
INNER JOIN (
    SELECT
        ipc_subclass,
        count(*) AS enterprise_count,
        avg(patent_cnt) AS avg_density,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(patent_cnt) AS density_dist
    FROM XiaoSu.tmp_ent_subclass_global
    GROUP BY ipc_subclass
) d ON p.ipc_subclass = d.ipc_subclass
ORDER BY p.ipc_subclass;

-- ============ Step 5: 中国基准 ============
DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_china;

CREATE TABLE XiaoSu.tmp_ent_subclass_china
ENGINE = MergeTree()
ORDER BY (applicant_name, ipc_subclass)
AS SELECT
    arrayJoin(
        arrayFilter(x -> x != '', arrayMap(x -> trim(x), splitByString(',', `applicants_normal_stat`)))
    ) AS applicant_name,
    ipc_subclass,
    count(*) AS patent_cnt
FROM XiaoSu.tmp_patent_dedup
WHERE `country_name_stat_CH` = '中国' AND ipc_subclass != ''
GROUP BY applicant_name, ipc_subclass;

INSERT INTO XiaoSu.industry_quantile
SELECT
    'china' AS scope,
    p.ipc_subclass,
    p.patent_count,
    d.enterprise_count,
    p.avg_cited, p.avg_family, p.avg_claims, p.avg_value,
    d.avg_density,
    d.density_dist,
    p.cited_dist,
    p.family_dist,
    p.claims_dist,
    p.value_dist
FROM (
    SELECT
        ipc_subclass,
        count(*) AS patent_count,
        avg(cited) AS avg_cited,
        avg(family) AS avg_family,
        avg(claims) AS avg_claims,
        avg(value_score) AS avg_value,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(cited) AS cited_dist,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(family) AS family_dist,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(claims) AS claims_dist,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(value_score) AS value_dist
    FROM XiaoSu.tmp_patent_dedup
    WHERE `country_name_stat_CH` = '中国' AND ipc_subclass != ''
    GROUP BY ipc_subclass
) p
INNER JOIN (
    SELECT
        ipc_subclass,
        count(*) AS enterprise_count,
        avg(patent_cnt) AS avg_density,
        quantiles(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99)(patent_cnt) AS density_dist
    FROM XiaoSu.tmp_ent_subclass_china
    GROUP BY ipc_subclass
) d ON p.ipc_subclass = d.ipc_subclass
ORDER BY p.ipc_subclass;


-- ============ Step 6: 查看结果 ============
SELECT * FROM XiaoSu.industry_quantile ORDER BY scope, ipc_subclass LIMIT 10;

-- ============ 清理（可选） ============
-- DROP TABLE IF EXISTS XiaoSu.tmp_patent_dedup;
-- DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_global;
-- DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_china;
