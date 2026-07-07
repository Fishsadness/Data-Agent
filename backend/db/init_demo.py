"""
Demo 数据库初始化
创建示例电商数据库：orders / products / users 三张表并插入测试数据
"""
import logging
import random
from datetime import datetime, timedelta

from sqlalchemy import text

from db.connection import engine

logger = logging.getLogger(__name__)

# 示例数据
PRODUCTS = [
    ("iPhone 15 Pro", "手机"),
    ("MacBook Air M3", "电脑"),
    ("AirPods Pro", "耳机"),
    ("iPad Air", "平板"),
    ("Apple Watch S9", "手表"),
    ("Sony WH-1000XM5", "耳机"),
    ("Dell XPS 15", "电脑"),
    ("Samsung Galaxy S24", "手机"),
    ("Logitech MX Master 3S", "配件"),
    ("机械键盘 K8 Pro", "配件"),
    ("4K 显示器 27寸", "电脑"),
    ("Type-C 扩展坞", "配件"),
    ("华为 Mate 60 Pro", "手机"),
    ("小米 14 Ultra", "手机"),
    ("ThinkPad X1 Carbon", "电脑"),
]

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京", "西安", "重庆"]


def init_demo_db():
    """初始化 Demo 数据库"""
    logger.info("开始初始化 Demo 数据库...")

    with engine.connect() as conn:
        # 创建表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                register_date TEXT NOT NULL
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                total_price REAL NOT NULL,
                create_time TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """))

        conn.commit()

        # 检查是否已有数据
        result = conn.execute(text("SELECT COUNT(*) FROM products"))
        if result.scalar() > 0:
            logger.info("Demo 数据库已有数据，跳过初始化")
            return

        # 插入商品
        for name, category in PRODUCTS:
            price = round(random.uniform(99, 9999), 2)
            conn.execute(
                text("INSERT INTO products (name, category, price) VALUES (:n, :c, :p)"),
                {"n": name, "c": category, "p": price},
            )

        # 插入用户
        user_ids = []
        for i in range(1, 51):
            city = random.choice(CITIES)
            days_ago = random.randint(1, 730)
            reg_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            result = conn.execute(
                text("INSERT INTO users (name, city, register_date) VALUES (:n, :c, :r)"),
                {"n": f"用户{i:03d}", "c": city, "r": reg_date},
            )
            user_ids.append(result.lastrowid)

        # 插入订单
        product_ids = list(range(1, len(PRODUCTS) + 1))
        base_date = datetime(2024, 1, 1)
        order_count = 0

        for _ in range(500):
            user_id = random.choice(user_ids)
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 5)

            # 查价格
            price_result = conn.execute(
                text("SELECT price FROM products WHERE id = :pid"),
                {"pid": product_id},
            )
            price = price_result.scalar()
            total_price = round(price * quantity, 2)

            days_offset = random.randint(0, 550)
            order_time = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d %H:%M:%S")

            conn.execute(
                text(
                    "INSERT INTO orders (user_id, product_id, quantity, total_price, create_time) "
                    "VALUES (:uid, :pid, :qty, :tp, :ct)"
                ),
                {"uid": user_id, "pid": product_id, "qty": quantity, "tp": total_price, "ct": order_time},
            )
            order_count += 1

        conn.commit()

    logger.info(f"Demo 数据库初始化完成: {len(PRODUCTS)} 商品, 50 用户, {order_count} 订单")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_demo_db()