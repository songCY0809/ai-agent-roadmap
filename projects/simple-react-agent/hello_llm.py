"""W1 Day 1 · DeepSeek 流式 Hello World

用 httpx 直接调 DeepSeek /chat/completions 流式接口。
故意不用 openai SDK，目的是搞清楚 SSE 协议层细节。
"""
from __future__ import annotations

import json
import os
import sys

import httpx
from dotenv import load_dotenv


def stream_chat(prompt: str) -> dict:
    """以流式方式调 DeepSeek，实时打印每个 token，最后返回 usage 字典。"""
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
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    usage: dict = {}
    with httpx.Client(timeout=60) as client:
        with client.stream(
            "POST", f"{base_url}/chat/completions", headers=headers, json=body
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                payload = line.removeprefix("data: ")
                if payload == "[DONE]":
                    break
                chunk = json.loads(payload)
                choices = chunk.get("choices") or []
                if choices:
                    delta = choices[0].get("delta", {}).get("content", "") or ""
                    if delta:
                        print(delta, end="", flush=True)
                if chunk.get("usage"):
                    usage = chunk["usage"]
    print()
    return usage


def main() -> int:
    prompt = sys.argv[1] if len(sys.argv) > 1 else "用三句话介绍 ReAct Agent。"
    print(f"[prompt] {prompt}\n[stream] ", end="", flush=True)
    usage = stream_chat(prompt)
    print(f"\n[usage] {usage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())