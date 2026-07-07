"""
RAG 知识库检索模块
结合向量检索和关键词匹配，为数据分析提供业务上下文
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 知识库路径
KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge"

# 业务知识库 - 产品信息、行业术语、业务规则
BUSINESS_KNOWLEDGE = {
    "products": {
        "1001": "iPhone 15 Pro - 苹果旗舰手机，A17 Pro芯片，钛金属设计",
        "1002": "MacBook Air M3 - 轻薄笔记本，M3芯片，15英寸",
        "1003": "AirPods Pro - 主动降噪耳机，H2芯片",
        "1004": "iPad Air - 轻薄平板，M2芯片",
        "1005": "Apple Watch S9 - 智能手表，S9芯片",
        "1006": "Sony WH-1000XM5 - 索尼旗舰降噪耳机",
        "1007": "Dell XPS 15 - 高性能商务笔记本",
        "1008": "Samsung Galaxy S24 - 三星旗舰手机",
        "1009": "Logitech MX Master 3S - 高端办公鼠标",
        "1010": "机械键盘 K8 Pro - 客制化机械键盘",
        "1011": "4K 显示器 27寸 - 专业设计显示器",
        "1012": "Type-C 扩展坞 - 多功能扩展坞",
        "1013": "华为 Mate 60 Pro - 华为旗舰手机",
        "1014": "小米 14 Ultra - 小米旗舰手机",
        "1015": "ThinkPad X1 Carbon - 联想商务笔记本",
    },
    "categories": {
        "手机": "智能手机品类，包括各品牌旗舰机型，竞争激烈",
        "电脑": "笔记本电脑品类，包括轻薄本和商务本",
        "耳机": "音频设备品类，包括TWS和头戴式",
        "平板": "平板电脑品类，以iPad为主",
        "手表": "智能手表品类，健康监测功能",
        "配件": "电脑外设和配件品类",
    },
    "business_rules": {
        "季节规律": "电子产品销售旺季在Q3-Q4，Q1受春节影响，Q2相对平稳",
        "促销节点": "618、双11、双12、年货节为主要促销节点",
        "复购周期": "手机平均换机周期18-24个月，电脑36-48个月，配件12个月",
        "价格敏感": "配件类价格弹性大，旗舰手机价格弹性小",
    },
    "metrics_definition": {
        "销量": "订单中 quantity 字段的总和",
        "销售额": "订单中 total_price 字段的总和",
        "客单价": "销售额 / 订单数",
        "复购率": "购买超过1次的用户数 / 总用户数",
    },
}


def init_knowledge_base():
    """初始化知识库文件"""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    knowledge_file = KNOWLEDGE_DIR / "business_knowledge.json"
    if not knowledge_file.exists():
        with open(knowledge_file, "w", encoding="utf-8") as f:
            json.dump(BUSINESS_KNOWLEDGE, f, ensure_ascii=False, indent=2)
        logger.info(f"知识库已初始化: {knowledge_file}")


def load_knowledge() -> dict:
    """加载知识库"""
    knowledge_file = KNOWLEDGE_DIR / "business_knowledge.json"
    if knowledge_file.exists():
        with open(knowledge_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return BUSINESS_KNOWLEDGE


def search_knowledge(query: str, top_k: int = 5) -> str:
    """
    搜索知识库 - 简单的关键词匹配 + 语义理解
    返回相关的业务知识片段
    """
    knowledge = load_knowledge()
    query_lower = query.lower()
    results = []

    # 产品信息检索
    for pid, desc in knowledge.get("products", {}).items():
        if any(word in query_lower for word in desc.lower().split()):
            results.append(f"[产品信息] {desc}")

    # 品类检索
    for cat, desc in knowledge.get("categories", {}).items():
        if cat in query:
            results.append(f"[品类信息] {cat}: {desc}")

    # 业务规则检索
    keywords_map = {
        "季节": "季节规律",
        "促销": "促销节点",
        "复购": "复购周期",
        "价格": "价格敏感",
        "换机": "复购周期",
    }
    for kw, rule_key in keywords_map.items():
        if kw in query:
            rule = knowledge.get("business_rules", {}).get(rule_key)
            if rule:
                results.append(f"[业务规则] {rule}")

    # 指标定义检索
    for metric, definition in knowledge.get("metrics_definition", {}).items():
        if metric in query:
            results.append(f"[指标定义] {metric}: {definition}")

    if not results:
        return "未找到相关知识库信息"

    return "\n".join(results[:top_k])


def get_knowledge_context(query: str) -> str:
    """
    获取知识库上下文，用于增强 LLM Prompt
    """
    knowledge = search_knowledge(query)
    return f"""## 业务知识库
{knowledge}

请结合以上业务知识分析数据。"""


if __name__ == "__main__":
    init_knowledge_base()
    print(search_knowledge("iPhone销量下降"))
    print("---")
    print(search_knowledge("促销活动"))
    print("---")
    print(search_knowledge("客单价"))