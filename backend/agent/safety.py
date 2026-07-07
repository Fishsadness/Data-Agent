"""
SQL 安全校验模块
对 LLM 生成的 SQL 进行多层安全检查，防止危险操作
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from config import SQL_SAFETY

logger = logging.getLogger(__name__)

# 危险关键字 -> 风险说明
FORBIDDEN_PATTERNS = {
    r"\bDROP\b": "DROP 语句禁止执行",
    r"\bDELETE\b": "DELETE 语句禁止执行",
    r"\bUPDATE\b": "UPDATE 语句禁止执行",
    r"\bINSERT\b": "INSERT 语句禁止执行",
    r"\bTRUNCATE\b": "TRUNCATE 语句禁止执行",
    r"\bALTER\b": "ALTER 语句禁止执行",
    r"\bCREATE\b": "CREATE 语句禁止执行",
    r"\bREPLACE\b": "REPLACE 语句禁止执行",
    r"\bGRANT\b": "GRANT 语句禁止执行",
    r"\bREVOKE\b": "REVOKE 语句禁止执行",
    r"\bEXEC\b": "EXEC/EXECUTE 语句禁止执行",
    r"\bEXECUTE\b": "EXEC/EXECUTE 语句禁止执行",
    r"\bATTACH\b": "ATTACH 语句禁止执行",
    r"\bDETACH\b": "DETACH 语句禁止执行",
    r"\bPRAGMA\b": "PRAGMA 语句禁止执行",
}


@dataclass
class SafetyResult:
    """安全检查结果"""
    is_safe: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    sanitized_sql: Optional[str] = None


def clean_sql(sql: str) -> str:
    """
    清理 SQL 文本
    - 移除 Markdown 代码块标记
    - 移除首尾空白
    - 移除末尾分号后的内容
    """
    sql = sql.strip()

    # 移除 Markdown 代码块
    sql = re.sub(r"^```(?:sql)?\s*\n?", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\n?```\s*$", "", sql)

    # 只取第一条 SQL 语句（分号分隔）
    statements = sql.split(";")
    sql = statements[0].strip()

    return sql


def check_sql_safety(sql: str) -> SafetyResult:
    """
    检查 SQL 语句的安全性
    返回 SafetyResult 包含检查结果和清理后的 SQL
    """
    errors = []
    warnings = []

    if not sql or not sql.strip():
        errors.append("SQL 语句为空")
        return SafetyResult(is_safe=False, errors=errors)

    # 清理 SQL
    clean = clean_sql(sql)
    upper_sql = clean.upper()

    # 检查危险关键字
    for pattern, message in FORBIDDEN_PATTERNS.items():
        if re.search(pattern, upper_sql):
            errors.append(f"{message}: 匹配到 {pattern}")

    # 检查是否以 SELECT 开头（只读模式）
    if SQL_SAFETY["readonly"] and not upper_sql.strip().startswith("SELECT"):
        # 允许 WITH (CTE)、EXPLAIN 等
        allowed_prefixes = ("SELECT", "WITH", "EXPLAIN", "DESCRIBE", "DESC", "SHOW", "PRAGMA")
        if not any(upper_sql.strip().startswith(p) for p in allowed_prefixes):
            errors.append("只读模式下只允许 SELECT 查询")

    # 检查 SQL 长度
    if len(clean) > 10000:
        warnings.append("SQL 语句过长，可能影响性能")

    # 检查是否包含 LIMIT（建议）
    if "LIMIT" not in upper_sql and "SELECT" in upper_sql:
        warnings.append("建议添加 LIMIT 限制返回行数")

    is_safe = len(errors) == 0

    return SafetyResult(
        is_safe=is_safe,
        errors=errors,
        warnings=warnings,
        sanitized_sql=clean if is_safe else None,
    )


def add_row_limit(sql: str, max_rows: int = None) -> str:
    """自动为 SQL 添加 LIMIT 限制"""
    if max_rows is None:
        max_rows = SQL_SAFETY["max_rows"]

    clean = clean_sql(sql)
    upper = clean.upper()

    # 已有 LIMIT 则不添加
    if "LIMIT" in upper:
        return clean

    # 在末尾添加 LIMIT
    clean = clean.rstrip(";").strip()
    return f"{clean} LIMIT {max_rows}"