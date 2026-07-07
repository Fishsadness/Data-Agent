"""
数据库 Schema 读取模块
自动获取表结构信息，作为 LLM Prompt 的上下文
"""
import logging
from typing import Optional

from sqlalchemy import inspect, text

from db.connection import engine

logger = logging.getLogger(__name__)


def get_table_names() -> list[str]:
    """获取所有表名"""
    inspector = inspect(engine)
    return inspector.get_table_names()


def get_table_schema(table_name: str) -> dict:
    """获取单张表的完整 Schema 信息"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    pk = inspector.get_pk_constraint(table_name)
    fks = inspector.get_foreign_keys(table_name)

    pk_columns = set(pk.get("constrained_columns", []))

    col_info = []
    for col in columns:
        col_info.append({
            "name": col["name"],
            "type": str(col["type"]),
            "nullable": col.get("nullable", True),
            "primary_key": col["name"] in pk_columns,
            "default": str(col.get("default")) if col.get("default") else None,
        })

    return {
        "table_name": table_name,
        "columns": col_info,
        "foreign_keys": [
            {
                "columns": fk["constrained_columns"],
                "referenced_table": fk["referred_table"],
                "referenced_columns": fk["referred_columns"],
            }
            for fk in fks
        ],
    }


def get_all_schemas() -> dict:
    """获取所有表的 Schema"""
    schemas = {}
    for table_name in get_table_names():
        schemas[table_name] = get_table_schema(table_name)
    return schemas


def schema_to_prompt_text(schemas: Optional[dict] = None) -> str:
    """将 Schema 转换为 Prompt 可用的文本格式"""
    if schemas is None:
        schemas = get_all_schemas()

    lines = []
    for table_name, info in schemas.items():
        lines.append(f"表: {table_name}")
        lines.append("-" * 40)
        for col in info["columns"]:
            flags = []
            if col["primary_key"]:
                flags.append("PK")
            if not col["nullable"]:
                flags.append("NOT NULL")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            lines.append(f"  {col['name']}: {col['type']}{flag_str}")

        if info["foreign_keys"]:
            for fk in info["foreign_keys"]:
                lines.append(
                    f"  FK: {', '.join(fk['columns'])} "
                    f"-> {fk['referenced_table']}({', '.join(fk['referenced_columns'])})"
                )
        lines.append("")

    return "\n".join(lines)


def get_sample_data(table_name: str, limit: int = 3) -> list[dict]:
    """获取表的示例数据，帮助 LLM 理解数据内容"""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]