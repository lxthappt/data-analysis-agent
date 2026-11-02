"""测试三个工具的基本行为。"""
import sys
from pathlib import Path

# 测试文件在 tests/tests/ 下，需要退两级才能到项目根目录，再把 backend 加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from agent.tools import query_sql, run_pandas_code

def test_query_sql():
    r = query_sql.invoke("SELECT category, COUNT(*) FROM orders GROUP BY category")
    assert "category" in r

def test_query_sql_blocks_write():
    r = query_sql.invoke("DROP TABLE orders")
    assert "只允许" in r   # 危险语句被拦截

def test_run_pandas_code():
    r = run_pandas_code.invoke("df.groupby('category')['quantity'].sum()")
    assert "category" in r or "结果" in r