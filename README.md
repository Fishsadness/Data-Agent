# Data Agent — 企业级智能数据分析平台

> 自然语言驱动的 SQL 生成与数据分析 Agent。用户用中文提问，系统自动理解需求、规划任务、查询多数据源、结合知识库分析结果，最终生成图表与报告。

---

## 与传统 BI 的对比

| 维度 | 传统 BI / Chatbot | Data Agent |
|------|------------------|------------|
| 交互方式 | 手动拖拽报表 / 固定问答 | 自然语言自由提问 |
| 查询能力 | 预设 SQL 模板 | LLM 自动生成 SQL |
| 数据理解 | 人工分析图表 | Agent 自动解读趋势、异常、原因 |
| 多步骤分析 | 需要多次手动操作 | Planner 自动分解任务、编排执行 |
| 知识融合 | 纯数据呈现 | 数据库 + 业务知识库联合 |
| 输出形式 | 单一图表 | 图表 + 分析报告 + 洞察 + 建议 |
| 安全管控 | 依赖数据库权限 | 多层安全 + 角色权限 + 数据脱敏 |

核心区别：**Data Agent 不只是"查出数据"，而是"理解数据并给出分析结论"**。

---

## 系统架构

```
                          用户
                            │
                 自然语言 / API / WebSocket
                            │
                 ┌─────────────────────┐
                 │   Planner Agent     │  ← 任务规划与分解
                 └─────────────────────┘
                            │
     ┌──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼
  SQL Agent    RAG Agent    Python Agent   Report Agent
     │              │              │              │
     ▼              ▼              ▼              ▼
  SQL优化      知识检索      数据分析/预测     报告生成
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                            │
                  安全校验 + 权限控制
                            │
     ┌──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼
  SQLite/MySQL  PostgreSQL   ClickHouse     知识库
                            │
                            ▼
                  图表生成 + 报告导出
                            │
                            ▼
            Web 前端 / 企业微信 / 钉钉 / 邮件
```

**六层架构：**

```
用户层        Web 前端 / API / WebSocket
  │
Agent 编排层   Planner + Coordinator 多Agent协作
  │
工具层        SQL生成 / 知识检索 / Python分析 / 报告生成
  │
安全层        SQL安全检查 / 角色权限 / 数据脱敏
  │
数据层        SQLite / MySQL / PostgreSQL / ClickHouse
  │
展示层        ECharts图表 / 分析报告 / Dashboard
```

---

## 核心功能

### 1. 自然语言查询（核心）
```
用户: "查询2025年销量最高的10个商品"

系统内部流程:
  LLM 理解需求 → 读取 Schema → 生成 SQL → 安全检查 → 执行查询
  → 数据分析 → 自动图表 → LLM 解读结果 → 返回回答
```

### 2. 多 Agent 协作（Planner + Coordinator）
- **Planner Agent**：将复杂问题分解为多步骤执行计划
- **Coordinator**：管理依赖关系，调度 SQL / RAG / Python / Report 各 Agent
- 支持流式执行，实时展示每个步骤的进度

### 3. SQL 智能优化
- 8 条自动优化规则（函数包裹列、SELECT *、LIKE 前缀模糊、OR 条件等）
- 自动重写低效 SQL（如 `YEAR(create_time)=2025` → 范围查询）
- 索引推荐（WHERE / JOIN / ORDER BY 列）
- EXPLAIN 执行计划分析

### 4. RAG 知识库
- 产品信息、品类定义、业务规则、指标说明四大类知识
- 查询时自动检索相关知识，增强 LLM 分析上下文
- 支持 JSON 格式自定义知识库

### 5. Python 高级分析
- 异常检测（Z-Score / IQR）
- 趋势预测（线性回归）
- LLM 自动生成分析代码
- 沙箱执行环境

### 6. BI 报告生成
- 自动生成结构化分析报告（摘要、指标、分析、原因、建议）
- 导出 HTML / Markdown / JSON 格式
- 自动 Dashboard 配置生成
- 数据洞察自动提取

### 7. 安全与权限
- SQL 安全校验：禁止 DROP / DELETE / UPDATE / INSERT / TRUNCATE / ALTER 等
- 数据库级只读 PRAGMA 双重保护
- JWT 认证 + 5 种角色权限（admin / analyst / viewer / sales / finance）
- 敏感数据脱敏（手机号、邮箱、身份证、姓名）
- 表级和列级访问控制

### 8. 自动告警与巡检
- 3 条默认告警规则（销量骤降、订单暴涨、零销量商品）
- 支持自定义告警规则
- 每日自动巡检 + 趋势分析
- 可扩展通知渠道（企业微信、钉钉、邮件）

### 9. 多数据库支持
- 统一连接器：SQLite / MySQL / PostgreSQL / ClickHouse
- 多数据库自动路由
- 跨库联合查询

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | 高性能异步 Web 框架 |
| **Agent 框架** | LangChain + LangGraph | LLM Agent 编排 |
| **LLM** | OpenAI / 兼容 API | 支持 GPT-4o 及国内模型代理 |
| **数据库** | SQLAlchemy + SQLite | 默认 SQLite，可切换 MySQL/PG |
| **数据处理** | Pandas + NumPy | 数据分析与统计 |
| **可视化** | ECharts | 前端图表渲染 |
| **前端框架** | React 18 + TypeScript | SPA 应用 |
| **构建工具** | Vite 6 | 极速开发构建 |
| **样式** | Tailwind CSS 3 | 原子化 CSS |
| **状态管理** | Zustand | 轻量级状态管理 |
| **图标** | Lucide React | 开源图标库 |

---


### 4. 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | LLM API 密钥 | - |
| `OPENAI_BASE_URL` | LLM API 代理地址 | - |
| `DATA_AGENT_LLM_MODEL` | 模型名称 | `gpt-4o` |
| `DATA_AGENT_DB_URL` | 数据库连接串 | `sqlite:///data/demo.db` |
| `DATA_AGENT_PORT` | 后端端口 | `8002` |
| `DATA_AGENT_LOG_LEVEL` | 日志级别 | `INFO` |

---

## API 接口一览

### 查询
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/query` | 自然语言查询（核心接口） |
| `POST` | `/api/query/stream` | 流式查询（SSE） |
| `POST` | `/api/sql/execute` | 直接执行 SQL |
| `WS` | `/api/ws/query` | WebSocket 实时查询 |

### Schema
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/schema` | 获取全部 Schema |
| `GET` | `/api/schema/{table}` | 获取指定表详情 |

### 多 Agent 协作
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/agent/plan` | Planner 任务分解 |
| `POST` | `/api/agent/plan/stream` | 多 Agent 流式执行 |

### SQL 优化
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/sql/optimize` | SQL 优化（含自动重写） |
| `POST` | `/api/sql/analyze` | SQL 分析 + 索引推荐 |

### 知识库
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/knowledge/search` | 搜索知识库 |
| `POST` | `/api/knowledge/init` | 初始化知识库 |

### 分析
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/analysis/anomaly` | 异常检测 |
| `POST` | `/api/analysis/forecast` | 数据预测 |

### 报告
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/report/generate` | 生成分析报告 |
| `POST` | `/api/report/export` | 导出报告 |
| `POST` | `/api/report/dashboard` | 生成 Dashboard |
| `POST` | `/api/report/insights` | 数据洞察 |

### 告警
| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/alert/check` | 告警检查 |
| `GET` | `/api/alert/daily` | 每日巡检 |
| `GET` | `/api/alert/trend` | 趋势分析 |

### 权限
| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/login` | 用户登录 |
| `GET` | `/api/auth/me` | 当前用户信息 |

---

## 项目结构

```
data-agent/
├── backend/                        # Python 后端
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # 全局配置
│   ├── requirements.txt            # Python 依赖
│   │
│   ├── api/
│   │   └── routes.py               # 全部 API 路由（20+ 端点）
│   │
│   ├── agent/                      # Agent 核心
│   │   ├── llm_client.py           # LLM 客户端
│   │   ├── sql_agent.py            # 自然语言→SQL→分析
│   │   ├── planner.py              # 多Agent 编排器
│   │   ├── tools.py                # Agent 工具集
│   │   ├── safety.py               # SQL 安全校验
│   │   ├── optimizer.py            # SQL 优化器
│   │   ├── python_agent.py         # Python 分析 Agent
│   │   ├── report_agent.py         # 报告生成 Agent
│   │   └── alert_agent.py          # 告警巡检 Agent
│   │
│   ├── db/                         # 数据库层
│   │   ├── connection.py           # 连接管理
│   │   ├── schema.py               # Schema 读取
│   │   ├── init_demo.py            # Demo 数据初始化
│   │   └── multi_db.py             # 多数据库支持
│   │
│   ├── analysis/
│   │   └── analyzer.py             # 数据分析（统计摘要）
│   │
│   ├── visualization/
│   │   └── charts.py               # ECharts 图表配置生成
│   │
│   ├── knowledge/
│   │   └── retriever.py            # RAG 知识库检索
│   │
│   └── security/
│       └── permissions.py          # JWT + 角色权限 + 数据脱敏
│
├── web/                            # React 前端
│   ├── src/
│   │   ├── pages/Home.tsx          # 主页面
│   │   ├── components/
│   │   │   ├── chat/               # 聊天组件
│   │   │   │   ├── ChatHeader.tsx  # 导航栏
│   │   │   │   ├── ChatInput.tsx   # 输入框
│   │   │   │   ├── MessageList.tsx # 消息列表
│   │   │   │   └── MessageBubble.tsx # 消息气泡
│   │   │   └── panels/
│   │   │       ├── ChartView.tsx   # ECharts 图表渲染
│   │   │       ├── SchemaPanel.tsx # Schema 可视化
│   │   │       └── DashboardPanel.tsx # 系统仪表盘
│   │   ├── api/index.ts            # API 封装
│   │   ├── store/index.ts          # Zustand 状态
│   │   ├── types/index.ts          # TypeScript 类型
│   │   └── hooks/useTheme.ts       # 主题 Hook
│   └── ...配置文件
│
└── data/                           # 运行时数据
    ├── demo.db                     # Demo SQLite 数据库
    ├── knowledge/                  # 知识库文件
    ├── reports/                    # 导出报告
    └── logs/                       # 日志
```

---

## Demo 数据库

启动时自动初始化，包含：

| 表 | 数据量 | 说明 |
|----|--------|------|
| `products` | 15 条 | 商品信息（手机、电脑、耳机、配件等） |
| `users` | 50 条 | 用户信息（分布10个城市） |
| `orders` | 500 条 | 订单记录（2024年全年） |

**ER 关系：**
```
users ──< orders >── products
```

---

## 安全设计

### 三层防护

1. **SQL 关键字过滤**：禁止 DROP / DELETE / UPDATE / INSERT / TRUNCATE / ALTER / CREATE / GRANT / EXEC 等
2. **数据库只读模式**：SQLite 启用 `PRAGMA query_only = ON`
3. **行数限制**：自动添加 `LIMIT 10000`

### 角色权限

| 角色 | 可访问表 | 脱敏 | 说明 |
|------|---------|------|------|
| `admin` | 全部 | 否 | 管理员 |
| `analyst` | 全部 | 是 | 数据分析师 |
| `viewer` | orders, products | 是 | 查看者 |
| `sales` | orders, products | 是 | 销售 |
| `finance` | orders, products | 是 | 财务 |

---

## 使用示例

### 基本查询

```bash
curl -X POST http://localhost:8002/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "查询销量最高的10个商品"}'
```

返回：SQL + 数据 + 分析 + 图表配置 + 耗时

### 多 Agent 协作

```bash
curl -X POST http://localhost:8002/api/agent/plan \
  -H "Content-Type: application/json" \
  -d '{"question": "分析今年销量下降的原因并给出建议"}'
```

返回：Planner 分解的任务步骤列表

### SQL 优化

```bash
curl -X POST http://localhost:8002/api/sql/optimize \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM orders WHERE YEAR(create_time)=2025", "auto_fix": true}'
```

返回：优化后的 SQL + 建议 + 索引推荐

---

## 设计理念

- **自主性**：Agent 自主理解需求、规划步骤、调用工具，而非被动响应用户指令
- **安全性优先**：多层安全防护，企业级权限管控，敏感数据脱敏
- **可扩展**：模块化设计，支持多数据库、多 Agent、多通知渠道
- **渐进式**：从简单的自然语言查询到复杂的多 Agent 协作分析，可以逐步启用

---

## 路线图

- [x] 自然语言 → SQL → 数据分析核心链路
- [x] 多 Agent 协作（Planner + Coordinator）
- [x] RAG 知识库联合查询
- [x] SQL 智能优化与索引推荐
- [x] 角色权限 + 数据脱敏
- [x] Python 高级分析（异常检测、趋势预测）
- [x] BI 报告自动生成与导出
- [x] 自动告警与定时巡检
- [x] 多数据库统一查询接口
- [ ] MCP 工具生态接入
- [ ] 语音交互
- [ ] 移动端适配
