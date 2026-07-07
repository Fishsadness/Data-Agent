"""
多Agent协作编排器
Coordinator + Planner + Multi-Agent 模式
"""
import logging
import json
from typing import AsyncGenerator, Optional
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm_client import create_llm

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    PLANNER = "planner"       # 任务规划
    SQL = "sql"                # SQL生成与执行
    ANALYST = "analyst"        # 数据分析
    CHARTER = "charter"        # 图表生成
    REPORTER = "reporter"      # 报告生成
    RAG = "rag"                # 知识检索


@dataclass
class PlanStep:
    """规划步骤"""
    step_id: int
    agent: AgentRole
    description: str
    dependencies: list[int] = field(default_factory=list)
    result: Optional[str] = None


PLANNER_SYSTEM_PROMPT = """你是一位资深的数据分析规划师。

## 你的任务
分析用户的问题，将其分解为多个可执行的步骤，并分配给合适的 Agent。

## 可用的 Agent
- **sql**: 负责 SQL 生成、数据库查询、Schema 读取
- **analyst**: 负责数据分析、统计、趋势解读
- **charter**: 负责图表生成、数据可视化
- **reporter**: 负责报告生成、总结输出
- **rag**: 负责知识库检索、业务知识查询

## 输出格式
返回 JSON 数组，每个元素包含：
- step_id: 步骤编号
- agent: 使用的 agent 名称
- description: 步骤描述
- dependencies: 依赖的前置步骤编号列表

## 示例
用户: "分析今年销量下降的原因并给出建议"
输出:
```json
[
  {"step_id": 1, "agent": "sql", "description": "查询今年和去年的月度销量数据", "dependencies": []},
  {"step_id": 2, "agent": "analyst", "description": "对比分析销量变化趋势，找出下降月份", "dependencies": [1]},
  {"step_id": 3, "agent": "sql", "description": "按地区和品类查询销量明细", "dependencies": [1]},
  {"step_id": 4, "agent": "analyst", "description": "分析哪些地区和品类下降最严重", "dependencies": [3]},
  {"step_id": 5, "agent": "charter", "description": "生成销量趋势图和地区分布图", "dependencies": [2, 4]},
  {"step_id": 6, "agent": "reporter", "description": "综合所有分析结果，生成分析报告和建议", "dependencies": [2, 4, 5]}
]
```

只返回 JSON，不要其他内容。"""


class PlannerAgent:
    """任务规划器 - 将复杂问题分解为多步骤执行计划"""

    def __init__(self):
        self.llm = create_llm(temperature=0.0)

    async def plan(self, question: str) -> list[PlanStep]:
        """根据用户问题生成执行计划"""
        prompt = f"用户问题: {question}\n请生成执行计划。"

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])

            content = response.content.strip()
            # 清理可能的 markdown 代码块
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
            content = content.strip()

            steps_data = json.loads(content)
            return [
                PlanStep(
                    step_id=s["step_id"],
                    agent=AgentRole(s["agent"]),
                    description=s["description"],
                    dependencies=s.get("dependencies", []),
                )
                for s in steps_data
            ]
        except Exception as e:
            logger.error(f"Planner 规划失败: {e}")
            # 降级：直接作为单个 SQL 步骤
            return [PlanStep(step_id=1, agent=AgentRole.SQL, description=question)]


class CoordinatorAgent:
    """
    协调器 - 管理多个 Agent 的执行流程
    支持依赖管理、并行执行、结果聚合
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.results: dict[int, str] = {}

    async def execute(self, question: str) -> AsyncGenerator[dict, None]:
        """
        执行完整的分析流程
        1. Planner 规划步骤
        2. 按依赖关系执行各 Agent
        3. 聚合结果
        """
        # 第一步：规划
        yield {"type": "planning", "content": "正在分析问题，制定执行计划..."}

        steps = await self.planner.plan(question)

        yield {
            "type": "plan",
            "content": f"分析计划: {len(steps)} 个步骤",
            "steps": [
                {"id": s.step_id, "agent": s.agent.value, "desc": s.description}
                for s in steps
            ],
        }

        # 第二步：按依赖关系执行
        completed = set()
        remaining = list(steps)

        while remaining:
            # 找出所有依赖已满足的步骤
            ready = [
                s for s in remaining
                if all(d in completed for d in s.dependencies)
            ]

            if not ready:
                logger.error(f"死锁检测: 剩余步骤 {[s.step_id for s in remaining]}")
                break

            for step in ready:
                yield {
                    "type": "step_start",
                    "step_id": step.step_id,
                    "agent": step.agent.value,
                    "content": step.description,
                }

                # 执行对应 Agent
                result = await self._execute_step(step)
                step.result = result
                self.results[step.step_id] = result
                completed.add(step.step_id)

                yield {
                    "type": "step_complete",
                    "step_id": step.step_id,
                    "agent": step.agent.value,
                    "content": result[:500] if result else "完成",
                }

            remaining = [s for s in remaining if s.step_id not in completed]

        # 第三步：聚合结果
        yield {
            "type": "summary",
            "steps_completed": len(steps),
            "results": self.results,
        }

    async def _execute_step(self, step: PlanStep) -> str:
        """执行单个步骤"""
        # 根据 Agent 类型调用对应模块
        if step.agent == AgentRole.SQL:
            return await self._run_sql_agent(step)
        elif step.agent == AgentRole.ANALYST:
            return await self._run_analyst_agent(step)
        elif step.agent == AgentRole.CHARTER:
            return "图表生成已完成"
        elif step.agent == AgentRole.REPORTER:
            return await self._run_reporter_agent(step)
        elif step.agent == AgentRole.RAG:
            return await self._run_rag_agent(step)
        return "未知 Agent 类型"

    async def _run_sql_agent(self, step: PlanStep) -> str:
        """执行 SQL Agent"""
        from agent.sql_agent import query_simple

        result_parts = []
        async for event in query_simple(step.description):
            if event["type"] == "data":
                result_parts.append(f"查询结果: {event.get('row_count', 0)} 行")
            elif event["type"] == "answer":
                result_parts.append(event["content"])
            elif event["type"] == "error":
                result_parts.append(f"错误: {event['content']}")
        return "\n".join(result_parts) if result_parts else "SQL 查询完成"

    async def _run_analyst_agent(self, step: PlanStep) -> str:
        """执行分析 Agent"""
        from analysis.analyzer import analyze_dataframe
        from db.connection import execute_readonly

        context = self.results.get(step.dependencies[0], "") if step.dependencies else ""
        llm = create_llm(temperature=0.3)

        prompt = f"""你是一位数据分析专家。请根据以下信息分析数据。

上下文:
{context}

分析任务: {step.description}

请给出详细的数据分析，包括：
1. 关键发现
2. 数据趋势
3. 异常点
4. 业务建议"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def _run_reporter_agent(self, step: PlanStep) -> str:
        """执行报告 Agent"""
        llm = create_llm(temperature=0.3)

        context = "\n".join(
            f"步骤{k}: {v}" for k, v in self.results.items()
        )

        prompt = f"""你是一位数据分析报告撰写专家。请根据以下分析结果，撰写一份专业的分析报告。

所有分析结果:
{context}

报告要求: {step.description}

报告格式:
1. 概述
2. 核心发现
3. 数据详情
4. 原因分析
5. 建议措施"""

        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def _run_rag_agent(self, step: PlanStep) -> str:
        """执行 RAG Agent"""
        from knowledge.retriever import search_knowledge
        return search_knowledge(step.description)


# 全局协调器实例
coordinator = CoordinatorAgent()