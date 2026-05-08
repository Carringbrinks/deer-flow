#!/usr/bin/env python
"""
Lightweight debug runner for the DeerFlow lead agent.

需求：
1. 每次请求后，按顺序打印 Human / AI / Tool 等 message
2. 用户再次输入时，自动带上历史对话上下文
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    _HAS_PROMPT_TOOLKIT = True
except Exception:
    _HAS_PROMPT_TOOLKIT = False

load_dotenv()

DEFAULT_CONFIG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "config.yaml")
)

_LOG_FMT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _setup_logging(level_name: str) -> None:
    try:
        mapping = logging.getLevelNamesMapping()
        lvl = (level_name or "INFO").strip().upper()
        level = mapping.get(lvl, logging.INFO)
    except Exception:
        level = logging.INFO

    root = logging.root
    for h in list(root.handlers):
        root.removeHandler(h)
        h.close()

    root.setLevel(level)

    file_handler = logging.FileHandler(
        "debug_agent.log", mode="a", encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter(_LOG_FMT, datefmt=_LOG_DATEFMT)
    )
    root.addHandler(file_handler)




async def main():
    config_path = os.environ.get(
        "DEER_FLOW_CONFIG_PATH",
        DEFAULT_CONFIG_PATH
    )
    os.environ["DEER_FLOW_CONFIG_PATH"] = config_path

    _setup_logging("INFO")

    from langchain_core.messages import HumanMessage
    from langgraph.runtime import Runtime

    from deerflow.agents import make_lead_agent
    from deerflow.mcp import initialize_mcp_tools
    from deerflow.config import get_app_config

    try:
        await initialize_mcp_tools()
    except Exception as e:
        print(f"Warning: Failed to initialize MCP tools: {e}")

    app_config = get_app_config()
    print((f"Loaded app config: {app_config}"))
    thread_id = os.environ.get("THREAD_ID", "debug-thread-004")
    model_name = os.environ.get("MODEL_NAME")

    config = {
        "configurable": {
            "thread_id": thread_id,
            "thinking_enabled": True,
            "is_plan_mode": True,
            "subagent_enabled": False
        }
    }

    if model_name:
        config["configurable"]["model_name"] = model_name

    # Include `user_id` in runtime context so downstream components (e.g.
    # middlewares, paths resolution) can pick it up from the runtime as well.
    runtime_ctx = {"thread_id": thread_id}


    runtime = Runtime(context=runtime_ctx)
    config["configurable"]["__pregel_runtime"] = runtime

    print(f"Using config: {config}")

    agent = make_lead_agent(config)

    session = PromptSession(
        history=InMemoryHistory()
    ) if _HAS_PROMPT_TOOLKIT else None

    print("=" * 50)
    print("Lead Agent Debug Agent")
    print("Type quit / exit to stop")
    print("=" * 50)

    # ⭐ 保存历史消息
    history_messages = []

    while True:
        try:
            if session:
                user_input = (await session.prompt_async("\nYou: ")).strip()
            else:
                user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            # 当前用户输入
            human_msg = HumanMessage(content=user_input)

            # 加入历史
            history_messages.append(human_msg)

            # 把完整历史传进去
            state = {
                "messages": history_messages
            }

            print("\n开始执行...\n")

            msgs = None
            async for chunk in agent.astream(state,stream_mode="values",config=config):
                if "messages" not in chunk:
                    continue

                msgs = chunk["messages"]
                msgs[-1].pretty_print()
                # while seen < len(msgs):
                #     pretty_message(msgs[seen])
                #     seen += 1

            history_messages = msgs
            # print(history_messages)
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    workspace_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)

    asyncio.run(main())


