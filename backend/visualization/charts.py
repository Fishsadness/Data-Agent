"""
可视化模块
基于查询结果生成 ECharts 图表配置（JSON 格式），前端直接渲染
"""
import logging
from typing import Any, Optional

from analysis.analyzer import analyze_dataframe, suggest_chart_type

logger = logging.getLogger(__name__)


def generate_chart_config(
    columns: list[str],
    rows: list[dict],
    chart_type: Optional[str] = None,
    title: str = "查询结果",
) -> dict:
    """
    生成 ECharts 图表配置
    返回 JSON 格式的配置对象，前端可直接使用
    """
    if not rows:
        return {"error": "无数据可展示"}

    if chart_type is None:
        chart_type = suggest_chart_type(columns, rows)

    if chart_type == "none":
        return {"error": "数据不足以生成图表"}

    if chart_type == "table":
        return _build_table_config(columns, rows, title)

    analysis = analyze_dataframe(columns, rows)
    num_cols = analysis["numeric_columns"]
    text_cols = analysis["text_columns"]

    if chart_type == "bar":
        return _build_bar_config(columns, rows, text_cols, num_cols, title)
    elif chart_type == "line":
        return _build_line_config(columns, rows, text_cols, num_cols, title)
    elif chart_type == "pie":
        return _build_pie_config(columns, rows, text_cols, num_cols, title)
    else:
        return _build_bar_config(columns, rows, text_cols, num_cols, title)


def _build_table_config(columns: list[str], rows: list[dict], title: str) -> dict:
    """构建表格配置"""
    return {
        "type": "table",
        "title": title,
        "columns": columns,
        "rows": [list(row.values()) for row in rows[:100]],
    }


def _build_bar_config(
    columns: list[str], rows: list[dict],
    text_cols: list[str], num_cols: list[str], title: str
) -> dict:
    """构建柱状图配置"""
    x_col = text_cols[0] if text_cols else columns[0]
    y_col = num_cols[0] if num_cols else columns[-1]

    x_data = [str(row.get(x_col, "")) for row in rows]
    y_data = [float(row.get(y_col, 0) or 0) for row in rows]

    return {
        "type": "bar",
        "title": title,
        "option": {
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "category",
                "data": x_data,
                "axisLabel": {"rotate": 30 if len(x_data) > 8 else 0},
            },
            "yAxis": {"type": "value"},
            "series": [{
                "name": y_col,
                "type": "bar",
                "data": y_data,
                "itemStyle": {
                    "color": {
                        "type": "linear",
                        "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "#667eea"},
                            {"offset": 1, "color": "#764ba2"},
                        ],
                    }
                },
            }],
        },
    }


def _build_line_config(
    columns: list[str], rows: list[dict],
    text_cols: list[str], num_cols: list[str], title: str
) -> dict:
    """构建折线图配置"""
    x_col = text_cols[0] if text_cols else columns[0]
    x_data = [str(row.get(x_col, "")) for row in rows]

    series = []
    colors = ["#667eea", "#f093fb", "#4facfe", "#43e97b", "#fa709a"]
    for i, col in enumerate(num_cols[:5]):
        series.append({
            "name": col,
            "type": "line",
            "data": [float(row.get(col, 0) or 0) for row in rows],
            "smooth": True,
            "itemStyle": {"color": colors[i % len(colors)]},
        })

    return {
        "type": "line",
        "title": title,
        "option": {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": [s["name"] for s in series]},
            "xAxis": {
                "type": "category",
                "data": x_data,
                "axisLabel": {"rotate": 30 if len(x_data) > 8 else 0},
            },
            "yAxis": {"type": "value"},
            "series": series,
        },
    }


def _build_pie_config(
    columns: list[str], rows: list[dict],
    text_cols: list[str], num_cols: list[str], title: str
) -> dict:
    """构建饼图配置"""
    name_col = text_cols[0] if text_cols else columns[0]
    value_col = num_cols[0] if num_cols else columns[-1]

    data = [
        {"name": str(row.get(name_col, "")), "value": float(row.get(value_col, 0) or 0)}
        for row in rows
    ]

    return {
        "type": "pie",
        "title": title,
        "option": {
            "tooltip": {"trigger": "item"},
            "legend": {"type": "scroll", "orient": "vertical", "right": 10, "top": 20, "bottom": 20},
            "series": [{
                "name": value_col,
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["40%", "50%"],
                "data": data,
                "emphasis": {
                    "itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0,0,0,0.5)"},
                },
            }],
        },
    }