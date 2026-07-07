"""
Data Agent 配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库配置 - 默认使用 SQLite（演示用），可切换为 MySQL/PostgreSQL
DATABASE_URL = os.getenv(
    "DATA_AGENT_DB_URL",
    f"sqlite:///{BASE_DIR / 'data' / 'demo.db'}"
)

# LLM 配置
LLM_CONFIG = {
    "model": os.getenv("DATA_AGENT_LLM_MODEL", "gpt-4o"),
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "base_url": os.getenv("OPENAI_BASE_URL", ""),
    "temperature": 0.0,  # SQL 生成需要确定性
}

# 安全配置
SQL_SAFETY = {
    "readonly": True,                          # 只读模式
    "forbidden_keywords": [                    # 禁止的关键字
        "DROP", "DELETE", "UPDATE", "INSERT",
        "TRUNCATE", "ALTER", "CREATE", "REPLACE",
        "GRANT", "REVOKE", "EXEC", "EXECUTE",
    ],
    "max_query_timeout": 30,                   # 查询超时（秒）
    "max_rows": 10000,                         # 最大返回行数
}

# 服务配置
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": int(os.getenv("DATA_AGENT_PORT", "8002")),
}

# 日志配置
LOG_CONFIG = {
    "level": os.getenv("DATA_AGENT_LOG_LEVEL", "INFO"),
    "dir": BASE_DIR / "data" / "logs",
}