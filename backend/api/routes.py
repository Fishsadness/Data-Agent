"""
API 路由
提供 RESTful API 和 WebSocket 接口
"""
import json
import logging
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from db.schema import get_all_schemas, get_table_schema, get_sample_data, schema_to_prompt_text
from db.connection import test_connection, execute_readonly
from agent.safety import check_sql_safety, add_row_limit
from agent.sql_agent import query_simple
from analysis.analyzer import analyze_dataframe, suggest_chart_type
from visualization.charts import generate_chart_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["data-agent"])


# ============ 请求/响应模型 ============

class QueryRequest(BaseModel):
    question: str = Field(..., description="自然语言查询问题", min_length=1, max_length=2000)


class SQLExecuteRequest(BaseModel):
    sql: str = Field(..., description="SQL 查询语句", min_length=1, max_length=10000)


class QueryResponse(BaseModel):
    success: bool
    question: str = ""
    sql: str = ""
    columns: list[str] = []
    rows: list[dict] = []
    row_count: int = 0
    answer: str = ""
    chart: dict = {}
    analysis: dict = {}
    elapsed_ms: float = 0
    error: str = ""


# ============ 健康检查 ============

@router.get("/health")
async def health_check():
    """健康检查接口"""
    db_ok = test_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now().isoformat(),
    }


# ============ Schema 接口 ============

@router.get("/schema")
async def get_schema():
    """获取数据库完整 Schema"""
    try:
        schemas = get_all_schemas()
        return {
            "success": True,
            "tables": list(schemas.keys()),
            "schemas": schemas,
            "prompt_text": schema_to_prompt_text(schemas),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{table_name}")
async def get_table_info(table_name: str):
    """获取指定表的详细信息和示例数据"""
    try:
        schema = get_table_schema(table_name)
        sample = get_sample_data(table_name, limit=5)
        return {
            "success": True,
            "table_name": table_name,
            "schema": schema,
            "sample_data": sample,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"表不存在: {table_name}")


# ============ 查询接口 ============

@router.post("/query", response_model=QueryResponse)
async def natural_query(req: QueryRequest):
    """
    自然语言查询 - 核心接口
    输入自然语言，返回 SQL + 数据 + 分析 + 图表
    """
    start_time = time.time()

    result = QueryResponse(
        success=False,
        question=req.question,
    )

    try:
        async for event in query_simple(req.question):
            event_type = event.get("type", "")

            if event_type == "sql":
                result.sql = event["content"]
            elif event_type == "data":
                result.columns = event["columns"]
                result.rows = event["rows"]
                result.row_count = event["row_count"]
            elif event_type == "answer":
                result.answer = event["content"]
            elif event_type == "error":
                result.error = event["content"]
                result.elapsed_ms = (time.time() - start_time) * 1000
                return result

        # 生成图表和分析
        if result.columns and result.rows:
            result.analysis = analyze_dataframe(result.columns, result.rows)
            result.chart = generate_chart_config(
                result.columns, result.rows,
                title=req.question,
            )

        result.success = True
        result.elapsed_ms = round((time.time() - start_time) * 1000, 2)

    except Exception as e:
        logger.error(f"查询失败: {e}", exc_info=True)
        result.error = str(e)
        result.elapsed_ms = (time.time() - start_time) * 1000

    return result


@router.post("/query/stream")
async def natural_query_stream(req: QueryRequest):
    """
    自然语言查询 - 流式响应
    使用 SSE (Server-Sent Events) 逐步返回结果
    """
    async def event_generator():
        try:
            async for event in query_simple(req.question):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============ SQL 直接执行 ============

@router.post("/sql/execute")
async def execute_sql_direct(req: SQLExecuteRequest):
    """直接执行 SQL 查询（需通过安全检查）"""
    safety = check_sql_safety(req.sql)

    if not safety.is_safe:
        raise HTTPException(status_code=400, detail={
            "error": "SQL 安全检查失败",
            "details": safety.errors,
        })

    try:
        safe_sql = add_row_limit(safety.sanitized_sql)
        columns, rows = execute_readonly(safe_sql)
        analysis = analyze_dataframe(columns, rows)
        chart = generate_chart_config(columns, rows)

        return {
            "success": True,
            "sql": safe_sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "analysis": analysis,
            "chart": chart,
            "warnings": safety.warnings,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ WebSocket ============

@router.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """WebSocket 实时查询接口"""
    await websocket.accept()
    logger.info("WebSocket 连接已建立")

    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            question = request.get("question", "")

            if not question:
                await websocket.send_json({"type": "error", "content": "问题不能为空"})
                continue

            await websocket.send_json({"type": "step", "content": "开始处理查询..."})

            async for event in query_simple(question):
                await websocket.send_json(event)

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("WebSocket 连接已断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except Exception:
            pass