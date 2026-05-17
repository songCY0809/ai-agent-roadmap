"""W1 Day 2 · 一次性 tool-calling Agent (无循环)

流程:
  user prompt
    → LLM (带 tools schema)
    → 解析 tool_calls
    → Pydantic 校验
    → 执行 calculator
    → 打印结果
"""
from __future__ import annotations

import json
import os
import sys

import httpx
from dotenv import load_dotenv

from tools import CALCULATOR_TOOL_SCHEMA, CalculatorInput, calculator


def call_with_tools(prompt: str) -> dict:
    """调 DeepSeek, 带上 tools schema, 让它决定要不要用工具。

    注意: 这一版**不开 stream**。Function Calling 流式是 Day 3-4 的事,
    今天先把 tool_calls 拿到手再说。
    """
    load_dotenv()
    api_key = os.environ["DEEPSEEK_API_KEY"]
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [CALCULATOR_TOOL_SCHEMA],
        "tool_choice": "auto",       # 关键: 让 LLM 自主决定
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(
            f"{base_url}/chat/completions", headers=headers, json=body
        )
        resp.raise_for_status()
        return resp.json()


def execute_tool_call(tool_call: dict) -> float:
    """拿到一个 tool_call, 校验参数, 执行函数, 返回结果。"""
    fn_name = tool_call["function"]["name"]
    fn_args_raw = tool_call["function"]["arguments"]   # 注意是 str (JSON)
    fn_args = json.loads(fn_args_raw)

    print(f"[tool_call] {fn_name}({fn_args})")

    if fn_name == "calculator":
        # Pydantic 校验。如果 LLM 给了不合法的 op, 这里抛 ValidationError
        validated = CalculatorInput(**fn_args)
        print(f"[validated] {validated.model_dump()}")
        return calculator(**validated.model_dump())

    raise ValueError(f"未知工具: {fn_name}")


def main() -> int:
    prompt = sys.argv[1] if len(sys.argv) > 1 else "帮我算 23 * 47"
    print(f"[prompt] {prompt}")

    response = call_with_tools(prompt)
    message = response["choices"][0]["message"]

    # finish_reason 告诉你 LLM 为什么停: 'stop' (正常结束) / 'tool_calls' (要调工具) / 'length' (超 max_tokens)
    finish = response["choices"][0].get("finish_reason")
    print(f"[finish_reason] {finish}")

    if message.get("tool_calls"):
        # 关键点: tool_calls 是 list, 可能有多个 (今天先按 1 个处理)
        for tc in message["tool_calls"]:
            result = execute_tool_call(tc)
            print(f"[result] {result}")
    else:
        # LLM 决定不调工具, 直接回答
        print(f"[direct answer] {message.get('content')}")

    print(f"[usage] {response.get('usage')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())