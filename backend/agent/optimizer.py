"""
SQL 优化器
自动优化 LLM 生成的 SQL，提升查询效率
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _rewrite_function_where(sql: str) -> Optional[str]:
    """重写 WHERE 中的函数调用为范围查询"""
    # YEAR(date_col) = 2025 -> date_col >= '2025-01-01' AND date_col < '2026-01-01'
    year_match = re.search(
        r"YEAR\s*\(\s*(\w+)\s*\)\s*=\s*(\d{4})",
        sql, re.IGNORECASE
    )
    if year_match:
        col, year = year_match.group(1), year_match.group(2)
        old = year_match.group(0)
        new = f"{col} >= '{year}-01-01' AND {col} < '{int(year)+1}-01-01'"
        return sql.replace(old, new)

    # MONTH(date_col) = 6 -> date_col >= '2025-06-01' AND date_col < '2025-07-01'
    month_match = re.search(
        r"MONTH\s*\(\s*(\w+)\s*\)\s*=\s*(\d{1,2})",
        sql, re.IGNORECASE
    )
    if month_match:
        col, month = month_match.group(1), month_match.group(2).zfill(2)
        old = month_match.group(0)
        new = f"strftime('%m', {col}) = '{month}'"
        return sql.replace(old, new)

    return None


# SQL 优化规则
OPTIMIZATION_RULES = [
    # 规则1: 避免 SELECT *
    {
        "pattern": r"SELECT\s+\*\s+FROM",
        "check": lambda sql: bool(re.search(r"SELECT\s+\*\s+FROM", sql, re.IGNORECASE)),
        "suggestion": "建议明确指定需要的列，避免 SELECT *",
        "severity": "warning",
    },
    # 规则2: 避免在 WHERE 中使用函数包裹列
    {
        "pattern": r"WHERE\s+(?:YEAR|MONTH|DAY|DATE_FORMAT|UPPER|LOWER|TRIM)\s*\(",
        "check": lambda sql: bool(re.search(
            r"WHERE\s+(?:YEAR|MONTH|DAY|DATE_FORMAT|UPPER|LOWER|TRIM)\s*\(",
            sql, re.IGNORECASE
        )),
        "suggestion": "避免在 WHERE 子句中对列使用函数，这会导致索引失效。建议使用范围查询代替",
        "severity": "warning",
        "rewrite": _rewrite_function_where,
    },
    # 规则3: LIKE 前缀模糊匹配
    {
        "pattern": r"LIKE\s+['\"]%",
        "check": lambda sql: bool(re.search(r"LIKE\s+['\"]%", sql, re.IGNORECASE)),
        "suggestion": "LIKE 以 % 开头会导致全表扫描，建议使用全文索引或调整查询逻辑",
        "severity": "warning",
    },
    # 规则4: 大表 JOIN 建议
    {
        "pattern": r"JOIN",
        "check": lambda sql: bool(re.search(r"\bJOIN\b", sql, re.IGNORECASE)),
        "suggestion": "多表 JOIN 时确保连接字段上有索引",
        "severity": "info",
    },
    # 规则5: 缺少 LIMIT
    {
        "pattern": r"LIMIT",
        "check": lambda sql: "LIMIT" not in sql.upper() and "SELECT" in sql.upper(),
        "suggestion": "建议添加 LIMIT 限制返回行数，避免返回过多数据",
        "severity": "info",
        "rewrite": lambda sql: sql.rstrip(";").strip() + " LIMIT 1000",
    },
    # 规则6: OR 条件优化
    {
        "pattern": r"\bOR\b",
        "check": lambda sql: bool(re.search(r"\bOR\b", sql, re.IGNORECASE)),
        "suggestion": "多个 OR 条件可能导致索引失效，考虑使用 UNION ALL 或 IN 替代",
        "severity": "info",
    },
    # 规则7: 子查询优化
    {
        "pattern": r"IN\s*\(\s*SELECT",
        "check": lambda sql: bool(re.search(r"IN\s*\(\s*SELECT", sql, re.IGNORECASE)),
        "suggestion": "IN 子查询可能效率低下，考虑使用 JOIN 或 EXISTS 替代",
        "severity": "info",
    },
    # 规则8: 隐式类型转换
    {
        "pattern": r"=\s*['\"]\d+['\"]",
        "check": lambda sql: bool(re.search(r"=\s*['\"]\d+['\"]", sql, re.IGNORECASE)),
        "suggestion": "数字类型字段应使用数字比较，避免隐式类型转换",
        "severity": "warning",
    },
]


def analyze_sql(sql: str) -> list[dict]:
    """
    分析 SQL 语句，返回优化建议列表
    """
    suggestions = []

    for rule in OPTIMIZATION_RULES:
        try:
            if rule["check"](sql):
                suggestion = {
                    "severity": rule["severity"],
                    "message": rule["suggestion"],
                }
                if "rewrite" in rule:
                    rewritten = rule["rewrite"](sql)
                    if rewritten and rewritten != sql:
                        suggestion["rewritten_sql"] = rewritten
                suggestions.append(suggestion)
        except Exception as e:
            logger.debug(f"规则检查失败: {e}")

    return suggestions


def optimize_sql(sql: str, auto_fix: bool = False) -> dict:
    """
    优化 SQL 语句
    返回优化后的 SQL 和建议列表
    """
    suggestions = analyze_sql(sql)
    optimized = sql

    if auto_fix:
        for rule in OPTIMIZATION_RULES:
            if "rewrite" in rule and rule["check"](sql):
                rewritten = rule["rewrite"](sql)
                if rewritten and rewritten != optimized:
                    optimized = rewritten

    return {
        "original_sql": sql,
        "optimized_sql": optimized,
        "suggestions": suggestions,
        "has_warnings": any(s["severity"] == "warning" for s in suggestions),
        "has_improvements": optimized != sql,
    }


def generate_explain_sql(sql: str) -> str:
    """生成 EXPLAIN 查询计划"""
    return f"EXPLAIN QUERY PLAN {sql}"


def recommend_indexes(sql: str, schema_info: dict = None) -> list[str]:
    """
    根据 SQL 语句推荐索引
    """
    indexes = []
    sql_upper = sql.upper()

    # WHERE 条件中的列建议加索引
    where_match = re.search(r"WHERE\s+(.+?)(?:GROUP BY|ORDER BY|LIMIT|$)", sql_upper)
    if where_match:
        conditions = where_match.group(1)
        # 查找 = 比较的列
        eq_cols = re.findall(r"(\w+)\s*=\s*", conditions)
        for col in eq_cols:
            if col.upper() not in ("ID", "TRUE", "FALSE", "NULL"):
                indexes.append(f"CREATE INDEX idx_{col.lower()} ON table_name ({col})")

    # JOIN 列建议加索引
    join_match = re.findall(r"ON\s+\w+\.(\w+)\s*=\s*\w+\.(\w+)", sql_upper)
    for col1, col2 in join_match:
        indexes.append(f"CREATE INDEX idx_{col1.lower()} ON table_name ({col1})")

    # ORDER BY 列建议加索引
    order_match = re.search(r"ORDER BY\s+(.+?)(?:LIMIT|$)", sql_upper)
    if order_match:
        order_cols = re.findall(r"(\w+)", order_match.group(1))
        for col in order_cols:
            if col.upper() not in ("DESC", "ASC"):
                indexes.append(f"CREATE INDEX idx_{col.lower()}_order ON table_name ({col})")

    return list(set(indexes))