#!/usr/bin/env python
"""
Debug script for lead_agent.
Run this file directly in VS Code with breakpoints.

Requirements:
    Run with `uv run` from the backend/ directory so that the uv workspace
    resolves deerflow-harness and app packages correctly:

        cd backend && PYTHONPATH=. uv run python debug.py

Usage:
    1. Set breakpoints in agent.py or other files
    2. Press F5 or use "Run and Debug" panel
    3. Input messages in the terminal to interact with the agent
"""

import asyncio
import logging
import shlex
import shutil
from pathlib import Path

from dotenv import load_dotenv

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory

    _HAS_PROMPT_TOOLKIT = True
except ImportError:
    _HAS_PROMPT_TOOLKIT = False

load_dotenv()

_LOG_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"
_UPLOAD_COMMANDS = {"upload", "attach"}
_DEFAULT_UPLOAD_PROMPT = "Please analyze the attached file(s)."


def _split_upload_command(user_input: str) -> tuple[list[str], str]:
    """Parse an upload command into file paths and an optional prompt."""
    tokens = shlex.split(user_input)
    if not tokens:
        return [], ""

    command = tokens[0].lower()
    if command not in _UPLOAD_COMMANDS:
        return [], user_input

    if len(tokens) == 1:
        return [], ""

    try:
        separator_index = tokens.index("--", 1)
    except ValueError:
        separator_index = len(tokens)

    file_args = tokens[1:separator_index]
    prompt = " ".join(tokens[separator_index + 1 :]) if separator_index < len(tokens) else ""
    return file_args, prompt


def _is_upload_command(user_input: str) -> bool:
    """Return True when *user_input* starts with an upload command."""
    tokens = shlex.split(user_input)
    return bool(tokens) and tokens[0].lower() in _UPLOAD_COMMANDS


def _copy_uploaded_file(source: Path, uploads_dir: Path) -> tuple[Path, list[Path]]:
    """Copy *source* into *uploads_dir* and return the stored path plus sidecars."""
    uploads_dir.mkdir(parents=True, exist_ok=True)

    source = source.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"File not found: {source}")

    destination = uploads_dir / source.name
    if destination.exists() and destination.resolve() != source:
        suffix = source.suffix
        stem = source.stem
        counter = 1
        while destination.exists():
            destination = uploads_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    copied_files: list[Path] = []
    if destination.resolve() != source:
        shutil.copy2(source, destination)
    copied_files.append(destination)

    sidecar_md = source.with_suffix(".md")
    if sidecar_md.is_file():
        sidecar_destination = destination.with_suffix(".md")
        if sidecar_destination.resolve() != sidecar_md.resolve():
            shutil.copy2(sidecar_md, sidecar_destination)
        copied_files.append(sidecar_destination)

    return destination, copied_files


def _build_upload_message(file_paths: list[str], uploads_dir: Path) -> list[dict]:
    """Copy uploaded files and build the message metadata expected by the agent."""
    files: list[dict] = []
    copied_sidecars: list[Path] = []

    for raw_path in file_paths:
        source = Path(raw_path)
        stored_path, sidecars = _copy_uploaded_file(source, uploads_dir)
        copied_sidecars.extend(sidecars)
        files.append(
            {
                "filename": stored_path.name,
                "size": stored_path.stat().st_size,
                "path": f"/mnt/user-data/uploads/{stored_path.name}",
                "status": "uploaded",
            }
        )

    if copied_sidecars:
        sidecar_names = ", ".join(sorted({path.name for path in copied_sidecars if path.name.endswith(".md")}))
        if sidecar_names:
            logging.getLogger(__name__).info("Copied upload sidecar markdown files: %s", sidecar_names)

    return files


def _print_upload_help() -> None:
    print("上传文件方式:")
    print("  upload /path/to/file1 /path/to/file2 -- 可选的提示消息")
    print("  attach /path/to/file1 -- 可选的提示消息")
    print("如果省略消息，将发送默认上传提示。")


def _setup_logging(log_level: int = logging.INFO) -> None:
    """Route logs to ``debug.log`` using *log_level* for the initial root/file setup.

    This configures the root logger and the ``debug.log`` file handler so logs do
    not print on the interactive console. It is idempotent: any pre-existing
    handlers on the root logger (e.g. installed by ``logging.basicConfig`` in
    transitively imported modules) are removed so the debug session output only
    lands in ``debug.log``.

    Note: later config-driven logging adjustments may change named logger
    verbosity without raising the root logger or file-handler thresholds set
    here, so the eventual contents of ``debug.log`` may not be filtered solely by
    this function's ``log_level`` argument.
    """
    root = logging.root
    for h in list(root.handlers):
        root.removeHandler(h)
        h.close()
    root.setLevel(log_level)

    file_handler = logging.FileHandler("run_agnet.log", mode="a", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(_LOG_FMT, datefmt=_LOG_DATEFMT))
    root.addHandler(file_handler)


async def main():
    # Install file logging first so warnings emitted while loading config do not
    # leak onto the interactive terminal via Python's lastResort handler.
    _setup_logging()

    from deerflow.config import get_app_config
    from deerflow.config.app_config import apply_logging_level

    app_config = get_app_config()
    apply_logging_level(app_config.log_level)

    # Delay the rest of the deerflow imports until *after* logging is installed
    # so that any import-time side effects (e.g. deerflow.agents starts a
    # background skill-loader thread on import) emit logs to debug.log instead
    # of leaking onto the interactive terminal via Python's lastResort handler.
    from langchain_core.messages import HumanMessage
    from langgraph.runtime import Runtime

    from deerflow.agents import make_lead_agent
    from deerflow.mcp import initialize_mcp_tools

    # Initialize MCP tools at startup
    try:
        await initialize_mcp_tools()
    except Exception as e:
        print(f"警告: MCP 工具初始化失败: {e}")

    # Create agent with default config
    config = {
        "configurable": {
            "thread_id": "thread-001",
            "thinking_enabled": True,
            "is_plan_mode": True,
            "subagent_enabled": True,
            # Uncomment to use a specific model
            "model_name": "Qwen3.6-27B",
        }
    }

    runtime = Runtime(context={"thread_id": config["configurable"]["thread_id"]})
    config["configurable"]["__pregel_runtime"] = runtime

    agent = make_lead_agent(config)

    session = PromptSession(history=InMemoryHistory()) if _HAS_PROMPT_TOOLKIT else None

    print("=" * 50)
    print("Lead Agent 后端运行模式")
    print("输入 'quit' 或 'exit' 停止")
    _print_upload_help()
    print(f"日志: run_agent.log (日志级别={app_config.log_level})")
    if not _HAS_PROMPT_TOOLKIT:
        print("提示: `uv sync --group dev` 启用方向键和历史支持")
    print("=" * 50)

    # ⭐ 保存历史消息
    history_messages = []
    seen_artifacts: set[str] = set()

    from deerflow.config.paths import get_paths
    from deerflow.runtime.user_context import get_effective_user_id

    paths = get_paths()
    thread_id = config["configurable"]["thread_id"]
    user_id = get_effective_user_id()
    uploads_dir = paths.sandbox_uploads_dir(thread_id, user_id=user_id)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            if session:
                user_input = (await session.prompt_async("\nYou: ")).strip()
            else:
                user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                print("再见!")
                break

            file_args, prompt = _split_upload_command(user_input)
            if not file_args and _is_upload_command(user_input):
                _print_upload_help()
                continue
            if file_args:
                files = _build_upload_message(file_args, uploads_dir)
                message_text = prompt or _DEFAULT_UPLOAD_PROMPT
                human_msg = HumanMessage(content=message_text, additional_kwargs={"files": files})
                print(f"已上传 {len(files)} 个文件: {', '.join(file['filename'] for file in files)}")
            else:
                human_msg = HumanMessage(content=user_input)

            # 加入历史
            history_messages.append(human_msg)
            # 把完整历史传进去
            state = {"messages": history_messages}

            msgs = None
            async for chunk in agent.astream(state, stream_mode="values", config=config):
                if "messages" not in chunk:
                    continue
                msgs = chunk["messages"]
                msgs[-1].pretty_print()
            history_messages = msgs

            # Show files presented to the user this turn (new artifacts only)
            artifacts = chunk.get("artifacts") or []
            new_artifacts = [p for p in artifacts if p not in seen_artifacts]
            if new_artifacts:
                print("\n[新保存的文件]")
                for virtual in new_artifacts:
                    try:
                        physical = paths.resolve_virtual_path(thread_id, virtual, user_id=user_id)
                        print(f"  - {virtual}\n    → {physical}")
                    except ValueError as exc:
                        print(f"  - {virtual}    (解析物理路径失败: {exc})")
                seen_artifacts.update(new_artifacts)
            # print(history_messages)
        except (KeyboardInterrupt, EOFError):
            print("\n再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
