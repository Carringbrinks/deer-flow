#!/usr/bin/env python3
"""
DeerFlow API 会话能力测试脚本
使用方法: python test_conversation.py
"""

import json
import time

import requests

BASE_URL = "http://localhost:18001"
EMAIL = "admin@example.com"
PASSWORD = "admin123456"


class DeerFlowClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.current_thread_id: str | None = None
        self.csrf_token: str | None = None

    def _get_csrf_token(self) -> str | None:
        """从session cookie中获取CSRF token"""
        for cookie in self.session.cookies:
            if cookie.name == "csrf_token":
                return cookie.value
        return None

    def _build_headers(self, extra_headers: dict = None) -> dict:
        """构建请求头，自动添加CSRF token"""
        headers = extra_headers or {}
        if self.csrf_token:
            headers["X-CSRF-Token"] = self.csrf_token
        return headers

    def initialize_system(self) -> bool:
        """检查并初始化系统"""
        # 检查是否需要初始化
        resp = self.session.get(f"{self.base_url}/api/v1/auth/setup-status")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("needs_setup", False):
                print("⚠️  系统需要初始化admin账户...")
                init_resp = self.session.post(f"{self.base_url}/api/v1/auth/initialize", json={"email": EMAIL, "password": PASSWORD})
                if init_resp.status_code == 201:
                    print("✅ Admin账户创建成功")
                    return True
                else:
                    print(f"❌ 初始化失败: {init_resp.text}")
                    return False
        print("✅ 系统已初始化")
        return True

    def login(self) -> bool:
        """登录并保存cookie和CSRF token"""
        resp = self.session.post(f"{self.base_url}/api/v1/auth/login/local", data={"username": EMAIL, "password": PASSWORD})
        if resp.status_code == 200:
            # 从响应cookie中提取CSRF token，后续请求需要在header中携带
            self.csrf_token = self._get_csrf_token()
            print(f"✅ 登录成功 (CSRF token: {self.csrf_token[:8]}...)" if self.csrf_token else "✅ 登录成功 (未获取到CSRF token)")
            return True
        print(f"❌ 登录失败: {resp.text}")
        return False

    def create_thread(self, assistant_id: str = "lead_agent") -> str | None:
        """创建新线程"""
        resp = self.session.post(f"{self.base_url}/api/threads", json={"assistant_id": assistant_id}, headers=self._build_headers())
        if resp.status_code == 200:
            thread_id = resp.json()["thread_id"]
            print(f"✅ 线程创建成功: {thread_id}")
            self.current_thread_id = thread_id
            return thread_id
        print(f"❌ 创建线程失败: {resp.text}")
        return None

    @staticmethod
    def _extract_text(content) -> str:
        """从多种content格式中提取可读文本"""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    parts.append(block)
            return "".join(parts)
        if isinstance(content, dict):
            return content.get("text", str(content))
        return str(content) if content is not None else ""

    def send_message(self, message: str, stream: bool = True) -> dict:
        """发送消息并获取回复"""
        if not self.current_thread_id:
            print("❌ 没有活动线程")
            return {}

        payload = {
            "assistant_id": "lead_agent",
            "input": {"messages": [{"role": "user", "content": message}]},
            "stream_mode": ["messages-tuple"],
        }

        if stream:
            # 流式请求
            print(f"\n📤 发送: {message}")
            print("📥 回复: ", end="", flush=True)

            resp = self.session.post(f"{self.base_url}/api/threads/{self.current_thread_id}/runs/stream", json=payload, stream=True, headers=self._build_headers())

            full_response = ""
            current_event = None

            if resp.status_code == 200:
                for line in resp.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")

                        # SSE comment (heartbeat)
                        if line_str.startswith(": "):
                            continue

                        # SSE event field
                        if line_str.startswith("event: "):
                            current_event = line_str[7:]
                            continue

                        # SSE data field
                        if line_str.startswith("data: "):
                            try:
                                data = json.loads(line_str[6:])
                            except json.JSONDecodeError:
                                continue

                            # data: null — end signal or null payload
                            if data is None:
                                if current_event == "end":
                                    break
                                continue

                            if current_event == "metadata":
                                pass  # run_id, thread_id — not displayed

                            elif current_event == "messages":
                                # messages-tuple format: [chunk_dict, metadata_dict]
                                if isinstance(data, list) and len(data) >= 1:
                                    chunk = data[0]
                                    if isinstance(chunk, dict):
                                        content = self._extract_text(chunk.get("content", ""))
                                        if content:
                                            print(content, end="", flush=True)
                                            full_response += content

                            elif current_event == "error":
                                msg = data.get("message", str(data)) if isinstance(data, dict) else str(data)
                                print(f"\n⚠️  错误: {msg}")

                            elif current_event == "custom":
                                # subagent progress, etc. — skip for now
                                pass

                            elif current_event == "values":
                                # Full state snapshot — skip (content comes via messages)
                                pass

                print("\n")
                return {"content": full_response}
            else:
                print(f"\n❌ 请求失败: {resp.text}")
                return {}
        else:
            # 非流式（等待完成）
            resp = self.session.post(f"{self.base_url}/api/threads/{self.current_thread_id}/runs/wait", json=payload, headers=self._build_headers())
            if resp.status_code == 200:
                data = resp.json()
                print(f"\n📤 发送: {message}")
                # values是序列化后的通道值，包含messages数组
                values = data.get("values", {})
                messages = values.get("messages", [])
                last_ai = ""
                for msg in reversed(messages):
                    if msg.get("type") == "ai":
                        last_ai = self._extract_text(msg.get("content", ""))
                        break
                print(f"📥 回复: {last_ai}\n")
                return data
            print(f"❌ 请求失败: {resp.text}")
            return {}

    def get_thread_state(self) -> dict:
        """获取线程状态"""
        if not self.current_thread_id:
            return {}

        resp = self.session.get(f"{self.base_url}/api/threads/{self.current_thread_id}/state")
        if resp.status_code == 200:
            return resp.json()
        print(f"❌ 获取状态失败: {resp.text}")
        return {}

    def get_thread_messages(self, limit: int = 50) -> list:
        """获取线程消息历史"""
        if not self.current_thread_id:
            return []

        resp = self.session.get(f"{self.base_url}/api/threads/{self.current_thread_id}/messages", params={"limit": limit})
        if resp.status_code == 200:
            return resp.json()
        print(f"❌ 获取消息失败: {resp.text}")
        return []

    def run_conversation_test(self):
        """运行会话测试"""
        print("\n" + "=" * 50)
        print("🚀 开始会话能力测试")
        print("=" * 50)

        # 1. 初始化系统
        if not self.initialize_system():
            return

        # 2. 登录
        if not self.login():
            return

        # 3. 创建线程
        if not self.create_thread():
            return

        # 4. 发送多条消息测试多轮对话
        test_messages = ["你好！请介绍一下你的能力", "你能帮我做什么？", "请用一句话总结一下你的主要功能"]

        for msg in test_messages:
            self.send_message(msg)
            time.sleep(1)  # 避免请求过快

        # 5. 获取对话历史
        print("\n" + "=" * 50)
        print("📜 对话历史:")
        print("=" * 50)
        messages = self.get_thread_messages()
        for idx, msg in enumerate(messages[-6:], 1):  # 显示最近6条
            if "content" in msg:
                role = msg.get("type", msg.get("role", "unknown"))
                text = self._extract_text(msg.get("content", ""))
                display = text[:100]
                print(f"{idx}. [{role}] {display}..." if len(text) > 100 else f"{idx}. [{role}] {display}")

        # 6. 获取线程状态
        state = self.get_thread_state()
        if state:
            print(f"\n📊 线程状态: {state.get('status', 'unknown')}")

        print("\n✅ 测试完成!")
        print(f"💡 Thread ID: {self.current_thread_id}")
        print("💡 可以继续对话或使用此ID进行后续操作")


def main():
    client = DeerFlowClient(BASE_URL)
    client.run_conversation_test()


if __name__ == "__main__":
    main()
