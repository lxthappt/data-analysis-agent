"""初始化 SQLite 示例数据库：建一张电商订单表，造 1000 行随机数据。"""
import os
import sqlite3

import numpy as np
import pandas as pd

# 数据库文件位置（backend/data/ecommerce.db）
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DB_DIR, "ecommerce.db")


def init_db() -> None:
    """建库 + 造数据。可重复执行（每次会重建）。"""
    os.makedirs(DB_DIR, exist_ok=True)

    np.random.seed(42)  # 固定随机种子，保证每次生成的数据一样，方便测试
    n = 1000

    categories = ["电子产品", "服饰", "家居", "食品", "美妆"]
    regions = ["华东", "华南", "华北", "西南", "东北"]

    df = pd.DataFrame({
        "order_id": range(1, n + 1),
        # 2024 年内随机某一天
        "order_date": pd.to_datetime("2024-01-01") +
                      pd.to_timedelta(np.random.randint(0, 365, n), unit="D"),
        "category": np.random.choice(categories, n),
        "quantity": np.random.randint(1, 5, n),
        "price": np.round(np.random.uniform(10, 500, n), 2),
        "customer_id": np.random.randint(1, 200, n),
        "region": np.random.choice(regions, n),
    })

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("orders", conn, if_exists="replace", index=False)
    conn.close()
    print(f"数据库已生成：{DB_PATH}，共 {len(df)} 行")


if __name__ == "__main__":
    init_db()