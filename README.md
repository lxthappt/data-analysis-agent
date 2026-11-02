# 数据分析 Agent

自然语言驱动的数据分析助手：用一句话提问，Agent 自动判断该用 **SQL** 还是 **Pandas**，完成查询、分析、图表生成，并给出中文结论。

无需手写 SQL 或 Python，也无需在多个工具之间来回切换。

## 功能特性

- 🧠 **双引擎自动选择** —— 简单聚合走 `query_sql`，多步计算 / 自定义逻辑走 `run_pandas_code`，由 LLM 根据问题自行判断
- 📊 **交互式图表** —— 说「画个图」，Agent 调用 `create_chart` 生成 Plotly 图表，前端直接渲染，支持缩放、悬停
- 🔍 **执行过程可视化** —— 每一步调用了哪个工具、传了什么参数、返回了什么，前端可折叠回看
- 💬 **多轮对话** —— 基于 LangGraph `MemorySaver` + `thread_id` 记住同一会话的上下文，支持「刚才那个结果里……」这类追问
- 🔒 **SQL 只读防护** —— 语句白名单 + 只读模式连接双层拦截，写操作无法执行
- 🧪 **单元测试** —— 覆盖工具正常调用与危险语句拦截
- ⚡ **零外部数据库** —— SQLite 文件由脚本一键生成，克隆即可跑

## 技术栈

| 层次 | 技术 |
|------|------|
| Agent 编排 | LangGraph · LangChain |
| 大模型 | DeepSeek `deepseek-chat`（OpenAI 兼容接口） |
| 后端接口 | FastAPI · Uvicorn · Pydantic |
| 前端 | Vue 3 · Vite · plotly.js |
| 数据分析 | Pandas · NumPy · Plotly |
| 数据库 | SQLite |
| 测试 | pytest |

## 架构

```
┌──────────────┐   HTTP POST /chat   ┌────────────────┐
│  Vue3 前端    │ ──────────────────▶ │  FastAPI 后端   │
│  localhost:  │ ◀────────────────── │  localhost:8000 │
│  5173        │  answer/chart/steps │                 │
└──────────────┘                     └────────┬────────┘
                                              │ invoke
                                     ┌────────▼────────┐
                                     │  LangGraph Agent │
                                     │                  │
                                     │   ┌──────────┐   │
                              ┌──────┼──▶│ llm 节点  │   │
                              │      │   └────┬─────┘   │
                              │      │        │ 有 tool_calls?
                              │      │   ┌────▼─────┐   │
                              │      └───│ tools 节点 │   │
                              │          └────┬─────┘   │
                              │               │          │
                              │   query_sql / run_pandas_code / create_chart
                              │               │          │
                              │        ┌──────▼───────┐  │
                              │        │ SQLite       │  │
                              │        │ ecommerce.db │  │
                              │        └──────────────┘  │
                              └──────────────────────────┘
                                     │
                              ┌──────▼───────┐
                              │ DeepSeek API │
                              └──────────────┘
```

**一次请求的流程**

1. 前端把 `question` 和 `thread_id` 发给 `POST /chat`
2. LangGraph 的 `llm` 节点带着系统提示词和历史消息调用 DeepSeek
3. 若模型决定调工具，路由到 `tools` 节点执行，结果回传给 `llm` 继续推理，循环直到不再调用工具
4. 后端从消息流中提取最终答案、图表 JSON 和中间步骤，一次性返回
5. 前端展示答案，可折叠查看执行过程，并用 `Plotly.newPlot` 渲染图表

## 项目结构

```
.
├── backend/
│   ├── main.py               # FastAPI 入口：/chat、/health
│   ├── chat_cli.py           # 命令行交互脚本（非 pytest）
│   ├── agent/
│   │   ├── agent.py          # LangGraph 状态图组装（LLM ⇄ 工具循环）
│   │   ├── tools.py          # 三个工具：SQL / Pandas / 图表
│   │   └── prompts.py        # 系统提示词（表结构、工具选择规则）
│   ├── db/
│   │   └── init_db.py        # 生成示例数据库（1000 行电商订单）
│   └── data/
│       └── ecommerce.db      # 由 init_db.py 生成，不提交
├── frontend/
│   ├── src/
│   │   ├── App.vue           # 聊天界面 + 图表渲染
│   │   ├── main.js
│   │   └── style.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── tests/
│   └── tests/
│       └── test_tools.py     # 工具单元测试
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖（版本已锁定）
└── LICENSE
```

## 快速开始

**环境要求**：Python 3.10+、Node.js 18+、一个可用的 DeepSeek API Key。

### 1. 获取代码并安装 Python 依赖

```bash
git clone https://github.com/lxthappt/data-analysis-agent.git
cd data-analysis-agent

python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，把 `DEEPSEEK_API_KEY` 换成你自己的 key：

```dotenv
DEEPSEEK_API_KEY=sk-你的key
```

> `.env` 已被 `.gitignore` 忽略，不会进入版本库。

### 3. 初始化示例数据库

```bash
cd backend
python db/init_db.py
```

输出 `数据库已生成：.../ecommerce.db，共 1000 行` 即成功。脚本可重复执行，每次会重建数据（固定随机种子，结果一致）。

### 4. 启动后端（终端 A）

```bash
# 仍在 backend 目录下
uvicorn main:app --reload --port 8000
```

- 接口地址：<http://localhost:8000>
- 自动生成的接口文档：<http://localhost:8000/docs>

### 5. 启动前端（终端 B）

```bash
cd frontend
npm install
npm run dev
```

打开 <http://localhost:5173>，即可开始提问。

### 6. 命令行模式（可选）

不启动前端，直接在终端里对话：

```bash
cd backend
python chat_cli.py
```

## 示例问题

| 问题 | 预期调用 |
|------|---------|
| 各品类销售额排名前 3 是哪些？ | `query_sql` |
| 哪个地区的平均订单金额最高？ | `query_sql` |
| 用透视表算每个地区各品类的平均订单金额 | `run_pandas_code` |
| 订单金额的分布情况，画个直方图 | `query_sql` + `create_chart` |
| 按月统计销售额趋势并画折线图 | `create_chart` |
| 刚才的结果里，华东占多少比例？ | 多轮追问，复用上下文 |

示例数据为 **1000 行电商订单**，表名 `orders`，字段如下：

| 字段 | 含义 |
|------|------|
| `order_id` | 订单 ID |
| `order_date` | 下单日期（2024 年内） |
| `category` | 品类（电子产品 / 服饰 / 家居 / 食品 / 美妆） |
| `quantity` | 数量（1–4） |
| `price` | 单价（10–500） |
| `customer_id` | 客户 ID |
| `region` | 地区（华东 / 华南 / 华北 / 西南 / 东北） |

> 销售额 = `quantity * price`。

## API 文档

### `POST /chat`

请求体：

```json
{
  "question": "各品类销售额排名前3是哪些？",
  "thread_id": "demo"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question` | string | 是 | 自然语言问题 |
| `thread_id` | string | 否 | 会话 ID，默认 `"default"`；同一 ID 共享上下文 |

响应体：

```json
{
  "answer": "销售额排名前三的品类是……",
  "chart": null,
  "steps": [
    { "type": "tool_call", "tool": "query_sql", "args": { "sql": "SELECT ..." } },
    { "type": "tool_result", "tool": "query_sql", "output": "category  revenue\n..." }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `answer` | 最终中文结论 |
| `chart` | 图表对象 `{ "chart_json": "<Plotly Figure JSON 字符串>" }`；无图表时为 `null` |
| `steps` | 执行过程，`tool_call` 记录参数，`tool_result` 记录输出（截断 500 字） |

<details>
<summary>curl 示例</summary>

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "各品类销售额排名前3是哪些？", "thread_id": "demo"}'
```

</details>

### `GET /health`

```json
{ "status": "ok" }
```

## 安全设计

| 措施 | 实现位置 | 说明 |
|------|---------|------|
| SQL 语句白名单 | [tools.py](backend/agent/tools.py) `query_sql` | 仅放行 `SELECT` / `WITH` 开头的语句，其余直接拒绝 |
| 只读连接 | 同上 | 以 `mode=ro` URI 打开 SQLite，写操作在驱动层失败 |
| 分析代码命名空间 | `run_pandas_code` | 只预置 `pd`、`np`、`df`，不暴露 `os` / `sys` |
| 密钥隔离 | `.env` + `.gitignore` | Key 不进入代码、不进入提交 |
| 跨域限制 | [main.py](backend/main.py) | CORS 仅允许 `http://localhost:5173` |

> ⚠️ **如实说明**：`run_pandas_code` 使用 `exec` 执行模型生成的代码，命名空间里没有 `os`/`sys`，但未禁用 `__builtins__`，因此并非真正的安全沙箱，仍可通过 `__import__` 访问系统。当前定位是**降低误操作风险**，适用于本地可信环境。若要对外部署，应改为子进程 / 容器隔离执行。

## 测试

先确保示例数据库已生成，然后在项目根目录执行：

```bash
pytest tests/ -v
```

覆盖内容：

- `query_sql` 正常查询
- `query_sql` 拦截 `DROP TABLE` 等写操作
- `run_pandas_code` 正常执行聚合代码

`backend/chat_cli.py` 是手工交互脚本，不含测试用例，需按上文「命令行模式」单独运行。

## 技术难点与解决

| 难点 | 解决方案 |
|------|---------|
| 如何让 LLM 选对工具 | 工具 docstring 写清适用场景 + 系统提示词双重引导 |
| Text2SQL 准确率低 | 系统提示词注入表结构与字段含义 + 执行报错回传让 LLM 自我修正 |
| LLM 生成的 SQL 不安全 | 语句白名单 + 只读 URI 连接双层拦截 |
| LLM 生成的 Python 代码不可控 | 预置受限命名空间，只给 `pd`/`np`/`df` |
| 多轮对话上下文 | LangGraph `MemorySaver` 按 `thread_id` 持久化消息 |
| 前端如何渲染后端生成的图表 | Plotly `fig.to_json()` 序列化 → 前端 `JSON.parse` 后 `Plotly.newPlot` |
| 如何向用户展示 Agent 的中间步骤 | 遍历返回的消息流，把 `AIMessage.tool_calls` 与 `ToolMessage` 拆成 `steps` |

## 已知限制

- **会话只存在内存中**：`MemorySaver` 重启即丢；前端每次刷新页面会生成新的 `thread_id`，历史不会保留。
- **数据源固定**：表名、字段、数据库路径写死在提示词和工具里，换数据集需要改代码。
- **Pandas 执行不是真沙箱**：见上方安全说明。
- **无流式输出**：`/chat` 会等 Agent 全部跑完才返回，复杂分析需要等待。
- **一次只渲染一张图表**：后端只保留最后一个 `create_chart` 的结果。
- **前后端地址硬编码**：前端请求 `http://localhost:8000`，CORS 仅允许 5173 端口。

## 后续计划

- [ ] 会话持久化：改用 SQLite checkpointer，刷新不丢历史
- [ ] 流式输出：SSE 推送执行步骤，改善长任务体验
- [ ] 支持上传 CSV / 接入多个数据源，自动生成 schema
- [ ] Pandas / 图表代码改为沙箱子进程执行
- [ ] Docker Compose 一键启动
- [ ] 补充 Agent 层的集成测试

## License

[MIT](LICENSE) © 2026 lxt
