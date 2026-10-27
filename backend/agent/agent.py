"""组装 LangGraph Agent：LLM 节点 + 工具节点 + 循环路由。"""
import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from prompts import SYSTEM_PROMPT
from tools import create_chart, query_sql, run_pandas_code

load_dotenv()  # 读取 .env 里的 DEEPSEEK_API_KEY

# 1. 配置 LLM（DeepSeek，走 OpenAI 兼容接口）
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0,  # 数据分析要稳定，设为 0 减少随机性
)

tools = [query_sql, run_pandas_code, create_chart]
llm_with_tools = llm.bind_tools(tools)  # 关键：让 LLM 知道有哪些工具可用


# 2. 定义「LLM 节点」：把系统提示 + 历史消息喂给 LLM
def llm_node(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# 3. 定义「路由」：LLM 这轮有没有要求调用工具？
def should_continue(state: MessagesState):
    last = state["messages"][-1]
    if last.tool_calls:      # 有工具调用 → 去执行工具
        return "tools"
    return END                 # 没有 → 结束，返回最终答案


# 4. 画状态图：LLM ⇄ 工具 的循环
builder = StateGraph(MessagesState)
builder.add_node("llm", llm_node)
builder.add_node("tools", ToolNode(tools))        # ToolNode 自动执行工具
builder.add_edge(START, "llm")
builder.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "llm")                  # 工具执行完，回到 LLM 继续想

# 5. 加内存，支持多轮对话（记住上下文）
memory = MemorySaver()
agent = builder.compile(checkpointer=memory)


def run(question: str, thread_id: str = "default") -> str:
    """对外的调用入口。thread_id 用于区分不同会话。"""
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [("user", question)]}, config=config)
    return result["messages"][-1].content