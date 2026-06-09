# Memory-Driven Growth Agent TECH DESIGN V1

## 1. 文档目标

本文档用于描述 **Memory-Driven Growth Agent** 的技术设计方案。

该系统定位为一个面向长期成长陪伴场景的 AI Agent 项目，重点展示：

* 多层记忆系统设计
* LangGraph Agent 工作流编排
* 主动记忆采集
* 行为模式发现
* 干预策略路由
* 行动任务跟踪
* 周期性成长总结

本文档主要用于后续代码实现、Cursor Vibe Coding、项目开发拆分和面试讲解。

---

## 2. 技术目标

### 2.1 核心技术目标

系统需要实现从用户对话到成长干预的最小闭环：

```text
用户输入
↓
风险识别
↓
短期上下文读取
↓
长期记忆召回
↓
信息缺失检测
↓
主动追问 / 正常回复
↓
结构化记忆抽取
↓
多层记忆更新
↓
行为模式发现
↓
干预方法匹配
↓
行动任务生成
↓
任务跟踪与复盘
```

---

### 2.2 MVP 技术边界

MVP 阶段不追求复杂算法或完整成长管理系统，而是优先保证一条可演示、可验证的最小闭环。

MVP 阶段实现：

* 单用户或简单多用户
* Web 聊天界面
* FastAPI 后端接口
* LangGraph 条件化工作流
* MongoDB 存储结构化记忆和业务数据
* Milvus 存储长期记忆向量并支持语义召回
* 内置干预方法库
* 简单规则 + LLM 的行为模式发现
* 任务生成与完成情况记录
* 记忆查看、修改、删除
* 模式确认 / 拒绝
* 高风险输入安全流程

MVP 阶段暂不实现：

* Redis 会话缓存、限流和任务缓存
* 完整周总结页面
* 18 天成长计划
* 多会话管理
* 成长报告导出

这些内容可以作为 P1/P2 扩展，不影响第一版闭环演示。

---

## 3. 总体技术架构

## 3.1 架构图

MVP 使用 MongoDB + Milvus 的双存储架构：

```text
Frontend
  |
  | HTTP / SSE
  v
Backend API Server - FastAPI
  |
  v
LangGraph Agent Workflow
  |
  |-------------------------------|----------------------
  |                               |                     |
  v                               v                     v
Memory Service              Intervention Service   LLM Service
  |                               |
  |                               v
  |                         Method Library
  |
  |---- MongoDB
  |
  |---- Milvus / Vector Store
```

存储职责划分：

```text
Memory Service
  |
  |---- MongoDB: structured memory source of truth
  |
  |---- Milvus / Vector Store: semantic retrieval index
```

MongoDB 始终作为结构化记忆的事实来源。向量库只保存检索索引，不能成为唯一记忆存储。

MVP 不直接引入 Mem0、Letta、Graphiti、Cognee 等开源记忆 / Agent 平台作为核心依赖，避免框架边界扩大。可以借鉴这些项目的接口设计，但第一版由本项目自己的 MemoryService 统一封装 MongoDB + Milvus。

---

## 3.2 模块划分

```text
app/
├── api/
│   ├── chat_api.py
│   ├── memory_api.py
│   ├── pattern_api.py
│   ├── task_api.py
│   └── summary_api.py
│
├── agent/
│   ├── graph.py
│   ├── state.py
│   ├── nodes/
│   │   ├── risk_detection.py
│   │   ├── safety_response.py
│   │   ├── memory_retrieval.py
│   │   ├── gap_detection.py
│   │   ├── response_planner.py
│   │   ├── response_generation.py
│   │   ├── memory_extraction.py
│   │   ├── memory_update.py
│   │   ├── pattern_discovery.py
│   │   ├── intervention_routing.py
│   │   └── task_generation.py
│   └── prompts/
│       ├── risk_detection.md
│       ├── safety_response.md
│       ├── gap_detection.md
│       ├── response_generation.md
│       ├── memory_extraction.md
│       ├── pattern_discovery.md
│       └── intervention_routing.md
│
├── services/
│   ├── llm_service.py
│   ├── memory_service.py
│   ├── memory_provider.py
│   ├── vector_service.py
│   ├── pattern_service.py
│   ├── intervention_service.py
│   ├── task_service.py
│   └── summary_service.py
│
├── models/
│   ├── user.py
│   ├── conversation.py
│   ├── memory.py
│   ├── profile.py
│   ├── pattern.py
│   ├── task.py
│   └── method.py
│
├── repositories/
│   ├── user_repo.py
│   ├── conversation_repo.py
│   ├── memory_repo.py
│   ├── profile_repo.py
│   ├── pattern_repo.py
│   ├── task_repo.py
│   └── method_repo.py
│
├── schemas/
│   ├── chat_schema.py
│   ├── memory_schema.py
│   ├── pattern_schema.py
│   ├── task_schema.py
│   └── summary_schema.py
│
├── core/
│   ├── config.py
│   ├── logger.py
│   ├── exceptions.py
│   └── prompt_loader.py
│
└── main.py
```

项目初始化脚本：

```text
scripts/init_project.ps1
```

该脚本只负责创建目录、Python package marker 和最小 `app/main.py` 健康检查入口，不写入业务逻辑。

所有 Python package 目录必须包含 `__init__.py`，默认内容为简短 package marker。前端目录采用：

```text
frontend/src/
├── components/
├── hooks/
├── pages/
└── services/
```

---

## 4. 技术栈选型

## 4.1 后端

MVP 技术栈：

```text
FastAPI
Pydantic v2
LangGraph
MongoDB
Milvus / Vector Store
```

P1/P2 可选扩展：

```text
Redis
```

### 选择理由

#### FastAPI

用于提供后端 API 服务，支持异步接口和 SSE 流式输出。

#### Pydantic v2

用于请求参数、响应结构和 Agent State 的类型校验。

#### LangGraph

用于编排多节点 Agent 工作流。MVP 必须使用条件边，而不是每轮对话都线性执行所有节点。

#### MongoDB

用于存储：

* 用户信息
* 对话历史
* 结构化记忆
* 用户画像
* 行为模式
* 行动任务
* 方法库

MVP 中 MongoDB 作为结构化记忆和业务数据的事实来源。

#### Redis（P1 可选）

用于会话缓存、限流数据和临时任务状态。MVP 不依赖 Redis，避免增加部署复杂度。

#### Milvus / Vector Store

用于长期记忆的语义向量检索。MVP 使用 Milvus 存储 memory embedding，并通过 memory_id / embedding_id 与 MongoDB 结构化记忆关联。

---
#### 开源记忆项目借鉴原则

MVP 保持自有 MemoryService，不直接接入 Mem0、Letta、Graphiti、Cognee 等开源记忆 / Agent 平台作为底座。

原因：

* 本项目的核心展示点是结构化成长记忆、模式发现和行动闭环，不能被外部框架黑盒化。
* MongoDB 必须保留为结构化记忆事实来源，以支持可见、可改、可删、可追溯。
* Milvus 只作为语义召回索引，删除或修改记忆时必须由 MemoryService 控制一致性。
* 开源项目可以作为接口和实现参考，但不进入 MVP 依赖链。

后续如需接入开源记忆项目，应通过 MemoryProvider 适配层实现，不能让业务节点直接依赖第三方 SDK。

---

## 4.2 MemoryService Provider 边界

MemoryService 对 Agent 节点暴露稳定接口：

```text
add_memory(memory)
search_memories(query, filters, top_k)
list_memories(user_id, filters)
update_memory(memory_id, patch)
delete_memory(memory_id)
```

MVP 默认实现：

```text
MongoMilvusMemoryProvider
```

职责：

1. 将结构化记忆写入 MongoDB。
2. 将可检索文本写入 Milvus embedding 索引。
3. 通过 memory_id 关联 MongoDB 与 Milvus。
4. 删除或修改记忆时，同步失效对应向量索引。
5. 对上层返回 evidence_memory_ids，供模式发现和用户确认使用。

P2 可选实现：

```text
Mem0MemoryProvider
LangMemMemoryProvider
```

这些 provider 只作为替换实现，不改变 Agent State、PatternDiscoveryNode、InterventionRoutingNode 和 TaskGenerationNode 的业务逻辑。

---

## 4.3 前端

推荐：

```text
React + Vite
```

或：

```text
Next.js
```

MVP 阶段优先选择 React + Vite，开发成本更低。

MVP 前端页面包括：

* 聊天页
* 记忆页 / 记忆面板
* 模式页 / 模式面板
* 行动任务页 / 行动面板

完整总结页作为 P1 页面后置。

---

## 4.4 模型服务

可选模型：

```text
Qwen
DeepSeek
OpenAI
豆包
```

建议封装统一 `LLMService`，避免业务代码绑定具体模型。

---

## 4.5 依赖与环境配置

项目依赖以 `pyproject.toml` 为后端单一声明文件，避免同时维护 `requirements.txt` 和 `pyproject.toml` 造成漂移。

后端基础依赖：

```text
fastapi
uvicorn[standard]
pydantic v2
pydantic-settings
langgraph
langchain-core
motor
pymongo
pymilvus
jinja2
python-dotenv
httpx
```

测试和代码规范依赖：

```text
pytest
pytest-asyncio
ruff
```

前端依赖由 `frontend/package.json` 管理，MVP 使用 React + Vite + TypeScript。

环境变量模板放在 `.env.example`。本地开发时复制为 `.env`，不要提交真实密钥。

关键配置项：

```text
APP_ENV
LOG_LEVEL
MONGODB_URI
MONGODB_DATABASE
MONGODB_COLLECTION_PREFIX
VECTOR_BACKEND
MILVUS_HOST
MILVUS_PORT
MILVUS_COLLECTION
EMBEDDING_DIMENSION
LLM_PROVIDER
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL
LLM_TEMPERATURE
LANGGRAPH_CHECKPOINT_DIR
AGENT_NODE_TIMEOUT_SECONDS
DISCLAIMER_TEXT_PATH
RISK_KEYWORDS_PATH
PROMPT_DIR
```

---

## 4.6 core/config.py 设计

`app/core/config.py` 使用 `pydantic-settings` 读取环境变量，暴露单一 `Settings` 对象。

配置分组：

1. MongoDB：URI、数据库名、集合名前缀。
2. Milvus：host、port、collection name、embedding dimension。
3. LLM：provider、API key、base_url、model、temperature。
4. LangGraph：checkpoint 目录、节点超时。
5. Safety：免责声明文本路径、风险关键词文件路径。
6. Prompt：Prompt 根目录。

MVP 不实现复杂多环境配置系统，只区分 `development`、`test`、`production` 三个 `APP_ENV` 值。

---

## 4.7 日志与异常处理

`app/core/logger.py`：

* 开发环境使用可读文本日志。
* 生产环境优先使用 JSON 日志。
* 默认日志级别来自 `LOG_LEVEL`。
* Agent 节点日志必须包含 `user_id`、`conversation_id`、`node_name`，但不能记录完整敏感输入。

`app/core/exceptions.py` 定义项目业务异常：

```python
class AppError(Exception): ...
class MemoryNotFoundError(AppError): ...
class PatternNotFoundError(AppError): ...
class TaskNotFoundError(AppError): ...
class RiskDetectionError(AppError): ...
class MongoConnectionError(AppError): ...
class VectorStoreError(AppError): ...
class LLMServiceError(AppError): ...
```

`app/main.py` 需要注册 FastAPI 全局异常处理器，将业务异常转成稳定 JSON：

```json
{
  "error": {
    "code": "memory_not_found",
    "message": "Memory not found"
  }
}
```

---

## 4.8 Prompt Loader 设计

Prompt 文件放在 `app/agent/prompts/`，按节点名命名，使用 `.md` 后缀。

示例：

```text
risk_detection.md
safety_response.md
gap_detection.md
response_generation.md
memory_extraction.md
pattern_discovery.md
intervention_routing.md
```

`app/core/prompt_loader.py` 职责：

1. 从 `PROMPT_DIR` 读取本地 `.md` 文件。
2. 使用 Jinja2 渲染变量。
3. 在开发环境可每次读取文件，方便调 Prompt。
4. 在生产环境可做进程内缓存。

MVP 暂不实现多语言或多角色 Prompt 切换。若后续需要国际化，再通过目录分层扩展。

---

## 4.9 本地开发与部署

本地基础设施使用 `docker-compose.yml` 启动 MongoDB、Milvus standalone、etcd 和 MinIO：

```powershell
docker compose up -d
```

初始化数据库和方法库：

```powershell
python .\scripts\init_db.py
```

后端启动入口：

```powershell
uvicorn app.main:app --reload
```

前端启动入口：

```powershell
cd frontend
npm install
npm run dev
```

部署建议：

* MVP 演示优先使用单机 Docker Compose。
* 生产化部署再拆分 API、MongoDB、Milvus 和对象存储。
* 不在 MVP 中引入 Kubernetes、Redis、任务队列或复杂网关。

---

## 4.10 Authentication 边界

MVP 允许接口显式传入 `user_id`，用于作品集演示和单用户/简单多用户验证。

限制：

1. 不把该方案描述为生产级鉴权。
2. 所有数据访问必须按 `user_id` 过滤。
3. 后续生产化可增加登录态、JWT 或第三方 OAuth，但不进入 MVP。

---

## 5. 核心工作流设计

## 5.1 LangGraph 总流程

MVP 工作流不应是固定线性链路，而应根据风险、信息完整度和模式证据走条件分支。

```text
START
  ↓
RiskDetectionNode
  ├─ high risk → SafetyResponseNode → END
  ↓ none / low / medium
MemoryRetrievalNode
  ↓
GapDetectionNode
  ├─ need_follow_up=true → ResponsePlannerNode → ResponseGenerationNode → MemoryExtractionNode → MemoryUpdateNode → END
  ↓ need_follow_up=false
ResponsePlannerNode
  ↓
ResponseGenerationNode
  ↓
MemoryExtractionNode
  ↓
MemoryUpdateNode
  ↓
PatternDiscoveryNode
  ├─ no candidate pattern → END
  ├─ candidate pattern not confirmed → PatternFeedbackPrompt → END
  ↓ confirmed / high confidence
InterventionRoutingNode
  ↓
TaskGenerationNode
  ↓
END
```

关键原则：

1. 高风险输入直接进入安全回复，不继续普通成长教练流程。
2. 信息不足时优先追问，不急着生成行动任务。
3. 模式发现必须基于至少 3 条证据记忆。
4. 用户拒绝的模式不进入干预路由。
5. 干预和任务生成只在模式证据足够时触发。

---

## 5.2 节点说明

## 5.2.1 RiskDetectionNode

### 作用

识别用户输入中是否存在高风险内容。

高风险包括：

* 自伤
* 自杀
* 暴力
* 严重绝望
* 明确危险计划

### 输入

```json
{
  "user_input": "string",
  "short_term_messages": []
}
```

### 输出

```json
{
  "risk_level": "none | low | medium | high",
  "risk_reason": "string"
}
```

### 处理逻辑

如果风险等级为 high，则直接进入安全回复流程，不继续普通成长教练流程。

---
## 5.2.2 SafetyResponseNode

### 作用

当风险等级为 high 时生成安全回复，并阻止普通成长教练流程继续执行。

### 输入

```json
{
  "user_id": "string",
  "user_input": "string",
  "risk_level": "high",
  "risk_reason": "string"
}
```

### 输出

```json
{
  "assistant_response": "string",
  "safety_handled": true,
  "memory_write_policy": "minimal_safety_log_only",
  "next": "END"
}
```

### 处理逻辑

1. 表达关切。
2. 建议联系身边可信任的人。
3. 建议寻求专业帮助。
4. 如有紧急危险，建议联系当地紧急服务。
5. 不生成成长任务。
6. 不更新普通用户画像。
7. 不将该轮内容用于行为模式发现。

---

## 5.2.3 MemoryRetrievalNode

### 作用

根据当前用户输入召回相关长期记忆。

### 召回依据

* 当前问题关键词
* 当前情绪
* 当前场景
* 历史相似事件
* 用户画像
* 当前未完成任务

### 输入

```json
{
  "user_id": "string",
  "user_input": "string"
}
```

### 输出

```json
{
  "retrieved_memories": [],
  "user_profile": {},
  "active_tasks": []
}
```

### MVP 实现

第一版采用 MongoDB + Milvus 混合召回：

* MongoDB 按 user_id、emotion、scenario、trigger、behavior 做结构化过滤
* Milvus 按当前输入 embedding 做 TopK 语义召回
* 通过 memory_id 合并两路结果，并从 MongoDB 读取完整结构化记忆

---

## 5.2.4 GapDetectionNode

### 作用

检测用户当前表达中缺少哪些关键信息。

目标结构：

```json
{
  "event": "发生了什么",
  "emotion": "情绪是什么",
  "trigger": "触发因素",
  "behavior": "用户怎么应对",
  "result": "造成什么结果"
}
```

### 输入

```json
{
  "user_input": "string",
  "retrieved_memories": []
}
```

### 输出

```json
{
  "extracted_partial_event": {
    "event": "string | null",
    "emotion": "string | null",
    "trigger": "string | null",
    "behavior": "string | null",
    "result": "string | null"
  },
  "missing_fields": ["trigger", "behavior"],
  "need_follow_up": true,
  "follow_up_question": "string"
}
```

### 示例

用户输入：

```text
最近好焦虑。
```

输出：

```json
{
  "extracted_partial_event": {
    "event": null,
    "emotion": "焦虑",
    "trigger": null,
    "behavior": null,
    "result": null
  },
  "missing_fields": ["event", "trigger", "behavior", "result"],
  "need_follow_up": true,
  "follow_up_question": "最近有没有一件事让这种焦虑特别明显？"
}
```

---

## 5.2.5 ResponsePlannerNode

### 作用

决定当前应该采用哪种回复策略。

### 策略类型

```text
emotional_support
information_follow_up
pattern_feedback
action_suggestion
task_review
safety_response
```

### 输入

```json
{
  "risk_level": "none",
  "missing_fields": [],
  "retrieved_memories": [],
  "active_tasks": [],
  "detected_patterns": []
}
```

### 输出

```json
{
  "response_strategy": "information_follow_up",
  "strategy_reason": "当前用户表达信息不足，需要补全触发因素"
}
```

---

## 5.2.6 ResponseGenerationNode

### 作用

根据回复策略生成最终回复。

### 输入

```json
{
  "user_input": "string",
  "response_strategy": "string",
  "retrieved_memories": [],
  "follow_up_question": "string",
  "active_tasks": []
}
```

### 输出

```json
{
  "assistant_response": "string"
}
```

### 生成原则

1. 不诊断用户
2. 不替代心理咨询
3. 不一次问多个问题
4. 不给大而空的建议
5. 优先生成轻量行动
6. 对未完成任务不批评

---

## 5.2.7 MemoryExtractionNode

### 作用

从本轮对话中抽取结构化记忆。

### 输入

```json
{
  "user_input": "string",
  "assistant_response": "string",
  "short_term_messages": []
}
```

### 输出

```json
{
  "new_memories": [
    {
      "type": "emotion_event",
      "scenario": "秋招准备",
      "event": "准备面试时学不进去",
      "emotion": "焦虑",
      "trigger": "任务压力过大",
      "behavior": "刷视频回避",
      "result": "学习中断并产生自责",
      "importance": 4,
      "confidence": 0.82
    }
  ],
  "profile_updates": {}
}
```

### 抽取限制

只保存用户明确表达或高置信度推断的信息。

不要保存：

* 模糊猜测
* 一次性无意义情绪
* 低置信度人格判断
* 医疗诊断标签

---

## 5.2.8 MemoryUpdateNode

### 作用

将新记忆写入数据库，并更新用户画像。

### 输入

```json
{
  "new_memories": [],
  "profile_updates": {}
}
```

### 输出

```json
{
  "memory_update_result": "success",
  "updated_profile": {}
}
```

### 更新策略

记忆分为三类：

```text
append：新增事件记忆
merge：合并相似长期记忆
update：更新用户画像
```

---

## 5.2.9 PatternDiscoveryNode

### 作用

从长期记忆中发现重复行为模式。

### 输入

```json
{
  "user_id": "string",
  "new_memories": []
}
```

### 输出

```json
{
  "detected_patterns": [
    {
      "trigger": "任务压力过大",
      "emotion": "焦虑",
      "behavior": "刷视频回避",
      "result": "学习中断、自责",
      "frequency": 3,
      "evidence_memory_ids": ["memory_id_1", "memory_id_2", "memory_id_3"],
      "confidence": 0.8
    }
  ]
}
```

### MVP 规则

当相似链路出现次数大于等于 3 次时，生成候选模式。

相似链路主要比较：

* trigger
* emotion
* behavior
* result

---

## 5.2.10 InterventionRoutingNode

### 作用

根据行为模式匹配干预方法。

### 输入

```json
{
  "detected_patterns": [],
  "user_profile": {}
}
```

### 输出

```json
{
  "recommended_method": {
    "name": "15分钟启动法",
    "reason": "用户多次出现任务压力导致焦虑和拖延"
  }
}
```

### 方法匹配规则

```text
拖延 / 回避
→ 15分钟启动法

内耗 / 反复想太多
→ 认知记录表

高敏感 / 外界评价影响大
→ 注意力回收训练

长期迷茫
→ 人生意义探索写作

焦虑 + 内耗 + 高敏感长期混合
→ 18天成长计划
```

---

## 5.2.11 TaskGenerationNode

### 作用

将推荐方法转化为具体行动任务。

### 输入

```json
{
  "recommended_method": {},
  "user_context": {}
}
```

### 输出

```json
{
  "task": {
    "task_content": "今天只花15分钟整理简历中的项目描述，不要求全部改完。",
    "method": "15分钟启动法",
    "due_at": "datetime"
  }
}
```

### 任务生成原则

1. 小到用户可以开始
2. 只要求一个动作
3. 有明确完成标准
4. 不超过 15 到 30 分钟
5. 可以根据用户失败反馈继续降低难度

---

## 6. Agent State 设计

## 6.1 GrowthAgentState

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class PartialEmotionEvent(BaseModel):
    event: Optional[str] = None
    emotion: Optional[str] = None
    trigger: Optional[str] = None
    behavior: Optional[str] = None
    result: Optional[str] = None
    scenario: Optional[str] = None
    confidence: float = 0.0


class GrowthAgentState(BaseModel):
    user_id: str
    conversation_id: str
    user_input: str

    short_term_messages: List[Message] = Field(default_factory=list)

    risk_level: str = "none"
    risk_reason: Optional[str] = None

    retrieved_memories: List[Dict[str, Any]] = Field(default_factory=list)
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    active_tasks: List[Dict[str, Any]] = Field(default_factory=list)

    partial_event: Optional[PartialEmotionEvent] = None
    missing_fields: List[str] = Field(default_factory=list)
    need_follow_up: bool = False
    follow_up_question: Optional[str] = None

    response_strategy: Optional[str] = None
    assistant_response: Optional[str] = None

    new_memories: List[Dict[str, Any]] = Field(default_factory=list)
    detected_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_method: Optional[Dict[str, Any]] = None
    generated_task: Optional[Dict[str, Any]] = None
```

实现注意：

1. 具体代码需要验证当前 LangGraph 版本对 Pydantic `BaseModel` state 的支持情况。
2. 如果所用版本对 `BaseModel` state 兼容性不稳定，则运行时 state 使用 `TypedDict`，节点输入输出边界继续使用 Pydantic schema 校验。
3. 不允许为了兼容性绕过字段约束，尤其是 `risk_level`、`need_follow_up`、`evidence_memory_ids` 和删除一致性相关字段。

---

## 7. 数据库设计

## 7.1 MongoDB Collections

```text
users
conversations
memories
user_profiles
patterns
tasks
methods
summaries
```

---

## 7.2 users

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "nickname": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 7.3 conversations

```json
{
  "_id": "ObjectId",
  "conversation_id": "string",
  "user_id": "string",
  "title": "string",
  "messages": [
    {
      "role": "user | assistant",
      "content": "string",
      "created_at": "datetime"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 7.4 memories

```json
{
  "_id": "ObjectId",
  "memory_id": "string",
  "user_id": "string",
  "type": "emotion_event | goal | preference | reflection",
  "scenario": "string",
  "event": "string",
  "emotion": "string",
  "trigger": "string",
  "behavior": "string",
  "result": "string",
  "importance": 4,
  "confidence": 0.82,
  "source": "conversation | checkin | reflection",
  "embedding_id": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 7.5 user_profiles

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "traits": ["容易焦虑", "任务过大时容易拖延"],
  "goals": ["找到AI应用开发实习"],
  "stress_sources": ["秋招", "项目推进", "面试"],
  "common_emotions": ["焦虑", "自责"],
  "common_behaviors": ["刷视频回避", "反复纠结"],
  "preferred_support_style": "具体、直接、可执行",
  "avoid_support_style": "空泛鼓励、说教",
  "updated_at": "datetime"
}
```

---

## 7.6 patterns

```json
{
  "_id": "ObjectId",
  "pattern_id": "string",
  "user_id": "string",
  "scenario": "学习 / 求职 / 人际 / 项目",
  "trigger": "任务压力过大",
  "emotion": "焦虑",
  "behavior": "刷视频回避",
  "result": "学习中断、自责",
  "frequency": 3,
  "evidence_memory_ids": ["memory_id_1", "memory_id_2"],
  "confidence": 0.8,
  "status": "detected | confirmed | rejected",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 7.7 tasks

```json
{
  "_id": "ObjectId",
  "task_id": "string",
  "user_id": "string",
  "pattern_id": "string",
  "method_id": "string",
  "task_content": "今天只花15分钟整理简历项目描述。",
  "status": "pending | completed | failed | adjusted",
  "feedback": "string",
  "created_at": "datetime",
  "due_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 7.8 methods

```json
{
  "_id": "ObjectId",
  "method_id": "string",
  "name": "15分钟启动法",
  "target_problem": ["拖延", "回避", "任务压力"],
  "description": "通过降低启动难度帮助用户开始行动。",
  "steps": [
    "选择一个最小任务",
    "设置15分钟计时器",
    "只要求开始，不要求完成",
    "结束后记录感受"
  ],
  "suitable_patterns": ["任务压力-焦虑-回避-自责"],
  "difficulty": "low"
}
```

---

## 7.9 summaries

```json
{
  "_id": "ObjectId",
  "summary_id": "string",
  "user_id": "string",
  "type": "weekly | plan_18_days | stage",
  "content": "string",
  "period_start": "datetime",
  "period_end": "datetime",
  "created_at": "datetime"
}
```

---

## 7.10 数据库初始化脚本

数据库初始化脚本放在：

```text
scripts/init_db.py
```

职责：

1. 创建 MongoDB 基础索引。
2. 创建 Milvus collection 和向量索引。
3. 写入 MVP 方法库 seed 数据。

MongoDB MVP 索引：

```text
users: user_id unique
conversations: user_id + updated_at
memories: user_id + created_at
memories: user_id + type
memories: memory_id unique
patterns: user_id + status
patterns: pattern_id unique
tasks: user_id + status
tasks: task_id unique
methods: method_id unique
```

Milvus collection 默认名：

```text
memory_embeddings
```

字段：

```text
embedding_id: varchar primary key
memory_id: varchar
user_id: varchar
type: varchar
scenario: varchar
created_at: int64
embedding: float_vector
```

---

## 8. Milvus 向量设计

## 8.1 Collection：memory_embeddings

字段：

```text
embedding_id: string
memory_id: string
user_id: string
type: string
scenario: string
created_at: int64
embedding: float_vector
```

---

## 8.2 向量文本构造

每条长期记忆向量化时，将结构化字段拼接成 `memory_text`：

```text
场景：秋招准备。
事件：准备面试时学不进去。
情绪：焦虑。
触发因素：任务压力过大。
行为：刷视频回避。
结果：学习中断并产生自责。
```

`memory_text` 是向量化输入文本，不作为 Milvus collection 的必需字段存储。MongoDB 中的 `memories` collection 仍是完整记忆内容的事实来源；Milvus 只保存检索所需的向量和过滤字段。

---

## 8.3 检索策略

MVP 可以使用：

```text
TopK = 5
```

后续优化：

* 结合 user_id 过滤
* 结合 type 过滤
* 结合 importance 加权
* 结合 recency 加权
* 结合 reranker 精排

---

## 8.4 VectorService 边界

`app/services/vector_service.py` 对上层暴露稳定接口：

```text
upsert_embedding(memory_id, user_id, text, metadata)
search(query_text, user_id, top_k, filters)
delete_embedding(embedding_id)
delete_by_memory_id(memory_id)
rebuild_from_memories(user_id)
```

MVP 默认实现为 Milvus。单元测试可以使用 in-memory fake vector service，避免测试依赖本地 Milvus。

不建议在 MVP 默认依赖中加入 FAISS 或 ChromaDB。原因是它们会增加一套额外向量存储语义，容易让删除一致性和 MongoDB 事实来源边界变模糊。若本地 Milvus 成为开发阻塞，可在 P1 通过同一 `VectorService` 接口增加：

```text
VECTOR_BACKEND=faiss | chroma
```

但 Agent 节点不得直接依赖这些第三方向量库。

---

## 9. 核心接口设计

## 9.1 聊天接口

### POST /api/chat

请求：

```json
{
  "user_id": "string",
  "conversation_id": "string",
  "message": "我今天又学不进去了。"
}
```

响应：

```json
{
  "conversation_id": "string",
  "assistant_response": "你之前也提到过，任务一大时容易进入焦虑—回避—自责的循环。今天先不要求完成完整任务，只做15分钟启动。",
  "strategy": "action_suggestion",
  "retrieved_memories": [],
  "detected_patterns": [],
  "generated_task": {}
}
```

---

## 9.2 获取记忆列表

### GET /api/memories

参数：

```text
user_id
type
scenario
```

响应：

```json
{
  "memories": []
}
```

---

## 9.3 修改记忆

### PATCH /api/memories/{memory_id}

请求：

```json
{
  "event": "更新后的事件",
  "emotion": "焦虑"
}
```

响应：

```json
{
  "success": true
}
```

---

## 9.4 删除记忆

### DELETE /api/memories/{memory_id}

响应：

```json
{
  "success": true
}
```

---

## 9.5 获取行为模式

### GET /api/patterns

参数：

```text
user_id
status
```

响应：

```json
{
  "patterns": []
}
```

---

## 9.6 确认或拒绝模式

### POST /api/patterns/{pattern_id}/feedback

请求：

```json
{
  "status": "confirmed | rejected"
}
```

响应：

```json
{
  "success": true
}
```

---

## 9.7 获取行动任务

### GET /api/tasks

参数：

```text
user_id
status
```

响应：

```json
{
  "tasks": []
}
```

---

## 9.8 更新任务状态

### POST /api/tasks/{task_id}/status

请求：

```json
{
  "status": "completed | failed",
  "feedback": "我完成了15分钟，但后面没有继续。"
}
```

响应：

```json
{
  "success": true
}
```

---

## 9.9 生成周总结（P1）
### POST /api/summary/weekly

请求：

```json
{
  "user_id": "string",
  "period_start": "datetime",
  "period_end": "datetime"
}
```

响应：

```json
{
  "summary": "string"
}
```

---

## 10. Prompt 设计

## 10.1 信息缺失检测 Prompt

目标：

从用户输入中抽取部分情绪事件，并判断缺失字段。

输出必须是 JSON。

字段：

```json
{
  "event": null,
  "emotion": null,
  "trigger": null,
  "behavior": null,
  "result": null,
  "missing_fields": [],
  "need_follow_up": true,
  "follow_up_question": ""
}
```

要求：

* 不要过度推断
* 不要贴诊断标签
* 只追问一个问题
* 优先追问 trigger 或 event

---

## 10.2 记忆抽取 Prompt

目标：

从当前对话中抽取值得长期保存的信息。

要求：

* 只保存对未来有帮助的信息
* 只保存用户明确表达或高置信度信息
* 不保存普通闲聊
* 不保存医疗诊断
* 置信度低于 0.6 不写入长期记忆

输出：

```json
{
  "new_memories": [],
  "profile_updates": {}
}
```

---

## 10.3 行为模式发现 Prompt

目标：

基于多条情绪事件记忆，判断是否存在重复行为模式。

输入：

```json
{
  "memories": []
}
```

输出：

```json
{
  "patterns": [
    {
      "trigger": "",
      "emotion": "",
      "behavior": "",
      "result": "",
      "frequency": 3,
      "evidence_memory_ids": [],
      "confidence": 0.8
    }
  ]
}
```

要求：

* 必须有至少 3 条证据
* 必须引用 evidence_memory_ids
* 不要做人格判断
* 只描述观察到的行为链路

---

## 10.4 干预策略路由 Prompt

目标：

根据行为模式匹配方法库中的方法。

输入：

```json
{
  "pattern": {},
  "method_library": []
}
```

输出：

```json
{
  "method_id": "",
  "method_name": "",
  "reason": "",
  "task_suggestion": ""
}
```

要求：

* 优先选择低难度方法
* 任务必须具体
* 任务必须轻量
* 任务必须可完成
* 不给宏大建议

---

## 11. 方法库设计

MVP 内置 4 个低难度方法；18 天成长计划为 P1 方法，MVP 不实现。

## 11.1 15 分钟启动法

适用：

* 拖延
* 回避
* 任务压力过大
* 不知道从哪里开始

步骤：

```text
1. 选择一个最小任务
2. 设置 15 分钟
3. 只要求开始
4. 结束后记录感受
```

---

## 11.2 认知记录表

适用：

* 内耗
* 反复想太多
* 自我否定

步骤：

```text
1. 写下事件
2. 写下自动想法
3. 写下情绪
4. 写下支持这个想法的证据
5. 写下反驳这个想法的证据
6. 写下更平衡的解释
7. 写下一步行动
```

---

## 11.3 注意力回收训练

适用：

* 高敏感
* 过度关注他人评价
* 被消息回复影响情绪

步骤：

```text
1. 识别自己正在关注谁的反馈
2. 判断这种关注是否有实际帮助
3. 暂时减少非必要接触
4. 将注意力转回今天能完成的一件事
```

---

## 11.4 人生意义探索写作

适用：

* 长期迷茫
* 人生方向不清
* 职业目标不明确

步骤：

```text
1. 写下自己想达到什么样的状态
2. 写下赚钱的目的
3. 写下理想状态需要哪些能力
4. 反推出当前阶段应该做什么
```

---

## 11.5 18 天成长计划（P1）

适用：

* 长期内耗
* 焦虑
* 高敏感
* 多问题混合
* 用户愿意进行结构化训练

阶段：

```text
Day 1：三格记录 + 选择技能
Day 2-10：每日三格记录 + 技能学习 1.5 小时
Day 11：阶段总结
Day 12-15：识别消耗源 + 日记
Day 16-18：人生意义写作
```

---

## 12. 行为模式发现算法 MVP

MVP 不需要复杂机器学习。

采用规则 + LLM 聚类。

## 12.1 步骤

```text
1. 获取用户最近 N 条 emotion_event 记忆
2. 按 scenario / trigger / emotion / behavior 聚合
3. 查找相似链路
4. 出现次数 >= 3，生成候选模式
5. 用 LLM 总结模式描述
6. 保存到 patterns collection
7. 让用户确认模式是否准确
```

---

## 12.2 简化相似判断

可以先用字符串归一化：

```text
刷视频 / 看短视频 / 刷B站 / 刷抖音
→ 刷视频回避
```

```text
焦虑 / 慌 / 压力很大
→ 焦虑
```

```text
不想开始 / 拖着 / 学不进去
→ 拖延回避
```

---

## 12.3 后续优化

后续可以加入：

* Embedding 聚类
* LLM 归一化标签
* 时间衰减
* 置信度加权
* 用户反馈修正

---

## 13. 记忆更新策略

## 13.1 新增记忆

当 LLM 抽取到新的 emotion_event，且 confidence >= 0.6 时，写入 memories。

---

## 13.2 合并记忆

当新记忆与已有记忆高度相似时，不重复写入，而是更新已有记忆的：

* frequency
* last_seen_at
* evidence
* confidence

---

## 13.3 用户画像更新

当某种模式出现多次，才更新用户画像。

例如：

只有当用户多次出现任务压力导致回避时，才写入：

```text
任务过大时容易拖延
```

不要因为一次对话就写入稳定特征。

---

## 13.4 记忆污染控制

需要避免：

* 一次性情绪被写成长期特征
* LLM 过度推断
* 低置信度记忆长期保存
* 用户不认可的模式继续用于回复

控制策略：

1. 设置 confidence 阈值
2. 记忆来源必须可追溯
3. 模式需要用户确认
4. 用户可以删除或修改记忆
5. 画像更新需要多次证据

---

## 13.5 数据治理与删除一致性

长期记忆必须支持用户校正。MVP 需要保证：

1. 用户删除 memory 后，该 memory 不再参与召回、模式发现、画像更新和总结生成。
2. 用户拒绝 pattern 后，该 pattern 状态更新为 rejected，不再触发干预或任务生成。
3. 用户修改 memory 后，相关 pattern 应标记为需要重新评估。
4. 每条 memory 必须保存 source、confidence、created_at、updated_at。
5. 删除 memory 时必须同步删除或失效对应 embedding_id。

MongoDB 中的结构化记忆是事实来源。任何索引、缓存或向量数据都必须可以从 MongoDB 重建。

---
## 14. 安全策略

## 14.1 风险识别

风险识别采用：

```text
关键词规则
+
LLM 分类
```

风险等级：

```text
none：普通成长对话
low：负面情绪明显，但无自伤、自杀、暴力意图
medium：强烈绝望、自我否定或模糊危险表达
high：自伤、自杀、伤害他人、明确危险计划或迫近风险
```

高风险内容包括：

* 自杀
* 自伤
* 伤害他人
* 明确危险计划
* 极端绝望表达

---

## 14.2 高风险工作流

当风险等级为 high：

1. 跳过 MemoryRetrievalNode 之后的普通成长教练流程。
2. 进入 SafetyResponseNode。
3. 不生成行动任务。
4. 不更新普通用户画像。
5. 不把该轮内容用于行为模式发现。
6. 只保存最小安全处理记录，例如 risk_level、risk_reason、created_at。

---

## 14.3 高风险回复原则

回复原则：

1. 表达关切
2. 鼓励联系身边可信任的人
3. 建议寻求专业帮助
4. 如有紧急危险，建议联系当地紧急服务
5. 不做诊断，不讨论自伤方法细节，不给普通成长任务

---

## 14.4 产品免责声明

系统需要在首次使用或设置页展示：

```text
本产品用于自我成长记录和日常支持，不提供医学诊断、心理治疗或危机干预服务。如果你正在经历严重心理危机，请立即联系专业人士或当地紧急救助服务。
```

---

## 15. 前端页面设计

MVP 前端不追求完整成长管理后台，优先做一个可演示闭环的工作台。

## 15.1 聊天页

功能：

* 展示用户与 Agent 对话
* 支持流式输出
* 展示当前 Agent 状态
* 展示当前行动任务
* 展示本轮是否保存了新记忆

状态示例：

```text
正在召回相关记忆
正在识别可能的模式
正在生成行动建议
```

---

## 15.2 记忆面板

功能：

* 查看长期记忆
* 按类型筛选
* 编辑记忆
* 删除记忆
* 标记记忆是否准确

---

## 15.3 模式面板

功能：

* 展示系统发现的候选行为模式
* 展示证据记忆
* 用户确认或拒绝模式
* 根据已确认模式查看推荐方法

---

## 15.4 行动面板

功能：

* 展示当前任务
* 标记完成 / 未完成
* 填写反馈
* 查看历史任务

---

## 15.5 P1 页面

以下页面可后置：

* 独立总结页
* 18 天计划页
* 成长趋势可视化页
* 多会话管理页

---

## 16. 开发阶段拆分

## Phase 1：基础对话与记忆抽取

目标：

完成最小对话闭环。

任务：

1. 搭建 FastAPI 项目结构
2. 接入 LLMService
3. 实现 chat API
4. 实现 conversations 存储
5. 实现 MemoryExtractionNode
6. 实现 memories 存储
7. 实现简单前端聊天页

验收：

用户输入后，系统可以回复，并抽取结构化记忆写入 MongoDB。

---

## Phase 2：主动记忆采集与追问

目标：

实现 Memory Acquisition。

任务：

1. 实现 GapDetectionNode
2. 设计信息缺失检测 Prompt
3. 生成 follow_up_question
4. 在 ResponsePlannerNode 中选择追问策略
5. 支持当前追问状态保存

验收：

用户说「最近好焦虑」，系统可以识别缺失字段，并只追问一个关键问题。

---

## Phase 3：长期记忆与召回

目标：

实现基于 MongoDB 结构化记忆和 Milvus 语义召回的个性化回复。

任务：

1. 实现 MemoryRetrievalNode
2. 实现 memories 条件检索
3. 实现 user_profiles 的最小读取
4. 在回复中使用历史记忆
5. 确保已删除记忆不参与召回

验收：

用户再次提到相似问题时，系统能够通过 Milvus 召回相关历史事件，从 MongoDB 读取结构化详情，并生成个性化回复。Top 3 召回结果中至少有 1 条与当前输入相关。

---

## Phase 4：行为模式发现

目标：

实现 Pattern Discovery。

任务：

1. 实现 PatternDiscoveryNode
2. 设计模式发现规则
3. 实现 patterns 存储
4. 实现模式确认 / 拒绝接口
5. 实现模式面板

验收：

当类似事件出现至少 3 次后，系统可以生成候选模式，引用 evidence_memory_ids，并让用户确认或拒绝。被拒绝的模式不得进入干预路由。

---

## Phase 5：干预策略与行动任务

目标：

实现 Intervention Routing。

任务：

1. 初始化 methods 方法库
2. 实现 InterventionRoutingNode
3. 实现 TaskGenerationNode
4. 实现 tasks 存储
5. 实现任务状态更新接口
6. 实现行动页

验收：

系统可以根据模式推荐方法，并生成一个轻量行动任务。

---

## Phase 6：项目完善与演示准备

目标：

形成完整可讲解、可演示、可测试的 MVP。

任务：

1. 完善安全策略
2. 完善错误处理
3. 准备 demo 数据
4. 准备 30 条 Prompt 测试集
5. 准备项目 README
6. 准备面试讲解稿
7. 可选实现周总结生成

验收：

1. 至少 3 条 demo 输入可以跑通从对话、记忆抽取、记忆召回、模式发现、方法匹配、任务生成到反馈记录的完整流程。
2. 至少 1 条高风险输入会进入 SafetyResponseNode，不继续普通成长教练流程。
3. 至少 1 个候选模式引用不少于 3 条 evidence_memory_ids。
4. 记忆删除 / 修改后，不再参与召回、模式发现和画像更新。
5. 系统可以说明安全边界、记忆治理、MongoDB + Milvus 存储职责和 MVP 取舍。
6. 详细验收标准以 AGENTS.md 的 `Testing And Acceptance` 为准。

---

## 17. Demo 场景设计

## 17.1 场景一：学习拖延

用户连续多次表达：

```text
我今天又学不进去了。
任务太多，我一想到就烦。
我刷了一下午视频，晚上又很自责。
```

系统最终发现：

```text
任务压力过大
↓
焦虑
↓
刷视频回避
↓
学习中断、自责
```

推荐：

```text
15 分钟启动法
```

生成任务：

```text
今天只做 15 分钟简历项目描述修改。
```

---

## 17.2 场景二：高敏感内耗

用户表达：

```text
别人一句话我能想很久。
他没回我消息，我就一直看手机。
我总是很在意别人怎么看我。
```

系统发现：

```text
外部反馈
↓
不安
↓
反复查看消息
↓
注意力下降
```

推荐：

```text
注意力回收训练
```

---

## 17.3 场景三：长期迷茫

用户表达：

```text
我不知道自己到底想做什么。
我感觉努力也没有意义。
我不知道赚钱到底为了什么。
```

系统推荐：

```text
人生意义探索写作
```

---

## 18. 项目难点与解决方案

## 18.1 难点一：用户表达不结构化

### 问题

用户不会按照 event、emotion、trigger、behavior、result 的结构说话。

### 解决方案

设计 GapDetectionNode，通过信息缺失检测和苏格拉底式追问主动补全信息。

---

## 18.2 难点二：长期记忆容易污染

### 问题

LLM 容易把一次性情绪误判成长期特征。

### 解决方案

采用：

* confidence 阈值
* evidence 证据引用
* 用户确认机制
* 多次出现才更新画像
* 用户可编辑 / 删除记忆

---

## 18.3 难点三：模式发现可能不准确

### 问题

系统可能把偶然事件误认为模式。

### 解决方案

MVP 阶段要求：

* 至少 3 条证据
* 保存 evidence_memory_ids
* 用户确认后才进入强干预
* 未确认模式只作为温和提示

---

## 18.4 难点四：建议无法保证用户执行

### 问题

用户知道方法，但不一定执行。

### 解决方案

MVP 不承诺真正改变用户，只完成：

```text
发现
↓
建议
↓
跟踪
↓
复盘
```

的闭环。

任务生成时遵循：

* 足够小
* 可执行
* 有完成标准
* 未完成时继续降低难度

---

## 19. 测试方案

## 19.1 单元测试

测试对象：

* MemoryExtractionNode
* GapDetectionNode
* PatternDiscoveryNode
* InterventionRoutingNode
* TaskGenerationNode

---

## 19.2 集成测试

测试完整流程：

```text
用户输入
↓
记忆抽取
↓
记忆写入
↓
再次输入
↓
记忆召回
↓
模式发现
↓
方法匹配
↓
任务生成
```

---

## 19.3 Prompt 测试集

构造 30 条测试输入：

包括：

* 焦虑
* 拖延
* 高敏感
* 内耗
* 迷茫
* 普通闲聊
* 高风险表达

人工标注：

* 应抽取字段
* 是否需要追问
* 应匹配方法
* 是否应触发风险回复

通过标准：

1. emotion、trigger、behavior 三个核心字段抽取通过率不低于 80%。
2. 信息不足时，一次只追问一个问题的通过率不低于 90%。
3. 明确高风险表达必须进入 high 风险流程。
4. 每个候选模式必须引用至少 3 条 evidence_memory_ids。
5. 行动任务必须具体、轻量，建议 15 到 30 分钟内可以启动。

---

## 19.4 测试框架与目录

测试框架：

```text
pytest
pytest-asyncio
```

测试目录：

```text
tests/
├── test_nodes/
├── test_services/
└── test_api/
```

Mock 策略：

1. LLM 调用通过 `LLMService` 接口 mock，不在节点测试中直接调用真实模型。
2. 记忆服务通过 fake repository / fake provider 验证节点逻辑。
3. 向量检索在单元测试中使用 in-memory fake vector service。
4. 集成测试再连接 MongoDB 和 Milvus。

`pyproject.toml` 统一保存 pytest 和 ruff 配置。

---

## 19.5 代码规范

Python：

```text
ruff check .
ruff format .
pytest
```

前端：

```text
npm run lint
npm run build
```

代码风格原则：

1. 优先简单显式代码。
2. 不为单次使用创建抽象。
3. 不引入 MVP 闭环之外的框架。
4. 不让第三方 SDK 泄漏到 Agent 节点。

---

## 20. 评估指标

## 20.1 记忆抽取准确率

人工判断抽取字段是否正确。

字段：

```text
event
emotion
trigger
behavior
result
```

---

## 20.2 追问合理性

判断系统是否：

* 只问一个问题
* 问的是关键缺失信息
* 不像问卷
* 不冒犯用户

---

## 20.3 记忆召回相关性

判断召回的历史记忆是否对当前回复有帮助。

---

## 20.4 模式发现准确性

判断模式是否：

* 有足够证据
* 不是过度推断
* 对用户有解释价值
* 可以导向行动

---

## 20.5 干预匹配合理性

判断推荐方法是否适合当前模式。

---

## 21. 面试讲解重点

项目介绍时应强调：

```text
我做的不是心理聊天机器人，而是一个面向长期成长场景的记忆驱动 Agent。
```

核心讲法：

> 这个项目重点解决长期陪伴 Agent 的三个问题：第一，记忆从哪里来，所以我设计了主动记忆采集；第二，记忆如何组织，所以我设计了短期记忆、摘要记忆、长期记忆、用户画像和成长轨迹；第三，记忆如何产生价值，所以我设计了行为模式发现和干预策略路由，把用户问题转化为轻量行动任务，并持续跟踪执行结果。

---

## 22. 后续扩展方向

## 22.1 18 天成长计划

作为 Intervention Package 接入。

---

## 22.2 更多方法库

增加：

* 情绪 ABC 记录
* 目标拆解法
* 复盘四问
* 番茄钟启动
* 暴露练习简化版
* 价值观澄清卡片

---

## 22.3 成长可视化

展示：

* 高频情绪变化
* 压力源变化
* 行动完成情况
* 行为模式变化

---

## 22.4 通用长期陪伴 Agent 框架

未来可迁移到：

* 学习教练
* 面试教练
* 职业规划教练
* 健身教练
* 习惯养成教练

---

## 23. 总结

Memory-Driven Growth Agent 的技术核心不是单纯调用大模型聊天，而是构建一个长期陪伴 Agent 的完整闭环：

```text
主动采集记忆
↓
分层组织记忆
↓
召回相关记忆
↓
发现行为模式
↓
匹配成长方法
↓
生成行动任务
↓
跟踪执行反馈
↓
更新长期画像
```

该设计既能体现 AI Agent 的工程能力，也能展示对长期记忆、用户画像、工作流编排和产品场景的深入理解。
