"""W1 Day 2 · 工具定义层

定义一个 calculator 工具，三件事：
1. CalculatorInput: Pydantic 模型，描述参数 + 校验
2. calculator: 真正的 Python 函数（LLM 调不到，是你执行）
3. CALCULATOR_TOOL_SCHEMA: OpenAI Function Calling 格式的 schema，给 LLM 看的
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """计算器工具的输入参数。Pydantic 帮我们做 3 件事:
    1. 字段必填校验 (op/a/b 缺一报错)
    2. 类型校验 (op 必须在 4 个值里, a/b 必须能转 float)
    3. 自动生成 JSON Schema (.model_json_schema())
    """

    op: Literal["add", "sub", "mul", "div"] = Field(
        ..., description="运算符: add=加, sub=减, mul=乘, div=除"
    )
    a: float = Field(..., description="第一个操作数")
    b: float = Field(..., description="第二个操作数")


def calculator(op: str, a: float, b: float) -> float:
    """执行四则运算。注意:
    - 这是真正被你的代码调用的函数，LLM 看不到它的代码
    - 除以 0 抛 ValueError, 让上层决定怎么处理 (Day 4 加 fallback)
    """
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "mul":
        return a * b
    if op == "div":
        #if b == 0:
            #raise ValueError("除数不能为 0")
        #return a / b
        return None
    raise ValueError(f"未知运算符: {op}")


# OpenAI Function Calling 格式的 schema。这就是给 LLM 看的"使用说明书"
# 注意 3 层嵌套: {"type": "function", "function": {"name", "description", "parameters"}}
CALCULATOR_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "执行加减乘除四则运算。当用户问数学题时调用此工具。",
        "parameters": CalculatorInput.model_json_schema(),
    },
}


if __name__ == "__main__":
    # 自测 1: 看 schema 是不是符合 OpenAI 格式
    import json

    print("=== Tool Schema ===")
    print(json.dumps(CALCULATOR_TOOL_SCHEMA, ensure_ascii=False, indent=2))

    # 自测 2: Pydantic 校验对的输入
    print("\n=== Pydantic 正例 ===")
    ok = CalculatorInput(op="mul", a=23, b=47)
    print(ok.model_dump())

    # 自测 3: Pydantic 校验错的输入
    print("\n=== Pydantic 反例 ===")
    try:
        bad = CalculatorInput(op="pow", a=2, b=3)
    except Exception as e:
        print(f"{type(e).__name__}: {e}")

    # 自测 4: 真的算一遍
    print("\n=== 真实运算 ===")
    print(calculator("mul", 23, 47))
    print(calculator("div", 10, 3))
