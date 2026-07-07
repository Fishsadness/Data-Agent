"""
Python 分析 Agent
支持预测、聚类、异常检测等高级数据分析
"""
import logging
from typing import Optional

from langchain_core.messages import HumanMessage

from agent.llm_client import create_llm

logger = logging.getLogger(__name__)


def generate_analysis_code(question: str, data_description: str) -> str:
    """
    根据用户问题生成 Python 分析代码
    使用 LLM 自动生成分析脚本
    """
    llm = create_llm(temperature=0.0)

    prompt = f"""你是一位 Python 数据分析专家。请根据以下信息生成 Python 代码。

## 数据描述
{data_description}

## 分析需求
{question}

## 要求
- 只返回 Python 代码，不要任何解释
- 不要使用 Markdown 代码块
- 变量 df 是 pandas DataFrame（已存在）
- 使用 numpy、pandas、sklearn（如需要）
- 将分析结果存储在 result 变量中（dict 或 str）
- 如果需要可视化，使用 matplotlib 并保存为 'chart.png'"""

    response = llm.invoke([HumanMessage(content=prompt)])
    code = response.content.strip()

    # 清理代码块标记
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return code


def execute_python_analysis(code: str, df=None) -> dict:
    """
    在沙箱环境中执行 Python 分析代码
    返回执行结果
    """
    import pandas as pd
    import numpy as np

    if df is None:
        df = pd.DataFrame()

    # 创建受限的全局命名空间
    safe_globals = {
        "pd": pd,
        "np": np,
        "df": df,
        "plt": None,
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "list": list,
            "dict": dict,
            "str": str,
            "int": int,
            "float": float,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "sorted": sorted,
            "enumerate": enumerate,
            "zip": zip,
            "isinstance": isinstance,
            "type": type,
            "True": True,
            "False": False,
            "None": None,
        },
    }

    result = {}
    local_vars = {}

    try:
        exec(code, safe_globals, local_vars)
        result["success"] = True
        result["result"] = local_vars.get("result", "代码执行完成，但未设置 result 变量")
        result["output"] = str(local_vars.get("result", ""))
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["output"] = f"执行错误: {e}"

    return result


def detect_anomalies(data: list[dict], column: str, method: str = "zscore") -> dict:
    """
    异常检测
    支持方法: zscore, iqr
    """
    import numpy as np

    values = []
    for row in data:
        v = row.get(column)
        if v is not None:
            try:
                values.append(float(v))
            except (ValueError, TypeError):
                pass

    if not values:
        return {"error": "无有效数据"}

    arr = np.array(values)
    anomalies = []

    if method == "zscore":
        mean = np.mean(arr)
        std = np.std(arr)
        if std > 0:
            z_scores = np.abs((arr - mean) / std)
            anomalies = [
                {"index": i, "value": values[i], "z_score": round(z_scores[i], 2)}
                for i in range(len(values)) if z_scores[i] > 2.0
            ]

    elif method == "iqr":
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        anomalies = [
            {"index": i, "value": values[i]}
            for i in range(len(values))
            if values[i] < lower or values[i] > upper
        ]

    return {
        "method": method,
        "total": len(values),
        "anomaly_count": len(anomalies),
        "anomaly_rate": round(len(anomalies) / len(values) * 100, 2),
        "anomalies": anomalies,
        "stats": {
            "mean": round(float(np.mean(arr)), 2),
            "std": round(float(np.std(arr)), 2),
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
        },
    }


def forecast_simple(data: list[dict], value_col: str, periods: int = 3) -> dict:
    """
    简单预测（移动平均法）
    不需要 sklearn 依赖
    """
    import numpy as np

    values = []
    for row in data:
        v = row.get(value_col)
        if v is not None:
            try:
                values.append(float(v))
            except (ValueError, TypeError):
                pass

    if len(values) < 3:
        return {"error": "数据点不足，至少需要3个数据点"}

    arr = np.array(values)

    # 简单移动平均
    window = min(3, len(arr))
    ma = np.convolve(arr, np.ones(window) / window, mode='valid')

    # 线性趋势
    x = np.arange(len(values))
    z = np.polyfit(x, arr, 1)
    trend = np.poly1d(z)

    forecasts = []
    for i in range(periods):
        next_idx = len(values) + i
        forecasts.append(round(float(trend(next_idx)), 2))

    return {
        "method": "线性趋势预测",
        "historical": values[-3:],
        "forecast": forecasts,
        "trend": "上升" if z[0] > 0 else "下降",
        "slope": round(float(z[0]), 4),
    }