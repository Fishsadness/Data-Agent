"""
数据库连接管理
支持 SQLite / MySQL / PostgreSQL，通过 DATABASE_URL 配置切换
"""
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from config import DATABASE_URL, SQL_SAFETY

logger = logging.getLogger(__name__)


def _setup_sqlite_pragma(dbapi_connection, connection_record):
    """为 SQLite 连接设置超时"""
    cursor = dbapi_connection.cursor()
    cursor.execute(f"PRAGMA busy_timeout = {SQL_SAFETY['max_query_timeout'] * 1000}")
    cursor.close()


def _setup_readonly_pragma(dbapi_connection, connection_record):
    """为 SQLite 连接设置只读模式"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA query_only = ON")
    cursor.close()


def create_db_engine(readonly: bool = False) -> Engine:
    """创建数据库引擎"""
    connect_args = {}
    poolclass = None

    if "sqlite" in DATABASE_URL:
        connect_args = {"check_same_thread": False}
        poolclass = StaticPool

    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        poolclass=poolclass,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    if "sqlite" in DATABASE_URL:
        event.listen(engine, "connect", _setup_sqlite_pragma)
        if readonly:
            event.listen(engine, "connect", _setup_readonly_pragma)

    return engine


# 全局引擎实例（读写模式，用于初始化）
engine = create_db_engine(readonly=False)

# 只读引擎（用于查询）
readonly_engine = create_db_engine(readonly=True) if SQL_SAFETY["readonly"] else engine


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


def execute_readonly(sql: str):
    """执行只读 SQL 查询，返回结果列表"""
    conn = readonly_engine.connect()
    try:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
        return columns, [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def test_connection() -> bool:
    """测试数据库连接是否正常"""
    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False