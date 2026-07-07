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
from agent.planner import coordinator
from agent.optimizer import optimize_sql, analyze_sql, recommend_indexes
from agent.python_agent import detect_anomalies, forecast_simple
from agent.report_agent import generate_report, generate_dashboard_config, export_report, generate_insights
from agent.alert_agent import alert_manager, scheduled_analyzer
from knowledge.retriever import search_knowledge, get_knowledge_context, init_knowledge_base
from security.permissions import security, create_token, verify_token
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


# ============ 多Agent协作接口 ============

class PlanRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@router.post("/agent/plan")
async def agent_plan(req: PlanRequest):
    """多Agent协作规划 - Planner 分解任务"""
    steps = await coordinator.planner.plan(req.question)
    return {
        "success": True,
        "question": req.question,
        "steps": [
            {"id": s.step_id, "agent": s.agent.value, "description": s.description}
            for s in steps
        ],
    }


@router.post("/agent/plan/stream")
async def agent_plan_stream(req: PlanRequest):
    """多Agent协作 - 流式执行完整流程"""
    async def event_generator():
        async for event in coordinator.execute(req.question):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============ SQL优化接口 ============

class OptimizeRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=10000)
    auto_fix: bool = False


@router.post("/sql/optimize")
async def sql_optimize(req: OptimizeRequest):
    """SQL 优化分析"""
    result = optimize_sql(req.sql, auto_fix=req.auto_fix)
    return {
        "success": True,
        "original": result["original_sql"],
        "optimized": result["optimized_sql"],
        "suggestions": result["suggestions"],
        "has_warnings": result["has_warnings"],
        "has_improvements": result["has_improvements"],
    }


@router.post("/sql/analyze")
async def sql_analyze(req: OptimizeRequest):
    """SQL 分析（含建议索引）"""
    suggestions = analyze_sql(req.sql)
    indexes = recommend_indexes(req.sql)
    return {
        "success": True,
        "sql": req.sql,
        "suggestions": suggestions,
        "recommended_indexes": indexes,
    }


# ============ RAG知识库接口 ============

@router.get("/knowledge/search")
async def knowledge_search(q: str = ""):
    """搜索知识库"""
    if not q:
        return {"success": False, "error": "缺少查询参数 q"}
    result = search_knowledge(q)
    context = get_knowledge_context(q)
    return {
        "success": True,
        "query": q,
        "results": result,
        "context": context,
    }


@router.post("/knowledge/init")
async def knowledge_init():
    """初始化知识库"""
    init_knowledge_base()
    return {"success": True, "message": "知识库已初始化"}


# ============ 分析接口 ============

class AnomalyRequest(BaseModel):
    data: list[dict]
    column: str
    method: str = "zscore"


@router.post("/analysis/anomaly")
async def anomaly_detection(req: AnomalyRequest):
    """异常检测"""
    result = detect_anomalies(req.data, req.column, req.method)
    return {"success": True, **result}


class ForecastRequest(BaseModel):
    data: list[dict]
    value_col: str
    periods: int = 3


@router.post("/analysis/forecast")
async def forecast_data(req: ForecastRequest):
    """数据预测"""
    result = forecast_simple(req.data, req.value_col, req.periods)
    return {"success": True, **result}


# ============ 报告接口 ============

class ReportRequest(BaseModel):
    question: str
    analysis_results: str
    format: str = "markdown"


@router.post("/report/generate")
async def report_generate(req: ReportRequest):
    """生成分析报告"""
    content = generate_report(req.question, req.analysis_results)
    return {"success": True, "content": content, "format": req.format}


@router.post("/report/export")
async def report_export(req: ReportRequest):
    """导出报告"""
    content = generate_report(req.question, req.analysis_results)
    filepath = export_report(content, req.format)
    return {"success": True, "filepath": filepath, "format": req.format}


@router.post("/report/dashboard")
async def report_dashboard(data: dict):
    """生成Dashboard配置"""
    config = generate_dashboard_config(data)
    return {"success": True, "dashboard": config}


@router.post("/report/insights")
async def report_insights(data: dict):
    """生成数据洞察"""
    insights = generate_insights(data)
    return {"success": True, "insights": insights}


# ============ 告警接口 ============

@router.get("/alert/check")
async def alert_check():
    """执行告警检查"""
    alerts = alert_manager.check_all()
    return {"success": True, "alerts": alerts, "count": len(alerts)}


@router.get("/alert/daily")
async def alert_daily():
    """每日巡检"""
    results = scheduled_analyzer.run_daily_check()
    return {"success": True, **results}


@router.get("/alert/trend")
async def alert_trend(metric: str = "orders", days: int = 7):
    """趋势分析"""
    result = scheduled_analyzer.analyze_trend(metric, days)
    return {"success": True, **result}


# ============ 权限接口 ============

class LoginRequest(BaseModel):
    username: str


@router.post("/auth/login")
async def auth_login(req: LoginRequest):
    """用户登录"""
    user = security.get_user(req.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    token = create_token(req.username)
    return {
        "success": True,
        "token": token,
        "user": {
            "username": user.username,
            "role": user.role.value,
            "department": user.department,
        },
    }


@router.get("/auth/me")
async def auth_me(token: str = ""):
    """获取当前用户信息"""
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Token 无效")
    user = security.get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    perm = security.get_permission(user)
    return {
        "success": True,
        "user": {
            "username": user.username,
            "role": user.role.value,
            "department": user.department,
        },
        "permissions": {
            "allowed_tables": perm.allowed_tables,
            "forbidden_tables": perm.forbidden_tables,
            "require_masking": perm.require_masking,
        },
    }