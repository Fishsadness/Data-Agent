"""
Agent 工具定义
定义 Data Agent 可用的各种工具
"""
import logging
from typing import Optional

from langchain_core.tools import tool

from db.schema import (
    get_all_schemas,
    get_table_names,
    get_table_schema,
    get_sample_data,
    schema_to_prompt_text,
)
from db.connection import execute_readonly
from agent.safety import check_sql_safety, add_row_limit

logger = logging.getLogger(__name__)


@tool
def read_database_schema() -> str:
    """
    读取数据库的完整 Schema 信息。
    包括所有表名、字段名、字段类型、主键、外键关系。
    在生成任何 SQL 之前必须先调用此工具。
    """
    schemas = get_all_schemas()
    return schema_to_prompt_text(schemas)


@tool
def list_tables() -> str:
    """列出数据库中所有表名"""
    tables = get_table_names()
    return "数据库中的表:\n" + "\n".join(f"  - {t}" for t in tables)


@tool
def describe_table(table_name: str) -> str:
    """
    查看指定表的详细结构。
    参数 table_name: 表名
    """
    try:
        schema = get_table_schema(table_name)
        sample = get_sample_data(table_name, limit=2)
        result = schema_to_prompt_text({table_name: schema})
        if sample:
            result += f"\n示例数据 (前2行):\n{sample}"
        return result
    except Exception as e:
        return f"读取表 {table_name} 失败: {str(e)}"


@tool
def execute_sql_query(sql: str) -> str:
    """
    执行 SQL 查询并返回结果。
    参数 sql: 要执行的 SQL 语句（仅支持 SELECT 查询）
    """
    # 安全检查
    safety = check_sql_safety(sql)
    if not safety.is_safe:
        return f"SQL 安全检查失败:\n" + "\n".join(f"  - {e}" for e in safety.errors)

    safe_sql = safety.sanitized_sql
    safe_sql = add_row_limit(safe_sql)

    try:
        columns, rows = execute_readonly(safe_sql)
        row_count = len(rows)

        if row_count == 0:
            return "查询结果为空"

        # 格式化输出
        result = f"查询成功，返回 {row_count} 行，{len(columns)} 列\n\n"
        result += " | ".join(columns) + "\n"
        result += "-" * 40 + "\n"

        for row in rows[:50]:  # 最多显示 50 行
            values = [str(row.get(col, "")) for col in columns]
            result += " | ".join(values) + "\n"

        if row_count > 50:
            result += f"\n... 还有 {row_count - 50} 行未显示"

        return result
    except Exception as e:
        logger.error(f"SQL 执行失败: {e}")
        return f"SQL 执行失败: {str(e)}"


@tool
def get_table_sample(table_name: str, limit: int = 5) -> str:
    """
    获取表的示例数据，了解数据内容。
    参数 table_name: 表名
    参数 limit: 返回行数，默认5
    """
    try:
        rows = get_sample_data(table_name, limit)
        if not rows:
            return f"表 {table_name} 没有数据"
        result = f"表 {table_name} 示例数据 ({len(rows)} 行):\n"
        result += " | ".join(rows[0].keys()) + "\n"
        for row in rows:
            result += " | ".join(str(v) for v in row.values()) + "\n"
        return result
    except Exception as e:
        return f"获取示例数据失败: {str(e)}"


# 所有可用工具列表
ALL_TOOLS = [
    read_database_schema,
    list_tables,
    describe_table,
    execute_sql_query,
    get_table_sample,
]