-- =====================================================
-- ClickHouse: 企业行业位阶（对照全球/中国基准，3维）
-- 1. 取企业专利数前 3 IPC 小类，按数量赋权
-- 2. 对照 industry_quantile 分位数插值得到百分位
-- 3. 3 维（密度/引用/家族）取均值→综合位阶
-- =====================================================

-- ============ Step 1: 企业 × 小类 指标（仅该小类下专利）============
DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_metrics;

CREATE TABLE XiaoSu.tmp_ent_subclass_metrics
ENGINE = MergeTree()
ORDER BY (enterprise_name, subclass)
AS SELECT
    enterprise_name,
    subclass,
    count(*) AS cnt,
    avg(avg_cited) AS avg_cited,
    avg(avg_family) AS avg_family,
    avg(avg_claims) AS avg_claims
FROM (
    SELECT DISTINCT
        enterprise_name,
        substring(trim(ipc_raw), 1, 4) AS subclass,
        cited AS avg_cited,
        family AS avg_family,
        claims AS avg_claims
    FROM XiaoSu.tmp_enterprise_patent
    ARRAY JOIN splitByString(';', `IPC分类号`) AS ipc_raw
    WHERE `IPC分类号` != '' AND substring(trim(ipc_raw), 1, 4) != ''
)
GROUP BY enterprise_name, subclass;

-- ============ Step 2: 前 3 小类（按专利条数） ============
DROP TABLE IF EXISTS XiaoSu.tmp_ent_top3_subclass;

CREATE TABLE XiaoSu.tmp_ent_top3_subclass
ENGINE = MergeTree()
ORDER BY (enterprise_name, subclass)
AS SELECT
    enterprise_name,
    subclass,
    cnt
FROM (
    SELECT
        enterprise_name,
        subclass,
        cnt,
        row_number() OVER (PARTITION BY enterprise_name ORDER BY cnt DESC) AS rn
    FROM XiaoSu.tmp_ent_subclass_metrics
)
WHERE rn <= 3;

-- ============ Step 3: 建位阶结果表 ============
DROP TABLE IF EXISTS XiaoSu.enterprise_industry_rank;

CREATE TABLE XiaoSu.enterprise_industry_rank
(
    enterprise_name      String,
    scope                String,
    main_subclass        String,
    top3_subclasses      String,
    top3_counts          String,
    pct_density          Float64,
    pct_cited            Float64,
    pct_family           Float64,
    pct_composite        Float64,
    level                String,
    eval_date            Date DEFAULT today()
)
ENGINE = MergeTree()
ORDER BY (scope, pct_composite);

-- ============ Step 4a: 中间表（企业 × 小类 × scope × 百分位，不含claims）============
DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_pct;

CREATE TABLE XiaoSu.tmp_ent_subclass_pct
(
    enterprise_name String,
    scope String,
    subclass String,
    cnt UInt64,
    pct_density Float64,
    pct_cited Float64,
    pct_family Float64
)
ENGINE = MergeTree()
ORDER BY enterprise_name;

INSERT INTO XiaoSu.tmp_ent_subclass_pct
SELECT
    t3.enterprise_name,
    q.scope,
    t3.subclass,
    t3.cnt,
    multiIf(
        t3.cnt / eval.span_years > q.density_dist[99], 100,
        arrayFirstIndex(x -> t3.cnt / eval.span_years <= x, q.density_dist) / 99 * 100
    ) AS pct_density,
    multiIf(
        sub.avg_cited > q.cited_dist[99], 100,
        arrayFirstIndex(x -> sub.avg_cited <= x, q.cited_dist) / 99 * 100
    ) AS pct_cited,
    multiIf(
        sub.avg_family > q.family_dist[99], 100,
        arrayFirstIndex(x -> sub.avg_family <= x, q.family_dist) / 99 * 100
    ) AS pct_family
FROM XiaoSu.tmp_ent_top3_subclass AS t3
INNER JOIN XiaoSu.industry_quantile q ON t3.subclass = q.ipc_subclass
INNER JOIN XiaoSu.tmp_ent_subclass_metrics sub ON t3.enterprise_name = sub.enterprise_name AND t3.subclass = sub.subclass
INNER JOIN XiaoSu.enterprise_eval_result eval ON t3.enterprise_name = eval.enterprise_name;

-- ============ Step 4b: 按企业、scope 聚合（加权平均）============
INSERT INTO XiaoSu.enterprise_industry_rank
SELECT
    enterprise_name,
    scope,
    main_subclass,
    top3_subclasses,
    top3_counts,
    total_density / total_cnt AS pct_density,
    total_cited / total_cnt AS pct_cited,
    total_family / total_cnt AS pct_family,
    (total_density + total_cited + total_family) / (3 * total_cnt) AS pct_composite,
    multiIf(
        (total_density + total_cited + total_family) / (3 * total_cnt) >= 90, '行业领先',
        (total_density + total_cited + total_family) / (3 * total_cnt) >= 70, '行业优秀',
        (total_density + total_cited + total_family) / (3 * total_cnt) >= 50, '行业中上',
        (total_density + total_cited + total_family) / (3 * total_cnt) >= 30, '行业平均',
        (total_density + total_cited + total_family) / (3 * total_cnt) >= 10, '行业落后',
        '行业底部'
    ) AS level,
    today() AS eval_date
FROM (
    SELECT
        enterprise_name,
        scope,
        argMax(subclass, cnt) AS main_subclass,
        groupArray(subclass) AS top3_subclasses,
        groupArray(cnt) AS top3_counts,
        sum(pct_density * cnt) AS total_density,
        sum(pct_cited * cnt) AS total_cited,
        sum(pct_family * cnt) AS total_family,
        sum(cnt) AS total_cnt
    FROM XiaoSu.tmp_ent_subclass_pct
    GROUP BY enterprise_name, scope
) agg
ORDER BY enterprise_name, scope;


-- ============ Step 5: 查看结果 ============
SELECT
    enterprise_name, scope, main_subclass,
    top3_subclasses, top3_counts,
    round(pct_density, 1) AS pct_density,
    round(pct_cited, 1) AS pct_cited,
    round(pct_family, 1) AS pct_family,
    round(pct_composite, 1) AS pct_composite,
    level
FROM XiaoSu.enterprise_industry_rank
ORDER BY pct_composite DESC
LIMIT 10;