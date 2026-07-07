"""
Data Agent 主入口
启动 FastAPI 服务，初始化数据库
"""
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SERVER_CONFIG, LOG_CONFIG
from db.init_demo import init_demo_db
from db.connection import test_connection
from api.routes import router

# 配置日志
LOG_CONFIG["dir"].mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG["level"]),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_CONFIG["dir"] / "app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Data Agent - 智能数据查询系统",
    description="自然语言驱动的 SQL 生成与数据分析 Agent",
    version="1.0.0",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.on_event("startup")
async def startup():
    """启动时初始化数据库"""
    logger.info("=" * 50)
    logger.info("Data Agent 启动中...")
    logger.info("=" * 50)

    # 初始化 Demo 数据库
    try:
        init_demo_db()
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    # 测试连接
    if test_connection():
        logger.info("数据库连接正常")
    else:
        logger.warning("数据库连接异常，请检查配置")

    logger.info(f"服务地址: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    logger.info(f"API 文档: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}/docs")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Data Agent",
        "version": "1.0.0",
        "description": "智能数据查询系统 - 用自然语言查询数据库",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=SERVER_CONFIG["host"],
        port=SERVER_CONFIG["port"],
        reload=True,
        log_level=LOG_CONFIG["level"].lower(),
    )