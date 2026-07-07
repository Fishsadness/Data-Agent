"""
自动告警与定时分析
支持异常检测、定时巡检、多渠道通知
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from langchain_core.messages import HumanMessage

from agent.llm_client import create_llm
from db.connection import execute_readonly

logger = logging.getLogger(__name__)


class AlertRule:
    """告警规则"""

    def __init__(self, name: str, sql: str, threshold: dict, severity: str = "warning"):
        self.name = name
        self.sql = sql
        self.threshold = threshold  # {"field": "value", "operator": ">", "value": 100}
        self.severity = severity  # info, warning, critical


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: list[AlertRule] = []
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认告警规则"""
        self.rules = [
            AlertRule(
                name="销量骤降",
                sql="SELECT COUNT(*) as cnt FROM orders WHERE create_time >= date('now', '-1 day')",
                threshold={"field": "cnt", "operator": "<", "value": 5},
                severity="warning",
            ),
            AlertRule(
                name="订单暴涨",
                sql="SELECT COUNT(*) as cnt FROM orders WHERE create_time >= date('now', '-1 day')",
                threshold={"field": "cnt", "operator": ">", "value": 100},
                severity="info",
            ),
            AlertRule(
                name="零销量商品",
                sql="SELECT COUNT(*) as cnt FROM products p WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.product_id = p.id AND o.create_time >= date('now', '-30 days'))",
                threshold={"field": "cnt", "operator": ">", "value": 0},
                severity="warning",
            ),
        ]

    def check_all(self) -> list[dict]:
        """执行所有告警规则检查"""
        alerts = []

        for rule in self.rules:
            try:
                columns, rows = execute_readonly(rule.sql)
                if not rows:
                    continue

                value = rows[0].get(rule.threshold["field"])
                if value is None:
                    continue

                triggered = False
                op = rule.threshold["operator"]
                threshold = rule.threshold["value"]

                if op == ">" and float(value) > threshold:
                    triggered = True
                elif op == "<" and float(value) < threshold:
                    triggered = True
                elif op == ">=" and float(value) >= threshold:
                    triggered = True
                elif op == "<=" and float(value) <= threshold:
                    triggered = True
                elif op == "==" and float(value) == threshold:
                    triggered = True

                if triggered:
                    alerts.append({
                        "rule": rule.name,
                        "severity": rule.severity,
                        "value": value,
                        "threshold": threshold,
                        "operator": op,
                        "time": datetime.now().isoformat(),
                    })

            except Exception as e:
                logger.error(f"告警规则 [{rule.name}] 检查失败: {e}")

        return alerts

    def add_rule(self, rule: AlertRule):
        """添加自定义告警规则"""
        self.rules.append(rule)


class ScheduledAnalyzer:
    """
    定时分析器
    支持每日/每周自动巡检
    """

    def __init__(self):
        self.alert_manager = AlertManager()

    def run_daily_check(self) -> dict:
        """
        每日巡检
        检查关键指标是否异常
        """
        results = {
            "time": datetime.now().isoformat(),
            "alerts": [],
            "summary": "",
        }

        # 执行告警检查
        results["alerts"] = self.alert_manager.check_all()

        # 生成巡检摘要
        if results["alerts"]:
            critical = [a for a in results["alerts"] if a["severity"] == "critical"]
            warnings = [a for a in results["alerts"] if a["severity"] == "warning"]
            results["summary"] = f"发现 {len(critical)} 个严重告警, {len(warnings)} 个警告"
        else:
            results["summary"] = "所有指标正常"

        return results

    def analyze_trend(self, metric: str, days: int = 7) -> dict:
        """
        趋势分析
        对比过去N天的数据变化
        """
        columns, rows = execute_readonly(f"""
            SELECT date(create_time) as day, COUNT(*) as cnt
            FROM orders
            WHERE create_time >= date('now', '-{days} days')
            GROUP BY date(create_time)
            ORDER BY day
        """)

        if len(rows) < 2:
            return {"trend": "数据不足", "change": 0}

        # 计算趋势
        first_half = sum(r["cnt"] for r in rows[:len(rows)//2])
        second_half = sum(r["cnt"] for r in rows[len(rows)//2:])

        if first_half == 0:
            change = 100 if second_half > 0 else 0
        else:
            change = round((second_half - first_half) / first_half * 100, 2)

        return {
            "metric": metric,
            "days": days,
            "first_half_avg": round(first_half / (len(rows)//2), 2),
            "second_half_avg": round(second_half / (len(rows) - len(rows)//2), 2),
            "change_pct": change,
            "trend": "上升" if change > 5 else ("下降" if change < -5 else "平稳"),
            "data": [{"day": r["day"], "count": r["cnt"]} for r in rows],
        }


# 全局实例
alert_manager = AlertManager()
scheduled_analyzer = ScheduledAnalyzer()