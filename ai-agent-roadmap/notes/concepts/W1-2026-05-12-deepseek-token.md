---
title: DeepSeek 流式调用 + Token 计费
type: concept
week: W1
date: 2026-05-12
tags: [llm, deepseek, streaming]
source: []
related: []
status: draft
---

## from __future__ import annotations 干啥用？

作用：是让模块中所有的类型注解（type annotations）默认变成"字符串形式"

应用场景：
1.前向引用（forward reference）：可以直接写 Node，不再需要写成 "Node" 字符串
2.循环导入：仅用于类型注解的 import 可以放进 if TYPE_CHECKING: 块，避免运行时循环依赖
3.新语法兼容旧版本：例如在 Python 3.9 之前，list[int]、dict[str, int]、int | None 这些写法运行时会报错
___

## 为什么用 httpx 而不是 requests？

1.httpx有异步支持，requests没有
2.流式响应支持更好
3.http/2支持
___

## load_dotenv() 怎么找到 .env 文件的？

作用：加载.env文件中的环境变量
1.先检查当前目录下是否有.env文件
2.如果没有，在检查上级目录，直到找到或者到根目录为止
3.如果找到，则加载环境变量；如果没有找到，则抛出FileNotFoundError异常
___

## messages 数组里 role 还有什么取值？

```python
body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "stream_options": {"include_usage": True},
    }
```

1.system：系统指令，定义模型的行为、角色、上下文等
2.user：用户输入
3.assistant：模型的回复
4.tool：工具调用结果
___

## 如果删掉 Content-Type 会怎样？

1.使用httpx的json=body参数时，会自动设置Content-Type为application/json
2.用data=或者content=时，没有Content-Type参数，使用data=，httpx可能会默认为application/x-www-form-urlencoded；而content=，没有默认值，都会导致请求失败（400）
___

## stream_options 这个 key 是 DeepSeek 独有还是 OpenAI 通用

是OpenAI通用，DeepSeek跟着实现的
作用：专为流式拿 usage 设计，因为在流式输出下，每个 chunk 只有增量内容，最后一个 chunk 默认不包含 token 统计，加了这个，流式输出最后一个chunk会包含usage
___

## 为什么是两层 with？

第一层 httpx.Client(timeout=60) —— 管连接池
Client 内部维护到 api.deepseek.com 的 TCP + TLS 连接池
退出 with 时会：
1.关闭所有还在池里的连接
2.释放 socket、DNS 缓存等

第二层 client.stream(...) —— 管这一次响应的流
这是流式 API 的关键
退出第二层 with 时：
1.调 resp.close() —— 把没读完的 body 丢弃
2.把连接归还给第一层那个池子（复用而不是销毁）
___

## raise_for_status() 不调会怎样？

假设你 .env 里的 key 是错的，DeepSeek 返回 401，body 长这样（非 SSE，是普通 JSON）：
```python
{"error": {"message": "Authentication Fails", "code": "invalid_api_key"}}
```

因为错误 body 不是 SSE 格式（没有 data: 前缀），所以会被 continue 跳过，循环很快结束，函数返回空 usage = {}
```python
if not line or not line.startswith("data: "):
    continue
```

程序"成功"了，但你看不到任何输出，根本不知道是 401 还是 prompt 真的让模型啥也没说
```python
[prompt] 用三句话介绍 ReAct Agent。
[stream] 
[usage] {}
```

这就是 raise_for_status() 的价值：让错误立刻、显式地冒出来，而不是被你后面的解析逻辑悄悄吞掉
___

## 为什么 iter_lines 要 skip 空行？

SSE 协议规定每个事件以 \n\n（空行）结尾
```text
data: <payload>\n
\n                        ← 空行表示一个事件结束
data: <payload>\n
\n
```

DeepSeek 实际发回来的字节流大概长这样（用 \n 标出换行）：
```text
data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"你"}}]}\n
\n
data: {"id":"chatcmpl-2","choices":[{"delta":{"content":"好"}}]}\n
\n
data: {"id":"chatcmpl-3","choices":[{"delta":{"content":"！"}}]}\n
\n
data: [DONE]\n
\n
```
___

## line[len("data: "):] 切片得到什么？

去掉 "data: " 前缀（6 个字符：d、a、t、a、:、 ）后剩下的部分——也就是纯 JSON 字符串
```python
line    = 'data: {"choices":[{"delta":{"content":"你"}}]}'
payload = '{"choices":[{"delta":{"content":"你"}}]}'
```
可以使用payload = line.removeprefix("data: ")更佳
___

## [DONE] 为什么要单独判？

因为 [DONE] 不是合法 JSON，json.loads 会抛异常
___

