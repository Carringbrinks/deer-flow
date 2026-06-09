#!/usr/bin/env python3
"""
convert_to_docx.py
将专利导航报告 report.md 转换为 report.docx

功能：
  1. 将 report.md 中的 /mnt/user-data 图片路径替换为本地实际路径
  2. 保存替换后的新 md 文件（report_local.md）
  3. 使用 pandoc 将新 md 转换为 docx（含目录、章节编号、中文环境）

用法：
  python convert_to_docx.py /path/to/report.md
  python convert_to_docx.py /path/to/report.md --output /path/to/report.docx
  python convert_to_docx.py /path/to/report.md --base-path /custom/user-data
"""

import argparse
import os
import subprocess
import sys

# report.md 中写死的虚拟路径前缀
OLD_VIRTUAL_PATH = "/mnt/user-data"


def resolve_base_path(md_path: str) -> str:
    """从 report.md 路径向上查找 user-data 目录。"""
    current = os.path.dirname(os.path.abspath(md_path))
    while current != "/" and current != "":
        if os.path.basename(current) == "user-data":
            return current
        current = os.path.dirname(current)

    print(f"错误: 无法从 '{md_path}' 向上找到 user-data 目录。", file=sys.stderr)
    print("请使用 --base-path 手动指定本地路径。", file=sys.stderr)
    sys.exit(1)


def replace_paths(input_path: str, old_prefix: str, new_prefix: str, output_path: str) -> int:
    """将文件中所有 old_prefix 替换为 new_prefix，写入 output_path，返回替换次数。"""
    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    count = content.count(old_prefix)
    if count == 0:
        print(f"    警告: 未找到需要替换的路径 '{old_prefix}'")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content.replace(old_prefix, new_prefix))

    return count


def run_pandoc(md_path: str, docx_path: str, work_dir: str) -> None:
    """调用 pandoc 将 md 转换为 docx。"""
    subprocess.run(
        [
            "pandoc",
            md_path,
            "-o",
            docx_path,
            "--toc",
            "--toc-depth=3",
            "--number-sections",
            "-V",
            "lang=zh-CN",
        ],
        cwd=work_dir,
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将专利导航报告 report.md 转换为 report.docx",
    )
    parser.add_argument(
        "input",
        metavar="MD_PATH",
        help="report.md 的全路径",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="DOCX_PATH",
        help="输出 docx 路径（默认与输入同目录，report.docx）",
    )
    parser.add_argument(
        "-b",
        "--base-path",
        default=None,
        metavar="BASE_PATH",
        help="图片路径替换的目标基础路径（默认从 MD_PATH 自动推断到 user-data）",
    )
    parser.add_argument(
        "--keep-md",
        action="store_true",
        default=True,
        help="保留替换路径后的中间 md 文件",
    )
    args = parser.parse_args()

    # ── 解析路径 ───────────────────────────────────────────────────────
    md_input = os.path.abspath(args.input)
    if not os.path.isfile(md_input):
        print(f"错误: 文件不存在 — {md_input}", file=sys.stderr)
        sys.exit(1)

    md_dir = os.path.dirname(md_input)

    # 输出 docx
    if args.output:
        docx_output = os.path.abspath(args.output)
    else:
        docx_output = os.path.join(md_dir, "report.docx")

    # 替换后的新 md
    base_name = os.path.splitext(os.path.basename(md_input))[0]
    md_replaced = os.path.join(md_dir, f"{base_name}_local.md")

    # 目标基础路径
    if args.base_path:
        base_path = os.path.abspath(args.base_path)
    else:
        base_path = resolve_base_path(md_input)

    # ── 打印信息 ───────────────────────────────────────────────────────
    print("=" * 44)
    print("  Patent Navigation Report → DOCX")
    print("=" * 44)
    print(f"  输入文件:       {md_input}")
    print(f"  替换后 md:      {md_replaced}")
    print(f"  输出 docx:      {docx_output}")
    print(f"  目标基础路径:   {base_path}")
    print(f"  虚拟路径前缀:   {OLD_VIRTUAL_PATH}")
    print("=" * 44)
    print()

    # ── 步骤 1：路径替换 ──────────────────────────────────────────────
    print(">>> 步骤 1/2: 替换图片路径并保存新 md")
    print(f"    {OLD_VIRTUAL_PATH} → {base_path}")

    count = replace_paths(md_input, OLD_VIRTUAL_PATH, base_path, md_replaced)
    print(f"    共替换 {count} 处路径 → {md_replaced}")
    print()

    # ── 步骤 2：Pandoc 转换 ────────────────────────────────────────────
    print(">>> 步骤 2/2: Pandoc 生成 DOCX")
    try:
        run_pandoc(md_replaced, docx_output, md_dir)
    except subprocess.CalledProcessError as e:
        print(f"✗ Pandoc 转换失败 (exit code {e.returncode})", file=sys.stderr)
        sys.exit(1)

    # ── 清理中间 md ────────────────────────────────────────────────────
    if not args.keep_md:
        os.unlink(md_replaced)
        print("    (已删除中间 md)")
    else:
        print(f"    (已保留中间 md: {md_replaced})")

    print()

    # ── 结果 ───────────────────────────────────────────────────────────
    if os.path.isfile(docx_output):
        size_mb = os.path.getsize(docx_output) / (1024 * 1024)
        print("=" * 44)
        print("  ✓ 转换成功!")
        print(f"  {docx_output}")
        print(f"  文件大小: {size_mb:.2f} MB")
        print("=" * 44)
    else:
        print("✗ 转换失败：未生成输出文件。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
