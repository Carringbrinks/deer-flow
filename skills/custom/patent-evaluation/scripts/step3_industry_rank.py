#!/usr/bin/env python3
"""第三阶段：企业行业位阶排名
取每家企业专利数量最多的前 3 个 IPC 小类，对照行业基准分位数插值得出百分位，
按专利数量加权计算综合百分位并分档定级。
输出表：XiaoSu.enterprise_industry_rank
依赖 SQL：../references/enterprise_industry_rank_v3.sql
阶段依赖：需要先执行 step1 和 step2。
"""

import asyncio
import os
import sys

from loguru import logger

from common import execute_sql, execute_sql_file, format_result

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SQL_REF_DIR = os.path.join(SKILL_DIR, "references")

LABEL = "Step3"


async def main():
    sql_file = os.path.join(SQL_REF_DIR, "enterprise_industry_rank_v3.sql")
    if not os.path.exists(sql_file):
        logger.error(f"找不到 SQL 文件 {sql_file}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("第三阶段：企业行业位阶排名")
    logger.info(f"SQL 文件: {sql_file}")
    logger.info("=" * 60)

    logger.info(f"[{LABEL}] 清理历史临时表...")
    cleanup_sqls = [
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_metrics",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_top3_subclass",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_pct",
    ]
    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
        except Exception:
            pass

    await execute_sql_file(LABEL, sql_file)

    logger.info(f"[{LABEL}] 验证结果...")
    result = await execute_sql(
        "SELECT level, count() AS cnt FROM XiaoSu.enterprise_industry_rank "
        "GROUP BY level ORDER BY cnt DESC"
    )
    logger.info(f"enterprise_industry_rank 等级分布: {format_result(result)}")

    logger.info("第三阶段完成！")


if __name__ == "__main__":
    asyncio.run(main())
