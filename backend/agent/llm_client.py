"""
LLM 客户端
统一管理不同 LLM 提供商的连接
"""
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from config import LLM_CONFIG

logger = logging.getLogger(__name__)


def create_llm(temperature: Optional[float] = None) -> ChatOpenAI:
    """
    创建 LLM 实例
    支持 OpenAI 兼容的 API（包括国内模型代理）
    """
    kwargs = {
        "model": LLM_CONFIG["model"],
        "temperature": temperature if temperature is not None else LLM_CONFIG["temperature"],
    }

    if LLM_CONFIG["api_key"]:
        kwargs["api_key"] = LLM_CONFIG["api_key"]
    if LLM_CONFIG["base_url"]:
        kwargs["base_url"] = LLM_CONFIG["base_url"]

    logger.info(f"创建 LLM: model={kwargs['model']}, temperature={kwargs['temperature']}")

    return ChatOpenAI(**kwargs)


# 全局 LLM 实例 - 延迟初始化
_llm_instance = None


def get_llm() -> ChatOpenAI:
    """获取全局 LLM 实例（延迟初始化）"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = create_llm()
    return _llm_instance