"""
多数据库统一查询接口
支持 MySQL / PostgreSQL / SQLite / ClickHouse 等
"""
import logging
from typing import Optional

from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """统一数据库连接器"""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(
                self.url,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        return self._engine

    def execute(self, sql: str):
        """执行查询"""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return columns, rows

    def get_tables(self) -> list[str]:
        """获取表列表"""
        with self.engine.connect() as conn:
            from sqlalchemy import inspect
            inspector = inspect(conn)
            return inspector.get_table_names()


class MultiDBManager:
    """
    多数据库管理器
    支持同时连接多个异构数据库，自动路由查询
    """

    def __init__(self):
        self._databases: dict[str, DatabaseConnector] = {}

    def register(self, name: str, url: str):
        """注册数据库连接"""
        self._databases[name] = DatabaseConnector(name, url)
        logger.info(f"注册数据库: {name}")

    def get(self, name: str) -> Optional[DatabaseConnector]:
        return self._databases.get(name)

    def list_databases(self) -> list[str]:
        return list(self._databases.keys())

    def execute_on(self, db_name: str, sql: str):
        """在指定数据库上执行查询"""
        db = self.get(db_name)
        if not db:
            raise ValueError(f"数据库 {db_name} 未注册")
        return db.execute(sql)

    def execute_all(self, sql: str) -> dict[str, tuple]:
        """在所有数据库上执行查询"""
        results = {}
        for name, db in self._databases.items():
            try:
                results[name] = db.execute(sql)
            except Exception as e:
                results[name] = (["error"], [{"error": str(e)}])
        return results

    def get_all_schemas(self) -> dict:
        """获取所有数据库的 Schema"""
        schemas = {}
        for name, db in self._databases.items():
            try:
                tables = db.get_tables()
                schemas[name] = {
                    "type": "sqlite" if "sqlite" in db.url else "other",
                    "tables": tables,
                }
            except Exception as e:
                schemas[name] = {"error": str(e)}
        return schemas


# 全局实例
multi_db = MultiDBManager()