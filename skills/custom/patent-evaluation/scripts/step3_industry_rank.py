#!/usr/bin/env python3
"""第三阶段：企业行业位阶排名
取企业专利数量最多的前 3 个 IPC 小类，对照行业基准分位数插值得出百分位，
按专利数量加权计算综合百分位并分档定级。
由 run_all.py 调用，参数通过 --datasets 指定。

输出表：XiaoSu.enterprise_industry_rank{suffix}
SQL 模板：../references/enterprise_industry_rank_template.sql
"""

import asyncio
import os
import sys

from loguru import logger

from common import execute_sql, execute_sql_text, format_result, render_sql_template

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SQL_REF_DIR = os.path.join(SKILL_DIR, "references")

LABEL = "Step3"


async def main(suffix: str):
    template_file = os.path.join(SQL_REF_DIR, "enterprise_industry_rank_template.sql")
    if not os.path.exists(template_file):
        logger.error(f"找不到 SQL 模板文件 {template_file}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info(f"第三阶段：企业行业位阶排名（suffix={suffix!r}）")
    logger.info("=" * 60)

    # 清理临时表
    logger.info(f"[{LABEL}] 清理历史临时表...")
    cleanup_sqls = [
        f"DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_metrics{suffix}",
        f"DROP TABLE IF EXISTS XiaoSu.tmp_ent_top3_subclass{suffix}",
        f"DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_pct{suffix}",
    ]
    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
        except Exception:
            pass

    # 渲染并执行模板 SQL
    logger.info(f"[{LABEL}] 渲染并执行 SQL 模板...")
    rendered = render_sql_template(template_file, suffix=suffix)
    await execute_sql_text(LABEL, rendered)

    # 验证结果
    logger.info(f"[{LABEL}] 验证结果...")
    result = await execute_sql(
        f"SELECT level, count() AS cnt FROM XiaoSu.enterprise_industry_rank{suffix} "
        f"GROUP BY level ORDER BY cnt DESC"
    )
    logger.info(f"enterprise_industry_rank{suffix} 等级分布: {format_result(result)}")
    logger.info(f"第三阶段完成！（suffix={suffix!r}）")


if __name__ == "__main__":
    # 直接运行时从命令行读取参数
    import argparse
    parser = argparse.ArgumentParser(description="企业行业位阶排名")
    parser.add_argument("--suffix", required=True, help="表后缀")
    args, _ = parser.parse_known_args()
    asyncio.run(main(suffix=args.suffix))
