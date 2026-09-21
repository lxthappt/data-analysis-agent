# 数据分析 Agent

自然语言驱动的数据分析助手：用户用一句话提问，Agent 自动判断该用 **SQL** 还是 **Pandas**，完成查询、分析、图表生成，并返回结论。

> 🚧 **项目开发中**，当前进度见下方「开发进度」。

## 核心特性（目标）

- 🧠 **双引擎** —— Agent 自动选择：简单聚合走 SQL，复杂计算走 Pandas
- 📊 **图表生成** —— 自然语言描述即可生成交互式 Plotly 图表
- 🔍 **执行过程可视化** —— Agent 每步调用了什么工具、传了什么参数，全程可回看
- 🔒 **安全执行** —— SQL 只读限制 + Python 受限命名空间
- 💬 **多轮对话** —— 支持追问，记住上下文

## 技术栈

| 层次 | 技术 |
|------|------|
| Agent 编排 | LangGraph · LangChain |
| 后端接口 | FastAPI · Uvicorn |
| 前端 | Vue3 · Vite |
| 数据分析 | Pandas · NumPy · Plotly |
| 数据库 | SQLite |
| 大模型 | DeepSeek（`deepseek-chat`） |

## 架构

```
┌─────────────┐   HTTP    ┌──────────────┐      ┌─────────────────────┐
│  Vue3 前端   │ ────────▶ │  FastAPI 后端 │ ───▶ │  LangGraph Agent    │
│  (聊天界面)  │ ◀──────── │  (/chat 接口) │      │  (ReAct 循环)        │
└─────────────┘           └──────────────┘      │  ┌────────────────┐  │
                                                │  │ 工具1: SQL查询  │  │
                                                │  │ 工具2: Pandas  │  │
                                                │  │ 工具3: 图表     │  │
                                                │  └────────────────┘  │
                                                └──────────┬──────────┘
                                                           │
                                                ┌──────────▼──────────┐
                                                │   DeepSeek API      │
                                                └─────────────────────┘
```

## 项目结构

```
.
├── backend/            # FastAPI + LangGraph Agent
│   ├── agent/          # Agent 核心（工具、状态图、提示词）
│   ├── db/             # 数据库初始化
│   └── data/           # SQLite 数据文件（生成，不入库）
├── frontend/           # Vue3 聊天界面
├── tests/              # 单元测试
├── .env.example        # 环境变量模板
└── requirements.txt    # Python 依赖
```

## 快速开始

> ⚠️ 项目尚未完成，以下步骤待后端实现后可用。

```bash
# 1. 克隆
git clone https://github.com/lxthappt/data-analysis-agent.git
cd data-analysis-agent

# 2. 建虚拟环境并装依赖
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. 配置密钥
cp .env.example .env               # 然后填入你的 DEEPSEEK_API_KEY

# 4. 初始化示例数据
cd backend && python db/init_db.py

# 5. 启动后端
uvicorn main:app --reload

# 6. 启动前端（另开一个终端）
cd frontend && npm install && npm run dev
```

## 开发进度

- [x] 项目初始化（目录结构、.gitignore、LICENSE、README）
- [x] 环境依赖（requirements.txt）
- [ ] 示例数据（SQLite 电商订单表）
- [ ] 三个工具（SQL 查询 / Pandas 分析 / 图表生成）
- [ ] Agent 核心（LangGraph 状态图）
- [ ] FastAPI 接口（/chat）
- [ ] Vue3 前端
- [ ] 单元测试
- [ ] 部署说明

## 技术难点与解决

| 难点 | 解决方案 |
|------|---------|
| 如何让 LLM 选对工具 | 工具 docstring 写清适用场景 + 系统提示词双重引导 |
| Text2SQL 准确率低 | 系统提示词注入表 schema + 执行报错回传让 LLM 自我修正 |
| LLM 生成的代码不安全 | SQL 强制只读 + Python 受限命名空间（无 os/sys） |
| 多轮对话上下文 | LangGraph checkpointer 按 thread_id 持久化状态 |

## License

[MIT](LICENSE)
