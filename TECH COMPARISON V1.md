# Memory-Driven Growth Agent — 技术选型 V2

> 目标：以最少开源项目为基座，做最小适配修改，跑通核心闭环。

---

## 1. 一句话结论

**以 Mem0 为记忆基础设施，以 LangGraph 编排业务节点。只建 4 个东西。**

---

## 2. 为什么选 Mem0 作基座

把项目的技术需求拆开看：

| 需求 | 谁来做 | 说明 |
|------|:---:|------|
| 对话→结构化记忆抽取 | **Mem0** | `add()` 自动调用 LLM 提取事实 |
| 向量嵌入 + 语义搜索 | **Mem0** | 内置 embedding + `search()` |
| 记忆去重 | **Mem0** | MD5 哈希自动去重 |
| 用户隔离 | **Mem0** | `user_id` 原生支持 |
| 混合检索 | **Mem0** | V3：语义 + BM25 + 实体匹配 |
| 5字段结构化事件 | **自己** | 存到 Mem0 的 `metadata` 字段 |
| 信息缺失检测 + 追问 | **自己** | GapDetectionNode（1 个 LangGraph 节点） |
| 行为模式发现 | **自己** | SQL/LLM 聚合（1 个节点） |
| 干预策略路由 | **自己** | 方法库匹配（1 个节点） |
| 行动任务生成 + 跟踪 | **自己** | tasks 表 + TaskGenerationNode |

**Mem0 吃掉 80% 的基础工作量，你只做 20% 的领域特有逻辑。**

其他项目为什么不适合做基座：

| 项目 | 不适合原因 |
|------|------|
| Letta | 完整 Agent 平台，与 LangGraph 框架冲突 |
| Graphiti | 需要 Neo4j，MVP 太重 |
| Cognee | 通用数据管道，和你的需求差异大 |
| GBrain | TypeScript，个人系统不是通用框架，Python 技术栈不兼容 |

---

## 3. 架构（复用你已有的 Milvus + MongoDB）

```
pip install mem0 pymilvus langgraph fastapi

┌──────────────────────────────────────────────┐
│               FastAPI Server                 │
│                   │                          │
│          LangGraph Workflow                  │
│                                              │
│   GapDetectionNode ──→ PatternDiscovery      │
│          │                    │              │
│          ▼                    ▼              │
│   ┌──────────────┐    InterventionRouting    │
│   │    Mem0      │           │              │
│   │  (记忆基建)   │    TaskGeneration         │
│   │              │           │              │
│   │ add/search/  │           ▼              │
│   │ get_all      │    ┌──────────┐          │
│   └──────┬───────┘    │ MongoDB  │          │
│          │            │ (业务数据)│          │
│     Milvus            │          │          │
│   (向量检索)           │ users    │          │
│   (已部署 ✓)           │ convers. │          │
│                       │ patterns │          │
│                       │ tasks    │          │
│                       │ methods  │          │
│                       │ profiles │          │
│                       │ summaries│          │
│                       └──────────┘          │
│   ┌──────────┐                              │
│   │  Redis   │  会话缓存 / 短期记忆 / 任务状态│
│   │ (已部署 ✓)│                              │
│   └──────────┘                              │
└──────────────────────────────────────────────┘
```

**职责划分：**

| 组件 | 存什么 | 为什么 |
|------|------|------|
| **Mem0 → Milvus** | 记忆文本 + embedding + metadata（5字段事件） | Mem0 管记忆全生命周期，Milvus 做向量检索 |
| **MongoDB** | users / conversations / patterns / tasks / methods / profiles / summaries | 原 Tech Design 的 8 个 Collection，现在只存业务数据 |
| **Redis** | 会话缓存 / 短期对话窗口 / 当前任务状态 | 原 Tech Design 不变 |

**对比原 Tech Design 的简化：**

| 原设计 | 新方案 | 变化 |
|------|------|------|
| MongoDB `memories` collection + 自建 CRUD | **Mem0 管记忆，不需要 MongoDB memories 表** | 少写 1 个 Repository + 1 个 Service |
| Milvus `growth_memories` collection + 自建向量服务 | **Mem0 自动管理 Milvus collection** | 少写 VectorService + embedding 管道 |
| 需自己实现 MongoDB ↔ Milvus 同步 | **Mem0 内部处理** | 消除数据一致性问题 |

---

## 4. 核心改动：把 5 字段事件存进 Mem0

Mem0 的 `add()` 原生支持 `metadata` 字段，正好用来存放结构化的情绪事件。

### 4.1 Mem0 配置（对接你已有的 Milvus + DeepSeek）

```python
from mem0 import Memory

m = Memory.from_config({
    "vector_store": {
        "provider": "milvus",
        "config": {
            "collection_name": "growth_memories",
            "url": "http://localhost:19530",     # 你已有的 Milvus
            "embedding_model_dims": 1024,        # 和 embedder 维度一致
        }
    },
    "llm": {
        "provider": "deepseek",
        "config": {
            "model": "deepseek-chat",
            "temperature": 0.1,
            "max_tokens": 2000,
        }
    },
    "embedder": {
        "provider": "openai",  # DeepSeek / SiliconFlow / 豆包 的 embedding API
        "config": {
            "model": "text-embedding-v4",
            "api_key": "your-key",
            "openai_base_url": "https://api.siliconflow.cn/v1",
            "embedding_dims": 1024,
        }
    }
})

# ===== 核心：把 5 字段结构化事件存入 Mem0 metadata =====

def store_emotion_event(user_id: str, messages: list[dict], event_data: dict):
    """将 PRD §8.2 的情绪事件存入 Mem0"""
    m.add(
        messages,
        user_id=user_id,
        metadata={
            "type": "emotion_event",
            "scenario": event_data.get("scenario"),
            "event": event_data.get("event"),
            "emotion": event_data.get("emotion"),
            "trigger": event_data.get("trigger"),
            "behavior": event_data.get("behavior"),
            "result": event_data.get("result"),
            "importance": event_data.get("importance", 3),
            "confidence": event_data.get("confidence", 0.0),
            "source": "conversation"
        }
    )

# ===== 多维召回：按 metadata 过滤 =====

def recall_by_emotion(user_id: str, emotion: str, limit: int = 5):
    """按情绪类型召回历史记忆"""
    return m.search(
        query=f"用户感到{emotion}",
        user_id=user_id,
        filters={"AND": [{"type": "emotion_event"}, {"emotion": emotion}]},
        top_k=limit
    )

def recall_by_scenario(user_id: str, scenario: str, limit: int = 5):
    """按场景召回"""
    return m.search(
        query=f"关于{scenario}的经历",
        user_id=user_id,
        filters={"AND": [{"type": "emotion_event"}, {"scenario": scenario}]},
        top_k=limit
    )
```

**这 30 行代码就完成了原 Tech Design 中 MemoryExtractionNode + MemoryRetrievalNode + 向量存储 三个模块的工作。**

---

## 5. 你实际需要建的东西（只有 4 个）

### 5.1 GapDetectionNode（~80 行）

输入端：用户说了一句信息不全的话。输出端：判断缺哪些字段，生成一个追问。

```python
# 这是一个 LangGraph Node，不是基础设施
# Mem0 不管这个，LLM prompt 就搞定

GAP_DETECTION_PROMPT = """
从用户输入中抽取情绪事件的部分字段，判断缺失。

输出 JSON：
{
  "extracted": {"event": null, "emotion": "焦虑", "trigger": null, "behavior": null, "result": null},
  "missing_fields": ["event", "trigger", "behavior"],
  "need_follow_up": true,
  "follow_up_question": "最近有没有一件事让这种焦虑特别明显？"
}

规则：一次只追问一个最关键缺失字段。不要像问卷。不要贴诊断标签。
"""
```

### 5.2 PatternDiscoveryNode（~100 行）

输入端：`mem0.get_all()` 拉出用户近期所有 `emotion_event`。输出端：≥3 次出现的重复链路。

```python
# 核心逻辑：按 (trigger, emotion, behavior, result) 聚合
# Mem0 的 search 负责召回候选记忆
# 剩下就是简单的分组计数

def discover_patterns(user_id: str):
    memories = m.get_all(user_id=user_id, filters={"type": "emotion_event"})
    
    # 按四元组聚合
    from collections import Counter
    chains = Counter()
    for mem in memories:
        meta = mem.get("metadata", {})
        key = (meta.get("trigger"), meta.get("emotion"), 
               meta.get("behavior"), meta.get("result"))
        chains[key] += 1
    
    # 筛选 ≥3 次的
    return [
        {"trigger": k[0], "emotion": k[1], "behavior": k[2], 
         "result": k[3], "frequency": v}
        for k, v in chains.items() if v >= 3
    ]
```

### 5.3 InterventionRoutingNode（~60 行）

输入端：检测到的 pattern。输出端：从方法库匹配一个方法。

```python
METHOD_LIBRARY = [
    {"name": "15分钟启动法", "target": ["拖延", "回避", "任务压力"]},
    {"name": "认知记录表",   "target": ["内耗", "反复想太多", "自我否定"]},
    {"name": "注意力回收",   "target": ["高敏感", "在意他人评价"]},
    {"name": "人生意义写作", "target": ["迷茫", "方向不清"]},
]

def route_intervention(pattern: dict) -> dict:
    # 简单关键词匹配 + LLM 兜底
    for method in METHOD_LIBRARY:
        if any(t in str(pattern.values()) for t in method["target"]):
            return method
    return {"name": "LLM自定义建议", "target": []}
```

### 5.4 TaskGenerationNode（~50 行）

输入端：推荐的方法。输出端：一个用户今天就能执行的小任务。

```python
def generate_task(method: dict, user_context: str) -> dict:
    # LLM prompt：把方法转化为具体的、15分钟内可完成的动作
    # 原则：小到用户无法拒绝
    ...
```

---

## 6. 完整 LangGraph 流程（最简版）

```python
from langgraph.graph import StateGraph, END
from mem0 import Memory

m = Memory.from_config({...})  # 上面的配置

class AgentState(TypedDict):
    user_id: str
    user_input: str
    messages: list
    risk_level: str
    missing_fields: list
    follow_up_question: str
    retrieved_memories: list
    detected_patterns: list
    recommended_method: dict
    generated_task: dict
    assistant_response: str

def retrieval_node(state: AgentState) -> AgentState:
    """召回相关记忆（Mem0 一行搞定）"""
    result = m.search(state["user_input"], user_id=state["user_id"], top_k=5)
    state["retrieved_memories"] = result.get("results", [])
    return state

def gap_detection_node(state: AgentState) -> AgentState:
    """检测信息缺失 → LLM prompt"""
    ...

def response_node(state: AgentState) -> AgentState:
    """生成回复，可选择追问/反馈模式/行动建议"""
    ...

def memory_extraction_node(state: AgentState) -> AgentState:
    """抽取结构化记忆 → 调用 store_emotion_event()"""
    ...

def pattern_node(state: AgentState) -> AgentState:
    """模式发现 → discover_patterns()"""
    ...

# LangGraph 编排
workflow = StateGraph(AgentState)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("gap_detection", gap_detection_node)
workflow.add_node("response", response_node)
workflow.add_node("memory_extraction", memory_extraction_node)
workflow.add_node("pattern_discovery", pattern_node)
# ... edges

app = workflow.compile()
```

**总代码量预估：核心节点 ~400 行 + API 层 ~200 行 + 前端 ~500 行 ≈ 1500 行以内跑通 MVP。**

---

## 7. 与原 Tech Design 的差异总结

| 模块 | 原设计 | 新方案 | 省了什么 |
|------|--------|--------|------|
| 记忆存储 | MongoDB `memories` 表 + 自建 CRUD | **Mem0 → Milvus** | MemoryRepository / MemoryService 不用写 |
| 向量检索 | Milvus + 自建 VectorService | **Mem0 内部调 Milvus** | VectorService 不用写 |
| MongoDB | 管全部数据（含 memories） | **只管业务数据**（users/conversations/patterns/tasks...） | 少 1 个 Collection |
| 记忆抽取 | 自建 MemoryExtractionNode + Prompt | **Mem0.add() 自动调 LLM** | 不用写抽取 Prompt + JSON 解析 |
| 记忆去重 | 自建 merge 逻辑 | **Mem0 MD5 去重** | 去重逻辑不用写 |
| 混合搜索 | MongoDB 文本 + Milvus 向量，需手动融合 | **Mem0.search() 内置语义+BM25+实体 RRF 融合** | 不用自己实现搜索融合 |
| 数据同步 | 需保证 MongoDB ↔ Milvus 一致性 | **Mem0 内部管理，一致性问题消除** | 无 |
| API 层 | 自建 /api/memories CRUD | **Mem0 原生 add/search/get/delete** | 少写 ~4 个 endpoint |
| 基础设施 | MongoDB + Milvus + Redis + etcd + MinIO + Pulsar | **MongoDB + Milvus + Redis**（你已有的不变） | etcd + MinIO + Pulsar 仍然需要（Milvus 依赖） |

---

## 8. 开发阶段重估

| Phase | 内容 | 预估时间 | 涉及组件 |
|-------|------|:---:|------|
| 1 | Mem0 + Milvus 配置 + MongoDB 连接 + FastAPI 骨架 | 0.5天 | mem0 + pymilvus + motor |
| 2 | Chat API + Mem0 存取 + 基础对话闭环 | 1天 | Phase 1 |
| 3 | GapDetection + 追问逻辑 | 1天 | Phase 2 |
| 4 | PatternDiscovery + MongoDB patterns 表 | 1天 | Phase 3 |
| 5 | 方法库 + TaskGeneration + 跟踪 + 周总结 | 1天 | Phase 4 |
| 6 | 前端聊天页 + 记忆页 + 模式页 | 1-2天 | Phase 2 |
| **合计** | | **5-6.5 天** | |

> Phase 1 从 1 天缩到 0.5 天——Milvus 已经在跑了，只需要配 Mem0 连接字符串。

比原 Tech Design 的 6 Phase × 2-3 天 ≈ 12-18 天，**工期减半**。

---

## 9. 面试讲法（关键）

> "项目用了 Mem0 作为记忆基础设施，但我没有停留在调 API。核心创新在三个方面：
>
> 第一，我在 Mem0 的通用记忆模型之上，定义了一套 5 字段结构化情绪事件本体（event/emotion/trigger/behavior/result + confidence），让记忆从纯文本变成可聚合、可分析的结构化数据。
>
> 第二，我设计了 GapDetection 机制——LLM 不只看用户说了什么，还看用户没说什么，主动追问缺失字段。这是 Mem0 本身不提供的。
>
> 第三，我基于结构化事件实现了行为模式发现——当 trigger→emotion→behavior→result 的链路出现 ≥3 次，系统自动生成候选 Pattern。这是纯向量搜索做不到的。
>
> 选择 Mem0 而不是从零写存储层，是工程判断：不做无意义的重复造轮子，把精力集中在领域特有的记忆采集和模式发现上。"

---

## 10. 总结

| 决策 | 结论 |
|------|------|
| 基座项目 | **Mem0**（唯一的直接依赖） |
| 向量存储 | ChromaDB（Mem0 内置支持，嵌入式零配置） |
| LLM | DeepSeek / Qwen / 豆包（Mem0 原生支持） |
| Agent 编排 | LangGraph（不变） |
| 业务数据库 | SQLite（MVP）/ PostgreSQL（生产） |
| 需要自建 | 4 个 LangGraph 节点 + 方法库 + 前端页面 |
| 不需要建 | 记忆 CRUD、向量检索、去重、混合搜索、embedding |

**核心思路：Mem0 是地基，你只建房子。不挖地基。**

---

*文档版本: V2 | 2026-06-04 | 基于 Mem0 + LangGraph 方案*
