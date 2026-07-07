"""
Data Agent 核心
基于 LangChain Agent 实现自然语言 -> SQL -> 数据 -> 分析 的完整链路
"""
import logging
from typing import AsyncGenerator, Optional

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from agent.llm_client import create_llm
from agent.tools import ALL_TOOLS
from agent.safety import check_sql_safety
from db.schema import schema_to_prompt_text, get_all_schemas

logger = logging.getLogger(__name__)

# System Prompt - 定义 Agent 的角色和行为
SYSTEM_PROMPT = """你是一位资深的数据分析师和 SQL 专家。

## 你的工作流程
1. **理解需求**：仔细分析用户的自然语言问题
2. **读取 Schema**：使用 read_database_schema 工具了解数据库结构
3. **生成 SQL**：根据 Schema 和用户需求，编写准确的 SQL 查询
4. **执行查询**：使用 execute_sql_query 工具执行 SQL
5. **分析结果**：根据查询结果，用自然语言回答用户的问题

## 重要规则
- 在生成 SQL 之前，必须先调用 read_database_schema 了解表结构
- 只生成 SELECT 查询，禁止任何写操作
- SQL 使用 SQLite 语法
- 查询结果要清晰、有条理地呈现给用户
- 如果用户的问题不明确，先询问澄清再查询
- 使用中文回答用户

## 数据分析能力
- 查询结果出来后，分析数据趋势、对比、排名等
- 可以给出业务建议和洞察
- 如果数据不足以回答用户问题，诚实告知
"""


def create_data_agent():
    """创建 Data Agent 实例"""
    llm = create_llm(temperature=0.0)
    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )
    return agent


async def query_data_agent(question: str) -> AsyncGenerator[dict, None]:
    """
    执行 Data Agent 查询，流式返回结果
    
    Yields:
        dict: {"type": "step", "content": "..."}  - 步骤信息
        dict: {"type": "sql", "content": "..."}    - 生成的 SQL
        dict: {"type": "data", "columns": [...], "rows": [...]}  - 查询数据
        dict: {"type": "answer", "content": "..."}  - 最终回答
        dict: {"type": "error", "content": "..."}  - 错误信息
    """
    try:
        agent = create_data_agent()

        yield {"type": "step", "content": "正在分析您的问题..."}

        # 获取 Schema 信息
        schemas = get_all_schemas()
        schema_text = schema_to_prompt_text(schemas)

        # 构建最终消息
        final_message = f"用户问题: {question}\n\n数据库 Schema:\n{schema_text}"

        # 流式执行 Agent
        messages = []
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=final_message)]},
            version="v2",
        ):
            kind = event.get("event", "")

            if kind == "on_tool_start":
                tool_name = event.get("name", "")
                yield {"type": "step", "content": f"执行工具: {tool_name}..."}

            elif kind == "on_tool_end":
                output = event.get("data", {}).get("output", "")
                if event.get("name") == "execute_sql_query":
                    yield {"type": "sql_result", "content": str(output)}

            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    messages.append(chunk.content)

        # 返回完整回答
        full_answer = "".join(messages)
        if full_answer:
            yield {"type": "answer", "content": full_answer}

    except Exception as e:
        logger.error(f"Agent 执行失败: {e}", exc_info=True)
        yield {"type": "error", "content": f"查询失败: {str(e)}"}


async def query_simple(question: str) -> AsyncGenerator[dict, None]:
    """
    简化版查询 - 直接使用 LLM 生成 SQL 然后执行
    适用于 LangGraph 不可用时的降级方案
    """
    try:
        llm = create_llm(temperature=0.0)
        schemas = get_all_schemas()
        schema_text = schema_to_prompt_text(schemas)

        yield {"type": "step", "content": "正在读取数据库 Schema..."}

        # 生成 SQL
        sql_prompt = f"""你是一位 SQL 专家。根据以下数据库 Schema 和用户问题，生成一条 SQL 查询语句。

数据库 Schema:
{schema_text}

用户问题: {question}

要求:
- 只返回 SQL 语句，不要任何解释
- 不要使用 Markdown 代码块
- 使用 SQLite 语法
- 只生成 SELECT 查询"""

        yield {"type": "step", "content": "正在生成 SQL 查询..."}

        response = await llm.ainvoke([HumanMessage(content=sql_prompt)])
        sql = response.content.strip()

        # 清理 SQL
        import re
        sql = re.sub(r"^```(?:sql)?\s*\n?", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\n?```\s*$", "", sql)

        yield {"type": "sql", "content": sql}

        # 安全检查
        safety = check_sql_safety(sql)
        if not safety.is_safe:
            yield {"type": "error", "content": "\n".join(safety.errors)}
            return

        # 执行 SQL
        yield {"type": "step", "content": "正在执行查询..."}

        from db.connection import execute_readonly
        from agent.safety import add_row_limit

        safe_sql = add_row_limit(safety.sanitized_sql)
        columns, rows = execute_readonly(safe_sql)

        yield {
            "type": "data",
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }

        # LLM 分析结果
        yield {"type": "step", "content": "正在分析查询结果..."}

        if rows:
            # 格式化数据供 LLM 分析
            data_summary = f"查询成功，返回 {len(rows)} 行数据。\n\n"
            data_summary += " | ".join(columns) + "\n"
            for row in rows[:30]:
                values = [str(row.get(col, "")) for col in columns]
                data_summary += " | ".join(values) + "\n"

            analysis_prompt = f"""根据以下查询结果，用中文回答用户的问题。

用户问题: {question}

执行的 SQL:
{sql}

查询结果:
{data_summary}

请分析数据并给出清晰的回答，包括:
1. 直接回答用户的问题
2. 关键数据洞察
3. 如果有值得注意的趋势或异常，请指出"""

            analysis = await llm.ainvoke([HumanMessage(content=analysis_prompt)])
            yield {"type": "answer", "content": analysis.content}
        else:
            yield {"type": "answer", "content": "查询结果为空，请检查查询条件是否正确。"}

    except Exception as e:
        logger.error(f"查询失败: {e}", exc_info=True)
        yield {"type": "error", "content": f"查询失败: {str(e)}"}