"""
BI 报告生成器
自动生成分析报告、导出多种格式
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage

from agent.llm_client import create_llm

logger = logging.getLogger(__name__)

REPORT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "reports"


def generate_report(
    question: str,
    analysis_results: str,
    chart_data: dict = None,
    format: str = "markdown",
) -> str:
    """
    生成分析报告
    """
    llm = create_llm(temperature=0.3)

    prompt = f"""你是一位资深的数据分析报告撰写专家。请根据以下信息生成一份专业的分析报告。

## 分析问题
{question}

## 分析结果
{analysis_results}

## 报告格式要求
请生成一份结构化的分析报告，包含以下章节：

1. **报告摘要** - 一段话概括核心发现
2. **关键指标** - 列出最重要的数据指标
3. **详细分析** - 深入分析数据
4. **原因分析** - 解释数据背后的原因
5. **趋势判断** - 预测未来趋势
6. **建议措施** - 给出可操作的建议

使用 Markdown 格式，包含表格和必要的强调。"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def generate_dashboard_config(analysis_data: dict) -> dict:
    """
    自动生成 Dashboard 配置
    返回多个图表的配置数组
    """
    from visualization.charts import generate_chart_config

    dashboards = []

    # 根据分析数据生成多个图表
    if "columns" in analysis_data and "rows" in analysis_data:
        cols = analysis_data["columns"]
        rows = analysis_data["rows"]

        # 柱状图
        bar_chart = generate_chart_config(cols, rows, "bar", "数据概览")
        dashboards.append(bar_chart)

        # 饼图（如果数据适合）
        if len(rows) <= 10:
            pie_chart = generate_chart_config(cols, rows, "pie", "占比分布")
            dashboards.append(pie_chart)

    return {
        "title": "数据分析仪表盘",
        "generated_at": datetime.now().isoformat(),
        "charts": dashboards,
    }


def export_report(report_content: str, format: str = "markdown") -> str:
    """
    导出报告到文件
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.{format}"

    if format == "markdown":
        filename = f"report_{timestamp}.md"
    elif format == "html":
        filename = f"report_{timestamp}.html"
    elif format == "json":
        filename = f"report_{timestamp}.json"

    filepath = REPORT_DIR / filename

    if format == "html":
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>数据分析报告</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 2rem; color: #3b2208; background: #f5e6d3; }}
        h1 {{ border-bottom: 2px solid #8b4513; padding-bottom: 0.5rem; }}
        h2 {{ color: #8b4513; margin-top: 2rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #8b4513; padding: 0.5rem; text-align: left; }}
        th {{ background: #eedbc2; }}
    </style>
</head>
<body>
{report_content}
</body>
</html>"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
    elif format == "json":
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"content": report_content, "generated_at": timestamp}, f, ensure_ascii=False, indent=2)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_content)

    return str(filepath)


def generate_insights(analysis_data: dict) -> list[str]:
    """
    自动生成数据洞察
    """
    from analysis.analyzer import analyze_dataframe

    insights = []

    if "columns" in analysis_data and "rows" in analysis_data:
        stats = analyze_dataframe(analysis_data["columns"], analysis_data["rows"])

        # 数值列洞察
        for col, stat in stats.get("stats", {}).items():
            if "avg" in stat:
                if stat["max"] > stat["avg"] * 3:
                    insights.append(
                        f"注意: {col} 的最大值 ({stat['max']}) 远超平均值 ({stat['avg']})，可能存在异常值"
                    )
                if stat["min"] < 0 and stat["avg"] > 0:
                    insights.append(f"注意: {col} 存在负值，需检查数据质量")

        # 文本列洞察
        for col, stat in stats.get("stats", {}).items():
            if "top_values" in stat and stat["unique_count"] > 10:
                top = stat["top_values"][0]
                insights.append(
                    f"'{col}' 列中 '{top['value']}' 出现频率最高 ({top['count']} 次)，"
                    f"共 {stat['unique_count']} 个不同的值"
                )

    return insights