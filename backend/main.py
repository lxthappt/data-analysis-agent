"""FastAPI 入口：把 Agent 包装成 /chat 接口。"""
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, ToolMessage
from pydantic import BaseModel

from agent.agent import agent

app = FastAPI(title="数据分析 Agent")

# CORS：允许 Vue3 开发服务器（默认 5173 端口）跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """请求体：问题 + 会话 ID。"""
    question: str
    thread_id: str = "default"   # 多轮对话时，同一个会话用同一个 thread_id


@app.post("/chat")
def chat(req: ChatRequest):
    """核心接口：接收问题，返回答案 + 图表 + 执行过程。"""
    config = {"configurable": {"thread_id": req.thread_id}}
    result = agent.invoke({"messages": [("user", req.question)]}, config=config)

    messages = result["messages"]
    answer = messages[-1].content  # 最后一条消息就是最终答案

    # 遍历消息流，提取「中间步骤」和「图表」，供前端可视化执行过程
    steps = []
    chart = None
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            # LLM 这轮想调工具 → 记下「调了什么、传了什么参数」
            for tc in m.tool_calls:
                steps.append({
                    "type": "tool_call",
                    "tool": tc["name"],
                    "args": tc.get("args", {}),
                })
        elif isinstance(m, ToolMessage):
            output = m.content
            # 图表工具的结果单独拎出来，不放步骤里（避免 JSON 撑爆前端）
            if m.name == "create_chart" and output.startswith("{"):
                chart = json.loads(output)
            else:
                steps.append({
                    "type": "tool_result",
                    "tool": m.name,
                    "output": output[:500],   # 截断，只给前端看前 500 字
                })

    return {"answer": answer, "chart": chart, "steps": steps}


@app.get("/health")
def health():
    return {"status": "ok"}