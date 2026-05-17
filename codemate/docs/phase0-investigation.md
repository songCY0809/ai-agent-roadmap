# Phase 0 调研 · CodeMate 三大参考项目分析与可行性结论

> **本文档目的**：W4 第 1-2 天 Phase 0 调研产出。回答 3 个问题：
> 1. 三个开源参考项目能给 CodeMate 提供什么具体借鉴？
> 2. CodeMate 在 9 周内交付的可行性如何？风险点在哪？
> 3. 项目骨架长什么样，模块怎么划分？
>
> **生成时间**：2026-05-11 ｜ **作者**：CodeMate 作者本人 + AI 调研助手 ｜ **配套学习路线**：[AI-Agent-学习路线 v1.1](../../ai-agent-roadmap/AI-Agent-学习路线.md)

---

## 1. 三大参考项目快照

| 项目 | 语言/规模 | 角色 | 借鉴密度 |
|---|---|---|---|
| [khoj-ai/khoj](https://github.com/khoj-ai/khoj) | Python 3.10-3.12 · ~34.6k 行 `src/khoj/` | 产品级"第二大脑"范本 | **概念高 / 代码低**（栈差异大） |
| [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm) | JS/Node · ~148k 行（collector+server+frontend） | 架构与 loader 注册表参考 | **架构高 / 代码低**（语言不同） |
| [SPerekrestova/interactive-leetcode-mcp](https://github.com/SPerekrestova/interactive-leetcode-mcp) | TypeScript · ~6.9k 行 | MCP server + LeetCode 通信 | **代码高**（GraphQL/Submit 逻辑可移植）|

**结论一句话**：3 个项目里**最值钱的代码片段在 leetcode-mcp**（LC GraphQL + Submit/Cookie 逻辑），其余两个主要提供**架构思想**。

---

## 2. Khoj 深度分析：RAG pipeline 与对话历史的标杆

### 2.1 技术栈对照

| 维度 | Khoj | CodeMate（建议） | 决策 |
|---|---|---|---|
| ORM / DB | Django + PostgreSQL + pgvector | SQLite（元数据） + Milvus（向量） | **不照搬**：Django 学习成本太高 |
| Web 框架 | FastAPI + Django ASGI 嵌套 | 纯 FastAPI | **不照搬**：单一框架够用 |
| Embedding | sentence-transformers + CrossEncoder | sentence-transformers + bge-m3 | **借接口形态** |
| LLM Provider | OpenAI/Anthropic/Google 多路 | DeepSeek + 本地 Qwen 双轨 | **借抽象接口** |
| 多端 | Web/Obsidian/Desktop/Mobile/Telegram | CLI + Streamlit | **跳过所有多端** |

### 2.2 RAG 全链路（CodeMate 功能 A 的对照表）

| 阶段 | Khoj 关键文件 | CodeMate 决策 |
|---|---|---|
| **Loader 调度** | `src/khoj/routers/helpers.py:configure_content` | **简化**：保留"类型→处理器"分发即可 |
| **Chunking** | `src/khoj/processor/content/text_to_entries.py:split_entries_by_max_tokens` 用 `RecursiveCharacterTextSplitter` | **借概念**：分层 chunk（标题→递归 splitter），参数换成 tiktoken/字符计数对齐 bge-m3 |
| **Embedding** | `src/khoj/processor/embeddings.py:EmbeddingsModel` 本地/API 分叉 + 批量 | **借接口形态**，实现换 bge-m3 |
| **向量存储** | `Entry.VectorField` + Django ORM | **不重做**：直接用 Milvus Python SDK |
| **查询重写** | `routers/helpers.py:extract_questions` 每条用户消息 LLM 改写出多条 query | **W5 再做**：MVP 阶段先用原句 |
| **检索** | `EntryAdapters.search_with_embeddings` 余弦距离 + filter | **借"filter + 向量"思路** |
| **Rerank** | `text_search.py:rerank_and_sort_results` 用 CrossEncoder | **W5 应做**：先 top-k，rerank 作为升级项 |
| **引用** | `prompts.py` 强制 inline markdown 引用 + `compiled_references` 注入 | **直接借鉴**：性价比极高 |
| **Citation 存储** | `save_to_conversation_log` 把 refs 存 assistant 消息的 `context` | **直接借鉴**：SQLite JSON 列存 |

### 2.3 对话历史与上下文截断

- **持久化**：Khoj 用 `Conversation` 模型 + `conversation_log` JSONField，每条消息 `ChatMessageModel` 校验
- **截断策略**：发往模型前 `truncate_messages`——丢最旧消息块，再必要时截断当前条
- **模型预算**：`model_to_prompt_size` 按模型名给 token 预算

**CodeMate W6 SQLite 抄作业**：JSON 聊天表 + 每次 append + 构建 ChatML 前 truncate。**不要搬** Django + UserMemory + `ai_update_memories` 长期记忆子系统（太重）。

### 2.4 Khoj 里 Over-engineered 不能搬的部分

- ❌ Django + FastAPI 双栈、ASGI 嵌套、collectstatic
- ❌ 多租户用户体系（KhojUser、邮箱/手机验证、Google OAuth）
- ❌ Billing / Stripe / Twilio / Resend
- ❌ Agent / Research / Operator / E2B 代码执行整条工具链
- ❌ 遥测、限流、APScheduler 自动化
- ❌ Whisper、图像生成、多 embedding 后端 fallback

### 2.5 Khoj 借鉴 Top 5（按性价比）

1. **`text_to_entries.py`** — `split_entries_by_max_tokens` + `update_embeddings`（哈希增量 / 删除对齐 / 批量写入）—— 索引管线骨架
2. **`markdown_to_entries.py`** — 按标题递归 + `#line=` 引用粒度 —— Demo 演示加分项
3. **`embeddings.py`** — EmbeddingsModel 本地/远端分叉 —— 双轨切换的接口范式
4. **`routers/helpers.py` 中的 `search_documents` / `execute_search`** —— 多 query + filter + rerank 的产品套路
5. **`conversation/utils.py:truncate_messages` + `prompts.py`** —— 上下文窗口管理 + 强制引用 prompt

### 2.6 Khoj 陷阱 Top 5

1. **"Hybrid retrieval" 实际不是 BM25 + 向量融合**——Khoj 的"混合"是向量主检索 + icontains filter + cross-encoder；CodeMate 要真正做 BM25 + 稠密混合，需自己实现稀疏通道（Milvus BM25 Sparse 或独立 BM25 索引）
2. **照搬栈 = 死路**——Django ORM + pgvector + 双 ASGI 学习曲线远大于 LangGraph + Milvus
3. **`extract_questions` 每次都打一次 LLM**——延迟、成本、JSON failover 都拖 MVP，先关掉
4. **sentence-transformers + torch 2.6 锁版本**——对 RTX 4060 8G 显存是硬约束，bge-m3 本地跑前要先核实显存占用
5. **会话 JSON 无限增长**——磁盘上的 `conversation_log` 会变大，CodeMate 要做按会话归档或保留最近 N 条

---

## 3. AnythingLLM 深度分析：文档导入 pipeline 与 MCP 桥接

### 3.1 架构亮点

- **collector / server / frontend 三段拆分**：collector 是文档摄入微服务（hotdir 上传 → MIME 路由 → 标准化文档 JSON → 写 server 的 `storage/documents`）。CodeMate **不必拆**，单 FastAPI + worker 够用。
- **向量库通过 `getVectorDbClass()` 抽象**：支持 LanceDB/Chroma/Milvus/Qdrant 等 9 种后端。CodeMate **借接口思想，硬编码 Milvus**。
- **Workspace 模型 = 向量 namespace**：`workspaces` 表 + `workspace.slug` 作为 vector namespace。**这个概念直接抄成 CodeMate 的"笔记本/课程包"**。

### 3.2 Loader Registry（最值得抄的设计）

**模式**：`collector/utils/constants.js:SUPPORTED_FILETYPE_CONVERTERS` 是 extension → converter 文件路径的映射；`processSingleFile/index.js` 按扩展名 require() 对应文件，未知扩展回退当 `.txt` 处理。

CodeMate 在 Python 里的对应：

```python
LOADER_REGISTRY: dict[str, type[Loader]] = {
    ".md": MarkdownLoader,
    ".markdown": MarkdownLoader,
    ".docx": DocxLoader,
    ".txt": TextLoader,
    # W4 末再加 PDF / 语雀
}
```

**各文件类型处理速查**（AnythingLLM 已实现的，CodeMate 选择性 mirror）：

| 类型 | AnythingLLM 文件 | CodeMate 决策 |
|---|---|---|
| `.md/.txt` | `convert/asTxt.js` | ✅ 必做（核心场景） |
| `.docx` | `convert/asDocx.js`（LangChain `DocxLoader`）| ✅ 必做 |
| `.pdf` | `convert/asPDF/index.js`（LangChain PDF + OCR fallback）| ⚠️ W4 后再加，**注意：AnythingLLM 把 PDF 各页 flatten 成单字符串，丢失页号 → CodeMate 要保留 page 在 chunk metadata** |
| `.pptx/.odt` | `convert/asOfficeMime.js` | ❌ 跳过（场景外） |
| `.xlsx` | `convert/asXlsx.js` | ❌ 跳过 |
| Audio/Image | Whisper / OCR | ❌ 跳过 |
| URL / YouTube | `processLink/...` | ❌ 跳过 |
| 语雀 | **无** | ✏️ 自写 |

### 3.3 文档标准化 schema（抄）

AnythingLLM 所有 loader 输出统一 schema：`{ id, title, chunkSource, pageContent, published, ...metadata }`。CodeMate 应有相同的：

```python
@dataclass
class DocumentRecord:
    doc_id: str        # 稳定 ID（用于增量/删除对齐）
    title: str
    chunk_source: str  # "file:///...", "yuque://...", "https://..."
    page_content: str
    metadata: dict     # page, line, section, published, ...
```

### 3.4 Chunking + 元数据注入

- AnythingLLM 在 server 侧统一 chunking（`TextSplitter` = LangChain `RecursiveCharacterTextSplitter`），可配置 chunk size / overlap，**有 `buildHeaderMeta` 在每个 chunk 前注入 `<document_metadata>title/published/source</document_metadata>` 包装**
- 但这个 header 注入**只认 `link://` 和 `youtube://` 前缀**——`file://` / 语雀都不会被注入
- **CodeMate 抄这个 header 注入模式，但自己定义 prefix 规则**：file/markdown/yuque/docx 全都注入 metadata header

### 3.5 MCP 处理（W5 重点参考）

- **AnythingLLM 只做 MCP Client（消费别人的 server），不做 MCP Server**——`server/utils/MCP/hypervisor/` 用 `@modelcontextprotocol/sdk` 的 Client + stdio/HTTP/SSE 传输
- 把 MCP `listTools` 结果转成内部 `Aibitat` 函数（`convertServerToolsToPlugins`）
- **CodeMate 反过来——既写 MCP Server（暴露 LeetCode 工具给 Cursor），也在 LangGraph 里调 MCP Client（消费自己的 server）**

### 3.6 AnythingLLM Over-engineered 部分

- ❌ 多用户 / SSO / Roles / API Keys 表面
- ❌ Telegram bot / 浏览器插件 / embed widget
- ❌ Aibitat agent marketplace / community hub
- ❌ 多 vector backend / 几十个 LLM provider 适配器
- ❌ collector hotdir + signed extension API + Puppeteer
- ❌ document_vectors 缓存重放（增量同步太复杂）

### 3.7 AnythingLLM 借鉴 Top 5

1. **`collector/utils/constants.js` + `processSingleFile/index.js`** → Python `LOADER_REGISTRY` + 共享 `DocumentRecord`
2. **`collector/processRawText/index.js` + `writeToServerDocuments`** → 标准 schema 在 chunk/embed 前确定
3. **`server/utils/TextSplitter/index.js:buildHeaderMeta`** → metadata 头部注入 + max tokens cap
4. **`server/utils/helpers/index.js:getVectorDbClass` + `vectorDbProviders/base.js`** → 薄 `VectorStore` 协议（CodeMate 只实现 Milvus + Chroma 两个）
5. **`server/utils/MCP/index.js:convertServerToolsToPlugins`** → MCP `inputSchema` → LangGraph `StructuredTool` 的桥接模式

### 3.8 AnythingLLM 陷阱 Top 5

1. **PDF 各页 flatten 丢页号**——CodeMate 要在 chunk metadata 里保留 `page` 字段
2. **"Hybrid retrieval" 实际是 vector + 可选 rerank 重排序**——不是 BM25 + 向量融合；CodeMate 真正混合检索是自己的设计
3. **MCP client 子进程/env 在学生机上脆弱**（npx、PATH、Docker）——CodeMate 的 MCP server 应优先 stdio + 明确超时
4. **`chunkSource` URL header 只认 link/youtube**——文件/语雀需要自定义 prefix
5. **collector + server 双进程**——CodeMate 单 FastAPI 进程更轻

---

## 4. interactive-leetcode-mcp 深度分析：MCP server 起步代码

### 4.1 项目结构（精简 ~6.9k 行 TS）

```
src/
├── index.ts                # MCP server 启动入口（stdio transport）
├── common/                 # RegistryBase 等共享抽象
├── leetcode/
│   ├── graphql/            # ★ LeetCode GraphQL 查询字符串（直接可移植）
│   ├── leetcode-service-interface.ts
│   └── leetcode-global-service.ts  # ★ submit/cookie/getQuestionId/validateCredentials
├── mcp/
│   ├── tools/              # 工具注册（get_problem, search_problems, submit_solution 等）
│   ├── prompts/            # 学习/认证类 prompts
│   └── resources/          # categories://problems/all, problem://{slug} 等
├── types/                  # Zod schemas
└── utils/
    └── credentials.ts      # ~/.leetcode-mcp/credentials.json 凭据持久化
```

### 4.2 MCP 工具注册模式（CodeMate 抄）

```typescript
this.server.registerTool(
    "get_problem",
    {
        description: "Retrieves details about a specific LeetCode problem...",
        inputSchema: {
            titleSlug: z.string().describe("The URL slug...")
        }
    },
    async ({ titleSlug }) => {
        // 调用 service
        // try/catch → 返回 { content: [{ type: "text", text: JSON.stringify(...) }] }
    }
);
```

**CodeMate Python 等价**（用 MCP Python SDK + Pydantic）：

```python
@server.tool()
async def get_problem(title_slug: str) -> dict:
    """Retrieves details about a specific LeetCode problem..."""
    try:
        data = await leetcode_service.fetch_problem_simplified(title_slug)
        return {"content": [{"type": "text", "text": json.dumps(data)}]}
    except LeetCodeError as e:
        return {"content": [{"type": "text", "text": json.dumps({"error": str(e)})}]}
```

### 4.3 LeetCode API 通信关键点（**最有价值的可移植代码**）

| 操作 | 走哪个 API | 认证 | 难点 |
|---|---|---|---|
| 读取题目 | GraphQL `https://leetcode.com/graphql` | 无需登录 | 字段 drift（`similarQuestions` 易解析失败）|
| 搜索题目 | GraphQL（tags/difficulty/keywords）| 无需登录 | — |
| 用户进度 / 提交记录 | GraphQL | **必须登录** | `LEETCODE_SESSION` + `csrftoken` cookie |
| 提交代码 | `POST /problems/{slug}/submit/` | **必须登录** | 需要 `X-CSRFToken` header + 题目 `questionId`（≠ frontend id）|
| 轮询结果 | `GET /submissions/detail/{id}/check/` | 登录 | 间隔 1s、最多 30 次（~30s 上限） |

### 4.4 关键决策：TypeScript fork vs Python 重写

**强烈推荐 Path B：Python 重写 MCP server**，理由：

| 维度 | Path A (fork TS) | **Path B (Python 重写)** ✅ |
|---|---|---|
| 工具链 | 需学 TS + npm（你完全没碰过）| 用 W1-W3 学的 Python |
| 与 LangGraph 集成 | 跨进程调 MCP（多一层）| 同进程直接调，或本地 MCP |
| 简历叙述 | "复用别人的 MCP server" | **"我写了 MCP server"** |
| LeetCode 通信 | `leetcode-query` npm 包帮你做了一半 | 需自己实现，**但 GraphQL 查询和 submit 逻辑可逐字搬过来** |
| MCP 协议本身 | 5%的工作量 | 5% 的工作量（Python SDK 一样简单）|

**实施策略**：把 `src/leetcode/graphql/*.ts` 当作"权威 GraphQL 查询字典"用，把 `leetcode-global-service.ts` 当作"submit 流程参考实现"，这两个文件值得**逐行对照**。

### 4.5 leetcode-mcp 借鉴 Top 5

1. **`src/leetcode/graphql/*.ts`** — drop-in GraphQL 查询字符串，直接 copy 进 Python `httpx` 请求体
2. **`src/leetcode/leetcode-global-service.ts`** — `submitSolution` / `getQuestionId` / `validateCredentials` / `LANGUAGE_MAP` 的实现细节
3. **`src/utils/credentials.ts` + `types/credentials.ts`** — 凭据存储路径、权限、字段
4. **`tests/helpers/test-client.ts`** — 内存传输（InMemoryTransport.createLinkedPair）测试思路
5. **`skills/interactive-leetcode-mcp/SKILL.md`** — 产品化 agent 指令（认证流程、错误提示话术）

### 4.6 leetcode-mcp 陷阱 Top 3

1. **CSRF + Cookie 同时需要**——submit 必须带 `LEETCODE_SESSION` cookie + `X-CSRFToken` header；401 = 重新登录
2. **slug vs questionId vs frontend id 三者别混**——submit 用 `questionId`，public 工具用 slug，需要 `getQuestionId` 中间查询
3. **MCP capabilities 必须 connect 前注册**——违反会出"missing capability"诡异错误

---

## 5. CodeMate 可行性总评

### 5.1 GO / NO-GO 结论

**✅ GO**——按现有 9 周路线交付 v1.0 是**可行的**，前提是严格遵守 MVP 分级。

**主要论据**：
- 三个参考项目的核心模块在 CodeMate 里都有"瘦身版"，没有要从 0 攻关的子问题
- Khoj 工业级实现存在 → 证明 RAG 全链路在 Python + Milvus 上**可行**
- AnythingLLM 的 loader 注册模式 → CodeMate 的 W4 数据导入有**蓝图可抄**
- leetcode-mcp 已给出 LeetCode GraphQL/Submit 实现 → CodeMate W5 算法陪练**不用从 0 摸 LC API**

### 5.2 工时核算

| 阶段 | 路线图工时 | 实际复杂度评估 | 风险 |
|---|---|---|---|
| W1-W3 简单项目 | 78h | 与原估一致 | 低 |
| **W4 RAG 基础** | 26h | **可能略紧**（要写 3 个 loader + chunker + 跑通 RAG）| 中 |
| **W5 Agentic RAG + MCP** | 26h | **关键周**（Milvus 替换 + 混合检索 + MCP server 起步）| **中高** |
| **W6 CodeMate 核心** | 26h | 期末前必赢周，按 MVP 砍 D 是必然的 | 高 |
| W7-W8 工程化（跨期末）| 22+18h | 节奏舒缓 | 低 |
| W9 简历交付 | 30h | 期末后状态回升 | 低 |

**结论**：W5 是被低估的一周——既要 Milvus + 混合检索 + 查询重写，又要写 MCP server。建议 **W5 末做一次明确"砍一刀"决策**，避免堆 W6。

### 5.3 风险矩阵（基于路线图 §7.4 + 调研新发现）

| 风险 | 严重度 | 概率 | 调研新增证据 | 缓解 |
|---|---|---|---|---|
| W6 4 个功能做不完 | 高 | 高 | Khoj 4 个功能花了几年 | 严格 MVP 分级：MUST=A+B，砍 D，C 推到 W9 |
| 真正的 BM25+稠密混合检索难度 | 中 | 中 | **Khoj 和 AnythingLLM 都没做真正混合检索**，无现成代码可参考 | W5 退路：先纯稠密 + Reranker；混合作为升级项 |
| LeetCode API 反爬 / Cookie 失效 | 中 | 中 | leetcode-mcp 没做 rate-limit 处理 | 加 `httpx` retry + 显式 401 处理 + mock 模式 |
| LeetCode `questionId` resolve 出错 | 中 | 高（如果不知道）| leetcode-mcp 明确警告 slug vs questionId 问题 | 严格按 `getQuestionId` 移植 |
| 期末影响 W7+W8 工程化 | 中 | 已知 | — | 路线图已规划降速到 18-22h，无新风险 |
| Milvus Docker 翻车 | 中 | 中 | AnythingLLM 文档表明 Milvus 是支持但默认 LanceDB | **退路：Chroma**（已在 W4 用过，无缝退化）|
| bge-m3 + RTX 4060 8G 显存不够 | 中 | 低 | Khoj sentence-transformers + torch 2.6 锁版本，提示资源敏感 | W4 第 1 天先压测显存；不够就走 OpenAI embedding API |
| 引用质量差（PDF 页号丢失等）| 中 | 中 | AnythingLLM PDF flatten 丢页号 | chunk metadata 强制保留 page/line |
| 写自己的 MCP server 时间超期 | 低 | 中 | leetcode-mcp 起步代码可以直接抄 | W5 第 1 天先 hello world MCP，逐步加工具 |

### 5.4 与路线图 §7.4.1 风险表的对照

路线图原本识别了 5 类风险，**全部仍然成立**，调研新增 4 类（混合检索难度 / LeetCode questionId / 引用质量 / MCP server 超期）。**总体风险曲线没有恶化**，反而因为有了参考代码，**W5 的实施风险下降**。

---

## 6. 给路线图的微调建议（基于调研发现）

> 这些是新发现，建议同步反映到 `AI-Agent-学习路线.md`：

| 建议 | 落到哪一节 | 优先级 |
|---|---|---|
| W4 任务里明确"chunk metadata 必须保留 page/section/line" | §3.2 W4 | 高 |
| W5 把"真正 BM25+稠密混合"标为应做，纯稠密+Reranker 标为必做 | §3.2 W5 | 高 |
| W5 任务里加"先 hello-world MCP server 再加工具" | §3.2 W5 | 中 |
| 简历致谢段明确：Khoj（架构）+ AnythingLLM（loader registry）+ leetcode-mcp（LC GraphQL/Submit 移植）| §10.1 / §7.7 | 高 |
| 在 `references/` 加 `.gitignore` 注释每个项目的"借鉴点 → CodeMate 文件"对应表 | 单独的 references/README.md | 中 |

---

## 7. CodeMate 项目骨架（详见 src/ 实际目录）

详见仓库根 `README.md` 与 `docs/architecture.md`。本节只列模块语义：

### 7.1 模块划分（11 个）

```
src/codemate/
├── settings.py         # pydantic-settings 读 .env
├── llm/                # LLM 客户端抽象（DeepSeek / 本地 llama.cpp）
├── loaders/            # 文档加载器（markdown/docx/yuque），借鉴 AnythingLLM 注册表
├── chunkers/           # 分块（fixed/sentence），借鉴 Khoj RecursiveSplitter
├── embeddings/         # bge-m3 客户端
├── retrieval/          # vector store + BM25 + hybrid + reranker
├── graph/              # LangGraph 状态图（6 节点）
├── tools/              # 工具实现（leetcode/code_review/local_repo）
├── mcp_server/         # CodeMate 自己的 MCP server（W5 写）
├── features/           # 高层功能编排（A/B/C/D）
├── persistence/        # SQLite 持久化（对话历史 / 算法掌握度）
├── api/                # FastAPI app + SSE 路由（W6）
├── cli/                # `codemate ask "..."` CLI（W6）
└── ui/                 # Streamlit Web UI（W9）
```

### 7.2 周次 → 模块覆盖映射

| 周 | 完成模块 | 累计完成度 |
|---|---|---|
| W4 | `loaders/` + `chunkers/` + `embeddings/` + `retrieval/vector_store.py`(Chroma) + `features/rag_qa.py` 极简版 | 30% |
| W5 | `retrieval/`(Milvus + BM25 + hybrid + reranker) + `tools/leetcode.py` + `mcp_server/` | 55% |
| W6 | `graph/` + `features/algo_coach.py` + `persistence/` + `api/` 骨架 + `cli/` | **75% （v0.1 MVP 达成线）** |
| W7-W8 | `docker-compose.yml`（Milvus+Redis+Langfuse）+ Langfuse 埋点 + Ragas 评估 + README | 90% |
| W9 | `ui/`(Streamlit) + C++ MCP server 拓展 + 简历 STAR + 博客 | **100% （v1.0）** |

### 7.3 借鉴溯源矩阵

| CodeMate 文件 | 借鉴来源 | 借鉴具体 |
|---|---|---|
| `loaders/__init__.py` | AnythingLLM `collector/utils/constants.js` | LOADER_REGISTRY 模式 |
| `loaders/base.py` | AnythingLLM `processRawText/index.js` | DocumentRecord 标准 schema |
| `loaders/markdown.py` | Khoj `markdown_to_entries.py` | 按标题递归 + `#line=` 引用 |
| `loaders/docx.py` | Khoj `docx_to_entries.py` + AnythingLLM `asDocx.js` | python-docx 解析 |
| `chunkers/recursive.py` | Khoj `text_to_entries.py:split_entries_by_max_tokens` + AnythingLLM `TextSplitter:buildHeaderMeta` | RecursiveSplitter + metadata header 注入 |
| `embeddings/bge_m3.py` | Khoj `embeddings.py:EmbeddingsModel` | 本地/远端分叉、批量请求接口形态 |
| `retrieval/vector_store.py` | AnythingLLM `vectorDbProviders/base.js` | 薄抽象，只实现 Chroma + Milvus |
| `retrieval/hybrid.py` | （都没现成）—— **CodeMate 原创** | BM25 + 稠密融合（rerank 用 cross-encoder）|
| `graph/builder.py` | LangGraph 官方 Tutorial | 6 节点状态图 |
| `mcp_server/server.py` | leetcode-mcp `src/index.ts` | StdioServerTransport + register* 模式 |
| `tools/leetcode.py` | leetcode-mcp `src/leetcode/graphql/*.ts` + `leetcode-global-service.ts` | **GraphQL 查询和 Submit/Cookie 逻辑直接移植** |
| `persistence/conversation.py` | Khoj `conversation/utils.py:truncate_messages` + `save_to_conversation_log` | JSON 聊天表 + 前向截断 |
| `features/rag_qa.py` 中的 prompt | Khoj `prompts.py` | 强制 inline markdown 引用 |

---

## 8. 行动清单（Phase 0 收官，今天/明天做）

- [x] 三大开源项目阅读（已经完成）
- [x] 写本调研文档（`docs/phase0-investigation.md`）
- [ ] 初始化 `codemate/` 仓库：`pyproject.toml`、`README.md`、`.gitignore`、`docker-compose.yml` 占位
- [ ] 在 `references/` 加 README，标注每个项目的"借鉴点 → CodeMate 文件"
- [ ] 把"语雀 API 验证"列为 W4 风险点：先调通 `https://www.yuque.com/api/v2/...`
- [ ] 把"bge-m3 + RTX 4060 显存压测"列为 W4 第 1 天必做
- [ ] 把本文档中第 6 节"路线图微调建议"反映到 `AI-Agent-学习路线.md`（可选，看时间）

### 8.1 知识库数据源清单（W4 ingestion 默认配置）

W4 实现 `MarkdownLoader` 时，默认接入以下来源（按优先级排序）：

| 优先级 | 路径 | 内容 | 数据量预估 |
|---|---|---|---|
| P0 | `../ai-agent-roadmap/notes/concepts/` | 用户自写概念卡片 | W1-W9 累计 40-60 张，约 5-10 万字 |
| P0 | `../ai-agent-roadmap/notes/crashes/` | 用户自写翻车记录 | W1-W9 累计 10-20 篇，约 1-3 万字 |
| P0 | `../ai-agent-roadmap/notes/weekly/` | 用户自写周总结 | 9 篇，约 1-2 万字 |
| P1 | `./papers/` | PDF 论文（W4 后期加） | 10-20 篇 ReAct/RAG/MCP 经典论文 |
| P1 | `./yuque/` | 语雀文档（W5 风险点） | 看 API 调通后决定 |
| P2 | `./web-clips/` | 网页剪藏（W6 后） | 可选 |

P0 三个目录 **从今天（2026-05-12）开始持续填充**，每天都是 RAG 训练数据，到 W4 启动时已经积累 2-3 周的真实笔记可以直接 ingest，不用临时找 demo 数据。

笔记规范、frontmatter spec、命名约定见 [`../../ai-agent-roadmap/notes/README.md`](../../ai-agent-roadmap/notes/README.md)。一键建笔记 CLI 见 [`../../tools/new-note.py`](../../tools/new-note.py)。

**与"原创亮点"的关联**：架构 §3.4 真正混合检索是检索算法层的原创，**学习笔记知识库则是数据层的原创**——简历可写"自建 9 周 / 50+ 张概念卡片的学习笔记知识库，frontmatter 多字段过滤支持时间 / 类型 / 标签 / 掌握度维度检索"。

---

**总判词**：CodeMate **9 周内可交付 v1.0**。三大参考项目里，**最值钱的是 leetcode-mcp 的 LeetCode 通信逻辑**（直接移植），**最值钱的概念是 AnythingLLM 的 loader registry**（架构抄），**最值钱的产品反面教材是 Khoj**（知道哪些坑不要踩）。

---

## 9. 实施路径决策对比（W4 启动前必做）

> **本节追加时间**：2026-05-12（Phase 0 收官精修）
> **配套阅读**：[architecture.md §3](architecture.md) 关键设计决策 / [reference/README.md](../../reference/README.md) 参考项目本地副本

§1-§8 是 3 个参考项目的深度分析，本节回答"基于这些分析，CodeMate 实际怎么动手做"。三条路径并列呈现，**默认推荐路径 B**，但保留所有路径的可执行细节，留作 W4-W5 期间触发改选时的备案。

### 9.1 三路径速览

| 路径 | 底座 | 加什么 | 估算手写 LOC | 9 周可行性 | 简历强度 | 关键风险 |
|---|---|---|---|---|---|---|
| **A · fork kotaemon** | [Cinnamon/kotaemon](https://github.com/Cinnamon/kotaemon)（~150 Python 文件，BSD-3） | MCP server + LeetCode 工具 + 算法掌握度 + LangGraph 替换 ktem reasoning（可选） | ~800-1200 | 70-95%（视砍量） | 2★（"扩展 kotaemon"叙述偏弱） | 上游接口变更 / §3.4 原创亮点削弱 |
| **B · 库组合从 0 写**（默认） | 无固定底座，`langgraph` + `mcp` Python SDK + `pymilvus` + `FlagEmbedding` 等成熟库为地基 | 全部 11 个模块（按 [architecture.md §7.1](architecture.md)），每个模块都有库做地基 | ~3000 | 50-85%（视 Tier） | 5★（"从 0 实现 Agentic RAG + MCP"） | W6 翻车 / 进度溢出 |
| **C · LangGraph 模板拼接** | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) `examples/rag/agentic_rag/` 或 `langchain-cli` 的 `retrieval-agent` 模板 | 在模板上加 MCP / LeetCode / 算法掌握度 / 混合检索 RRF | ~1800-2200 | 60-90% | 3.5★（"基于模板搭建" 叙述居中） | 模板风格被新版本破坏 |

**核心结论**：

- B = 当前 architecture.md 设计；学习深度和简历强度最高，时间风险也最高
- A = "买现成的房子再装修"；时间最稳，但失去 §3.4 原创混合检索的简历亮点
- C = "买毛坯房自装修"；时间居中，简历强度居中

### 9.2 路径 A · fork kotaemon

#### 9.2.1 候选底座对比

为什么是 kotaemon，不是其它项目：

| 候选 | 语言 | 规模 | 真混合检索 | Agent | MCP | UI | License | 适合 fork？ |
|---|---|---|---|---|---|---|---|---|
| [Cinnamon/kotaemon](https://github.com/Cinnamon/kotaemon) | Python | 中（~150 文件） | 是 | 部分（ktem reasoning） | 否 | Gradio | BSD-3 | **唯一可行** |
| [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | Python+TS | 巨大（数十万行） | 是 | 是（LangGraph） | 否 | React | MIT | 否，太大学不完 |
| [khoj-ai/khoj](https://github.com/khoj-ai/khoj) | Python | 大 | 否（向量+filter） | 部分 | 否 | 多端 | AGPL | 否，Django+FastAPI 双栈 |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | Python | 大 | 是 | 部分 | 否 | React | Apache 2.0 | 否，产品化偏离 Agent 形态 |
| [weaviate/Verba](https://github.com/weaviate/Verba) | Python+TS | 中 | 部分 | 否 | 否 | React | BSD-3 | 否，强依赖 Weaviate |

#### 9.2.2 fork 后需新增的 4 个模块

1. **MCP server**（必做）：kotaemon 完全没有 MCP，需要从 0 用 `mcp` Python SDK 暴露 LeetCode + Code Review 工具
2. **LeetCode 工具**（必做）：移植 leetcode-mcp 的 GraphQL；放进 kotaemon 的 plugin 体系
3. **算法掌握度持久化**（必做）：SQLite + py-fsrs；kotaemon 没有此类模型
4. **LangGraph 替换 ktem reasoning**（可选）：如果保留 ktem 自带 reasoning，简历不能写 "LangGraph 6 节点状态图"；如果替换，工作量 ~300-500 行

#### 9.2.3 与 architecture.md §3.4 的冲突

[architecture.md](architecture.md) §3.4 把"真正 BM25 + 稠密 + RRF + Cross-Encoder"标为**原创亮点**。但 kotaemon `ktem/index/file/pipelines.py` 自带 hybrid pipeline。fork 后该卖点立不住——只能改写为"在 kotaemon 基础上**调优** Reranker 阈值"，简历强度从 5★ 跌到 3★。

#### 9.2.4 简历话术对比

| 维度 | 路径 A | 路径 B |
|---|---|---|
| 主语动词 | "扩展" / "替换" / "新增" | "实现" / "自研" / "移植" / "设计" |
| 例句 | "基于 kotaemon 扩展，新增 MCP server 暴露 LeetCode 工具" | "从 0 实现 Agentic RAG 系统：自研 LangGraph 6 节点状态图..." |
| 面试官追问 | "kotaemon 原本的混合检索怎么实现？" → 容易答崩 | "为什么用 RRF 而不是加权平均？" → 你写的你都知道 |

### 9.3 路径 B · 多项目参考 + 库组合（**默认推荐**）

#### 9.3.1 核心理念

不是"从 0 造每个轮子"，而是"用成熟库当地基，只写差异化胶水"。手写量从想象中的 10k+ 行压缩到约 3k 行。

#### 9.3.2 逐模块库选型表

对照 [architecture.md §7.1](architecture.md) 的 11 个包：

| CodeMate 包 | 核心依赖库 | 自写 LOC | 参考项目 |
|---|---|---|---|
| `settings/` | `pydantic-settings` | ~50 | — |
| `llm/` | `httpx` + 自写 `LLMClient` Protocol | ~200 | Khoj `embeddings.py` 的双轨范式 |
| `loaders/` | `unstructured` + `python-docx` + 自写 `yuque.py` | ~300 | AnythingLLM LOADER_REGISTRY |
| `chunkers/` | `langchain-text-splitters` | ~150 | Khoj `text_to_entries.py` |
| `embeddings/` | `FlagEmbedding`（bge-m3 + bge-reranker 官方） | ~80 | Khoj `embeddings.py` |
| `retrieval/` | `pymilvus` + `rank_bm25` + 自写 RRF（~50）+ `FlagEmbedding` reranker | ~400 | **onyx `backend/onyx/context/search/postprocessing/`** |
| `graph/` | `langgraph` | ~250 | **langchain-ai/open_deep_research** |
| `tools/leetcode.py` | `httpx` + 移植 leetcode-mcp GraphQL 字符串 | ~500 | leetcode-mcp `src/leetcode/` |
| `mcp_server/` | `mcp` 官方 Python SDK | ~200 | **modelcontextprotocol/python-sdk examples** |
| `features/` | 业务编排，纯胶水 | ~400 | — |
| `persistence/` | `sqlalchemy` + `py-fsrs` | ~200 | Khoj `conversation/utils.py` |
| `api/` | `fastapi` + `sse-starlette` | ~250 | — |
| `cli/` + `ui/` | `typer` + `streamlit` | ~300 | — |
| **合计** | — | **~3080** | — |

**关键发现**：差异化卖点（RRF / MCP / LeetCode）的手写部分只有 ~750 行，剩余 2.3k 行是常规工程胶水。

#### 9.3.3 工时表修订（对 §5.2 的更新）

原 §5.2 W4-W6 各 26h 的估算建立在"几乎从 0 写"的假设上。库组合后实际工时分布：

| 周 | 主要工作 | 修订后工时 |
|---|---|---|
| W4 | loaders（用 unstructured 省 200 行）+ chunkers + Chroma 跑通 RAG | 20-24h（原 26h，略松）|
| W5 | retrieval（写 RRF ~50 行 + 调 pymilvus + bm25）+ MCP hello-world（SDK 范例改 50 行）+ LeetCode GraphQL 移植 | 24-28h（原 26h，仍紧）|
| W6 | graph（langgraph 6 节点）+ features 编排 + cli + sqlite | 26h（原 26h，刚好）|

W4 因为 `unstructured` 省了大量解析代码，W5 仍是瓶颈周（混合检索 + MCP + LeetCode 三件同时）。

### 9.4 路径 C · LangGraph 模板拼接

#### 9.4.1 起点模板候选

| 起点 | 来源 | 文件数 | 适合度 |
|---|---|---|---|
| `langgraph/examples/rag/agentic_rag/` | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | ~5 个 notebook + py | **首选**：直接对应 CodeMate 形态 |
| `langchain-cli new my-agent --template retrieval-agent-fireworks` | langchain-cli | ~10 文件 | 次选：需脱掉 Fireworks 切自己模型 |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | LangGraph 官方 deep research 范本 | ~20 文件 | 学多 agent 编排可用 |

#### 9.4.2 模块来源映射

| CodeMate 模块 | 来源 | 操作 |
|---|---|---|
| Agent flow 骨架 | langgraph `react-agent` 模板 | 改 prompt + 加自定义节点 |
| MCP server hello-world | `modelcontextprotocol/python-sdk` examples/simple-tool | 直接复制改 |
| 混合检索 RRF | onyx `postprocessing.py` | 抄 ~50 行 |
| LeetCode 工具 | 原创 + 移植 leetcode-mcp GraphQL | 路径 B 同款 |
| 算法掌握度 | `py-fsrs` pip 装 | 直接调 |

#### 9.4.3 与 §7.3 借鉴溯源矩阵的融合

§7.3 矩阵保持不变，但在每一行的"借鉴来源"列后加一个"来源类型"标签（template / 参考 / 移植 / 自写），明确"我抄了模板还是我自己写"。

### 9.5 决策矩阵

5 维评分（每维 1-5 星，5 最优）：

| 维度 | 路径 A | 路径 B | 路径 C |
|---|---|---|---|
| 简历叙述强度 | ★★ | ★★★★★ | ★★★½ |
| 9 周可行性 | ★★★★½ | ★★★ | ★★★★ |
| 学习深度 | ★★ | ★★★★★ | ★★★★ |
| 上游依赖风险 | ★★（kotaemon 改坏要跟）| ★★★★★（库稳定）| ★★★★（模板偶尔升级）|
| 与 architecture.md §3 兼容度 | ★★（§3.4 立不住）| ★★★★★（本就为 B 设计）| ★★★★ |
| **总分** | **12.5 / 25** | **22 / 25** | **20 / 25** |

### 9.6 各路径下的"可砍 / 可加"建议

#### 9.6.A 路径 A 下

- §3.4 真混合检索 → **直接用 kotaemon 的**（已实现），原创亮点切换到 §3.8 自写 MCP + LeetCode Python 移植
- 功能 C/D（代码 review / 学习计划）→ W9 加分项
- 简历重点 → "MCP 协议早期实践 + LeetCode 工具 + Cursor 集成"

#### 9.6.B 路径 B 下（默认）

- §3.4 真混合检索 → Tier 2 **应做**，Tier 1 退路 = 纯稠密 + Reranker（与原 §5.3 风险矩阵第 2 行的退路一致）
- 功能 C/D → W9 加分项
- 简历重点 → "Agentic RAG + 真混合检索 + 自研 MCP server"

#### 9.6.C 路径 C 下

- §3.4 真混合检索 → 直接抄 onyx 的 `postprocessing.py`（~50 行 RRF）
- Agent flow 用模板，节省 W6 ~10h 用于补 Reranker / Ragas
- 简历重点 → "LangGraph + 自研混合检索 + MCP" 居中表达

### 9.7 推荐 + 改选触发条件

**默认推荐：路径 B**。理由：

- 与 [architecture.md §3](architecture.md) 设计一致，无需重写
- 简历最强（5★）+ 学习最深（10+ 项核心技能）
- 上游依赖风险最低（成熟库）

**改选触发信号**（按时间顺序）：

| 关口 | 信号 | 触发动作 |
|---|---|---|
| W4 末 | RAG QA P95 > 10s 或召回率 < 70% 或 Chroma 跑不通 | **切路径 A**：用 kotaemon 已调好的 pipeline，W4 周末转 fork |
| W5 末 | MCP hello-world 写不出 或 LangGraph 6 节点设计卡死 | **切路径 C**：用 langgraph examples 模板起步 |
| 期末（W7-W8）| 实际工时 < 12h/周 | **B 内降级**：保留差异化三件套（RRF / MCP / LeetCode），砍 Tier 3 项 |
| W6 末 | Tier 1 没达成（功能 A 没跑通 / 引用没做）| **冻结新功能**，W7 全周补 Tier 1 |

### 9.8 库替代矩阵 + 分级 MVP

#### 9.8.1 库替代矩阵

每个模块在"时间不够"时的退路。**粗体行是简历核心，不可替代**：

| 模块 | 计划做法（Path B 默认）| 时间不够时退路 | 代价 |
|---|---|---|---|
| `loaders/` | `unstructured` 包封装 | 切 `langchain.document_loaders` | 引用粒度变粗 |
| `chunkers/` | `langchain-text-splitters` | 同上，无变化 | 无 |
| `embeddings/` | `FlagEmbedding` 本地 bge-m3 | 切 DeepSeek embedding API | 失去"本地推理"叙述 |
| `retrieval/` 稠密 | `pymilvus` | 切 `chromadb` 持久化 | 性能略损 |
| **`retrieval/` BM25 + RRF** | 自写 ~50 行 RRF | **跳过混合，纯稠密** | **失去 §3.4 原创亮点** |
| `retrieval/` Reranker | `FlagEmbedding` cross-encoder | 跳过 | 召回降 5-8% |
| `graph/` 6 节点 | 自写 LangGraph 节点 | `langgraph.prebuilt.create_react_agent` 一行 | 失去自定义 reasoning 控制 |
| **`tools/leetcode.py`** | 移植 leetcode-mcp 的 GraphQL | （**无库可替**）| — |
| **`mcp_server/`** | 用 `mcp` Python SDK | （**无库可替**）| — |
| `features/` | 自写编排 | — | — |
| `persistence/` | SQLAlchemy + py-fsrs | `sqlite3` 标准库 + 简化评分 | 略繁琐但能跑 |
| `api/` SSE | `fastapi` + `sse-starlette` | 关流式用 polling | 失去流式体验 |
| `cli/` | `typer` | `argparse` 标准库 | 美观度下降 |
| `ui/` | `streamlit` | 不做 UI、纯 CLI | 失去 W9 演示加分项 |

#### 9.8.2 三件不可替代模块及原因

1. **真混合检索（BM25 + 稠密 + RRF + Reranker）**：没人替你写这个组合；onyx 提供参考但你要 Milvus 版；自写 50 行 RRF 是简历的"原创"证明
2. **自写 MCP server**：MCP 是新兴协议，市场上几乎没有候选人有；只能用官方 Python SDK 从 0 写
3. **LeetCode 工具 Python 移植**：leetcode-mcp 是 TypeScript；移植到 Python 时 CSRF/Cookie/slug↔questionId 是你的实现

这三件合计 ~750 行代码，是 CodeMate 项目的简历核心。

#### 9.8.3 Tier 分级 MVP

| Tier | 内容 | 简历价值 | 截止 |
|---|---|---|---|
| **Tier 1（必达）** | 功能 A 跑通 + 引用 + MCP hello-world + LeetCode `get_problem` + CLI | "能用的 RAG + MCP server"——最低及格线 | W6 末 |
| **Tier 2（应做）** | + 真混合检索 RRF + 算法掌握度（Ebbinghaus 简版）+ Reranker + Ragas 30 题评估 | "Agentic RAG + 评估闭环"——能讲故事 | W8 末 |
| **Tier 3（加分）** | + Code Review 功能 + Streamlit UI + FSRS + Langfuse + 1 个 C++ 拓展 | "完整产品 + 系统底层"——简历亮点 | W9 末 |

每周末 checkpoint：评估本周完成度，决定下周是否升 Tier 或降级。

#### 9.8.4 触发降级的具体信号

| 信号 | 触发动作 |
|---|---|
| W4 末 RAG QA P95 > 10s | 切 Chroma + 跳过 BM25，W5 不做混合 |
| W5 末 MCP hello-world 跑不通 | 暂停 LeetCode，先把 MCP `get_problem` mock 工具跑通 |
| W6 末 Tier 1 没达成 | W7 全周补 Tier 1，跨期末延后 Tier 2 至 W8 末 |
| 期末工时 < 12h/周 | 砍 Tier 3 的 Code Review 和 FSRS，保 Streamlit + 1 个 C++ 拓展 |
| W8 末 Ragas 跑不出来 | 简化为 5 题人工评估 + README 截图 |

---

**§9 总结**：默认走路径 B，把混合检索 RRF / MCP server / LeetCode 移植 当作不可替代的简历核心；其它模块全部用成熟库当地基。Tier 分级 + 每周末 checkpoint 是 9 周不翻车的保险。
