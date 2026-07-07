"""
数据分析模块
对查询结果进行统计分析，计算汇总指标
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def analyze_dataframe(columns: list[str], rows: list[dict]) -> dict:
    """
    对查询结果进行基础统计分析
    返回统计摘要信息
    """
    if not rows:
        return {"summary": "无数据", "stats": {}}

    numeric_cols = []
    text_cols = []

    # 识别数值列和文本列
    for col in columns:
        values = [row.get(col) for row in rows if row.get(col) is not None]
        if not values:
            continue
        sample = values[0]
        if isinstance(sample, (int, float)):
            numeric_cols.append(col)
        else:
            try:
                float(str(sample))
                numeric_cols.append(col)
            except (ValueError, TypeError):
                text_cols.append(col)

    stats = {}

    for col in numeric_cols:
        values = []
        for row in rows:
            v = row.get(col)
            if v is not None:
                try:
                    values.append(float(v))
                except (ValueError, TypeError):
                    pass

        if values:
            values.sort()
            n = len(values)
            stats[col] = {
                "count": n,
                "sum": round(sum(values), 2),
                "avg": round(sum(values) / n, 2),
                "min": round(values[0], 2),
                "max": round(values[-1], 2),
                "median": round(values[n // 2], 2),
            }

    for col in text_cols:
        values = [row.get(col) for row in rows if row.get(col) is not None]
        if values:
            # 统计频次
            freq = {}
            for v in values:
                v_str = str(v)
                freq[v_str] = freq.get(v_str, 0) + 1
            top_items = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
            stats[col] = {
                "unique_count": len(freq),
                "top_values": [{"value": k, "count": v} for k, v in top_items],
            }

    return {
        "row_count": len(rows),
        "column_count": len(columns),
        "numeric_columns": numeric_cols,
        "text_columns": text_cols,
        "stats": stats,
    }


def suggest_chart_type(columns: list[str], rows: list[dict]) -> str:
    """
    根据数据特征推荐图表类型
    """
    analysis = analyze_dataframe(columns, rows)

    num_count = len(analysis["numeric_columns"])
    text_count = len(analysis["text_columns"])
    row_count = analysis["row_count"]

    if row_count == 0:
        return "none"

    # 1个文本列 + 1个数值列 -> 柱状图
    if text_count >= 1 and num_count >= 1 and row_count <= 20:
        return "bar"

    # 多个数值列 -> 可以选择折线图或雷达图
    if num_count >= 2 and text_count >= 1 and row_count <= 30:
        return "line"

    # 1个文本列 + 1个数值列 -> 饼图（适合占比）
    if text_count >= 1 and num_count == 1 and row_count <= 10:
        total = sum(float(row.get(analysis["numeric_columns"][0], 0) or 0) for row in rows)
        if total > 0:
            return "pie"

    # 表格最适合大量数据
    if row_count > 20:
        return "table"

    return "bar"