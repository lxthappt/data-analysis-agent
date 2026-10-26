import io
import json
import os
import sys

import numpy as np
import pandas as pd
from langchain_core.tools import tool

# 数据库文件绝对路径（保证任意目录下运行都能找到）
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "ecommerce.db"
)


@tool
def query_sql(sql: str) -> str:
    """对 SQLite 数据库执行一条 SELECT 查询，返回表格结果。

    适合回答：分组统计（各品类销量）、排序筛选（TopN）、过滤（某地区订单）等
    能用一条 SQL 解决的问题。参数 sql 必须是完整 SELECT 语句。
    """
    import sqlite3

    # 安全第一：用只读模式打开数据库，写操作在连接层就被拒绝
    # uri=True 不能省，否则 SQLite 会把 "file:...?mode=ro" 当成普通文件名（静默建空库或直接报错）
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        df = pd.read_sql_query(sql, conn)
        # to_string 返回纯文本表格，LLM 能直接读
        return df.to_string(index=False)
    except Exception as e:  # SQL 写错时，把错误信息返回给 LLM，让它自己改
        return f"SQL 执行失败：{e}"
    finally:
        conn.close()



        # 预置在代码执行命名空间里的东西：数据表 df + 常用库
def _load_orders_df() -> pd.DataFrame:
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM orders", conn)
    conn.close()
    return df


@tool
def run_pandas_code(code: str) -> str:
    """执行一段 Python 代码做数据分析。

    代码里可以直接用变量 df（已加载的订单表），以及 pd、np 两个库。
    适合回答：需要多步计算、透视表、自定义逻辑、统计等问题。
    约定：把「想返回的结果」写在最后一行（不带赋值号），
    例如最后一行写 df.groupby('category')['quantity'].sum()。
    """
    namespace = {"pd": pd, "np": np, "df": _load_orders_df()}

    # 捕获代码里 print 的输出
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf

    result = None
    try:
        lines = code.strip().split("\n")
        last = lines[-1].strip()
        # 如果最后一行是「表达式」（没有赋值号、不是控制语句），单独 eval 它并返回结果
        if last and "=" not in last and not last.startswith(
            ("for", "if", "def", "import", "return", "#")
        ):
            exec("\n".join(lines[:-1]), namespace)
            result = eval(last, namespace)
        else:
            exec(code, namespace)
    except Exception as e:
        return f"代码执行失败：{e}"
    finally:
        sys.stdout = old_stdout

    # 拼接输出：优先返回 print 的内容 + 最后表达式的值
    parts = []
    printed = buf.getvalue().strip()
    if printed:
        parts.append("print 输出：\n" + printed)
    if result is not None:
        parts.append("结果：\n" + str(result))
    return "\n\n".join(parts) if parts else "代码执行完成（无输出）"


@tool
def create_chart(code: str) -> str:
    """用 Plotly 生成一张交互式图表。

    代码里可以用变量 df（订单表）以及 px（plotly.express）。
    约定：把生成的图表赋值给变量 fig，例如 fig = px.bar(df, x='category')。
    返回图表的 JSON，前端用它渲染。
    """
    import plotly.express as px
    import plotly.graph_objects as go

    namespace = {"pd": pd, "np": np, "df": _load_orders_df(), "px": px, "go": go}

    try:
        exec(code, namespace)
    except Exception as e:
        return f"图表生成失败：{e}"

    fig = namespace.get("fig")
    if fig is None:
        return "错误：请把生成的图表赋值给变量 fig，例如 fig = px.bar(...)"

    # 图表序列化成 JSON，前端用 plotly.js 反序列化渲染
    return json.dumps({"chart_json": fig.to_json()})