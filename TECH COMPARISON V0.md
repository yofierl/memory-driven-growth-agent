# Memory-Driven Growth Agent — 开源记忆系统技术选型对比 V0

> 基于 PRD V1 和 TECH DESIGN V1 的需求，对比当前 GitHub 最热门的开源记忆系统项目，
> 给出本项目技术选型建议。

---

## 1. 项目需求回顾

### 1.1 核心记忆需求

| # | 需求 | 来源 |
|---|------|------|
| 1 | 五层记忆架构（Short-Term / Summary / Long-Term / User Profile / Growth Story） | PRD §8.3 |
| 2 | 结构化情绪事件抽取（event/emotion/trigger/behavior/result + confidence） | PRD §8.2 |
| 3 | 主动记忆采集（Gap Detection + 追问） | PRD §8.2 |
| 4 | 多维度记忆召回（情绪/场景/触发/行为相似 + 目标相关） | PRD §8.4 |
| 5 | 行为模式发现（trigger→emotion→behavior→result 链路，≥3次触发） | PRD §8.5 |
| 6 | 记忆合并去重（相似事件不重复写入，更新 frequency + confidence） | TECH §13.2 |
| 7 | 记忆污染控制（confidence阈值、用户确认、证据溯源） | TECH §13.4 |
| 8 | 用户画像动态演化（多次证据才更新稳定特征） | TECH §13.3 |
| 9 | 干预策略路由（模式→方法→任务） | PRD §8.6 |
| 10 | 行动任务跟踪 + 周总结 | PRD §8.8-8.9 |

### 1.2 当前 Tech Design 选型

```
后端: FastAPI + Pydantic v2 + LangGraph
数据库: MongoDB（主存储） + Milvus（向量检索）
缓存: Redis
前端: React + Vite
LLM: Qwen / DeepSeek / OpenAI（抽象统一接口）
```

---

## 2. 开源记忆系统全景对比

### 2.1 候选项目总览

| 项目 | Stars | 许可证 | 核心定位 | 存储后端 |
|------|:---:|:---:|------|------|
| **Mem0** | ~55K | Apache 2.0 | 通用 AI Agent 记忆层 | Qdrant/ChromaDB/PGVector/Milvus… |
| **Letta** (原 MemGPT) | ~22.5K | Apache 2.0 | 有状态 Agent 平台 | PostgreSQL/SQLite + 向量库 |
| **Graphiti** (Zep) | ~24K | Apache 2.0 | 时序知识图谱引擎 | Neo4j/FalkorDB/Kuzu |
| **Supermemory** | ~23K | 部分开源 | 记忆 API 服务 | Cloudflare Workers + pgvector |
| **Cognee** | ~15-17K | Apache 2.0 | 知识图谱抽取管道 | Neo4j/NetworkX + LanceDB/Qdrant + SQLite/PG |
| **GBrain** | ~16K | MIT | 个人知识大脑 | PGLite/Supabase PG + pgvector |
| **ChromaDB** | ~18K | Apache 2.0 | 轻量向量数据库 | 嵌入式（DuckDB/SQLite） |

### 2.2 与本项目需求的匹配矩阵

| 需求 | Mem0 | Letta | Graphiti | Cognee | GBrain | ChromaDB |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| 结构化事件存储 | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | ❌ |
| 多层记忆架构 | ❌ | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| 主动记忆采集(Gap Detection) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 多维召回 | ✅ | ✅ | ✅ | ✅ | ✅ | 仅向量 |
| 行为模式发现 | ❌ | ❌ | ⚠️ | ⚠️ | ❌ | ❌ |
| 记忆合并去重 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 时序追踪 | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| 置信度/证据管理 | ⚠️ | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| 中文支持 | ✅ | ⚠️ | ⚠️ | ⚠️ | ❌ | ✅ |
| pip install 即用 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| MCP 协议支持 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

> ✅ 原生支持 · ⚠️ 可适配 · ❌ 不支持/需自建

**关键发现：没有任何一个开源项目能直接满足本项目的全部需求。**
尤其是「主动记忆采集(Gap Detection)」「行为模式发现」「置信度管理」这三个核心功能，
所有项目都需要自建。

---

## 3. 逐项目深度分析

### 3.1 Mem0 — 记忆基础设施的最佳参考

**架构亮点：**
```
add(messages) → LLM事实抽取 → MD5去重 → 向量嵌入 → (图实体提取)
search(query) → 语义 + BM25 + 实体匹配 → RRF融合 → Top-K
```

**对本项目的价值：**

| 可借鉴 | 说明 |
|--------|------|
| `memory.add()` API 设计 | 统一 CRUD 接口，metadata 灵活扩展 |
| V3 混合搜索 | 语义 + 关键词 + 实体匹配的多信号融合 |
| `user_id`/`agent_id`/`run_id` 隔离 | 记忆的多租户/会话隔离模式 |
| MD5 哈希去重 | 避免完全相同的记忆重复写入 |
| metadata 过滤 | 按 category/scenario/type 过滤记忆 |

**不适合直接使用的原因：**
- Mem0 的记忆模型是通用的 `{memory: text, metadata: json}`，不支持本项目所需的 **结构化 5 字段事件模型**（event/emotion/trigger/behavior/result + confidence）
- 没有 pattern discovery 能力
- 没有 gap detection（信息缺失检测）
- 如果强行套用，需要在 Mem0 之上包装大量业务逻辑，反而增加复杂度

**结论：作为 API 设计和检索策略的参考，不作为直接依赖。**

---

### 3.2 Letta — 分层记忆架构的最佳参考

**架构亮点：**
```
Core Memory (in-context blocks) → 始终在上下文窗口
Archival Memory (vector search)  → 按需检索
Conversation Recall               → 历史对话搜索
Sleep-time Compute                → 后台异步巩固记忆
```

**对本项目的价值：**

| 可借鉴 | 说明 |
|--------|------|
| 分层记忆模型 | 与本项目五层架构高度对应 |
| memory blocks 概念 | persona/human/custom blocks 类似于 User Profile |
| self-editing memory | Agent 自主更新记忆块，而非被动存储 |
| Sleep-time Compute | 后台异步处理，不影响对话延迟 |
| `memory_rethink` | 记忆巩固/重组的概念 |

**与本项目五层架构的映射：**
```
Letta                    本项目
Core Memory (persona)  → User Profile
Core Memory (human)    → Long-Term Memory（关键事实）
Archival Memory        → Long-Term Memory（全部事件）
Conversation Recall    → Short-Term Memory + Summary Memory
Files                  → 方法库 / 成长计划模板
```

**不适合直接使用的原因：**
- Letta 是完整的 Agent 平台，与 LangGraph 存在框架冲突
- 数据模型不匹配（Letta 用非结构化文本块，本项目需要结构化字段）
- 引入 Letta 相当于引入第二套 Agent 框架，增加复杂度

**结论：分层架构的参考蓝图，不作为直接依赖。其 `ai-memory-sdk` 可关注后续发展。**

---

### 3.3 Graphiti (Zep) — 时序知识图谱的有条件候选

**架构亮点：**
```
add_episode → extract_entities → resolve_entities → extract_relationships
            → resolve_edges → community detection

search → 语义搜索 + BM25 + 图遍历 → Rerank → 结果

每条边: valid_at / invalid_at / expired_at（双时序模型）
```

**对本项目的价值：**

| 可借鉴 | 说明 |
|--------|------|
| 双时序模型 | 记录"事实何时为真"+"系统何时知道"，适合追踪用户行为变化 |
| Episode → Entity → Relationship | 从对话中抽取实体和关系，天然适合模式发现 |
| 图遍历增强检索 | trigger→emotion→behavior→result 链路在图数据库中查询极其高效 |
| 社区检测 | 自动发现相关的记忆簇，类似行为模式聚类 |

**与本项目模式发现的天然契合：**

在 Neo4j/Cypher 中，行为模式发现变成了图查询：
```cypher
MATCH (t:Trigger)-[:CAUSES]->(e:Emotion)-[:LEADS_TO]->(b:Behavior)-[:RESULTS_IN]->(r:Result)
WHERE t.name = '任务压力过大' AND e.name = '焦虑' AND b.name = '刷视频回避'
RETURN count(*) AS frequency
```
比 MongoDB 聚合管道直观得多。

**不适合直接使用的原因（MVP 阶段）：**
- Neo4j 是额外的基础设施，部署复杂度显著增加
- Graphiti 的实体/关系模型需要大量适配才能匹配 5 字段事件模型
- P95 延时 <300ms 需要 Zep Cloud，自建需要调优

**结论：**
- **MVP 阶段不推荐**（太重）
- **V2 阶段强烈推荐**：当行为模式发现需要更复杂的图分析时，Graphiti + Neo4j 是最佳选择
- 可以在 MVP 阶段先用 MongoDB 聚合模拟简单模式发现，架构上预留切换到 Graphiti 的空间

---

### 3.4 Cognee — ECL 管道的设计参考

**架构亮点：**
```
Extract (30+ 数据源) → Cognify (chunk → classify → extract → summarize)
                     → Load (GraphDB + VectorDB + RelationalDB 三写)
                     
Pydantic DataPoint 模型驱动本体论
```

**对本项目的价值：**

| 可借鉴 | 说明 |
|--------|------|
| Pydantic 驱动的数据模型 | 用 Pydantic 定义情绪事件本体，与 FastAPI 技术栈一致 |
| ECL 管道概念 | Extract→Cognify→Load 的分阶段处理 |
| 三写架构 | 同时写入关系库+向量库+图库的同步机制 |
| `run_tasks` 并发控制 | asyncio.Semaphore 限流模式 |

**不适合直接使用的原因：**
- 定位为"通用数据管道"，不针对情绪/行为追踪场景
- 15-17K stars 中很多是通用 RAG 场景，与本项目需求差异大
- 引入 Cognee 相当于引入一套完整的数据处理框架，学习曲线陡

**结论：管道设计模式参考，不作为直接依赖。**

---

### 3.5 GBrain — 记忆巩固与自进化机制的最佳参考

**架构亮点：**
```
Layer 1: Markdown + Git（真值源，Compiled Truth + Timeline 双结构）
Layer 2: Hybrid Search（向量 + 全文 + RRF + Backlink加权）
Layer 3: Fat Skills（34个Agent工作流）
Dream Cycle: 夜间记忆巩固（去重 → 补充引用 → 修复链接 → 重建索引）
Tier System: 实体按提及次数自动升级（Tier 3 → Tier 2 → Tier 1）
自布线知识图谱: 纯正则提取实体关系，零LLM调用
```

**对本项目的价值：**

| 可借鉴 | 说明 |
|--------|------|
| **Dream Cycle** | 夜间记忆巩固是本项目最值得借鉴的概念！ |
| Compiled Truth + Timeline | 顶部是最佳理解，底部是不可篡改的证据链 |
| Tier 系统 | 记忆按 repeated evidence 自动升级，与本项目"≥3次才形成模式"理念一致 |
| RRF 混合搜索 | Reciprocal Rank Fusion，比纯向量搜索 Recall 提升显著 |
| "Fat Skills" 设计 | 智能在 Markdown prompt 文件中，框架极薄 |
| Minions vs Subagent | 能确定性处理的不调 LLM，成本控制 |

**Dream Cycle 在本项目的应用：**

GBrain 的 Dream Cycle 与本项目需求几乎完全对应：

```
GBrain Dream Cycle              本项目可实现的 Nightly Consolidation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
拉取标记帖子                     扫描当日新增 emotion_event 记忆
去重合并                         合并相似记忆，更新 frequency
补充引用                         补全 evidence_memory_ids
修复损坏引用                     标记 confidence < 0.6 的记忆待复审
重建索引                         更新向量索引 + 用户画像
                                 检测是否出现 ≥3 次的行为模式
                                 生成候选 Pattern
```

**不适合直接使用的原因：**
- GBrain 是 Garry Tan 的个人系统，不是通用框架
- 强依赖 Markdown + Git 工作流，与本项目数据库架构不兼容
- TypeScript 实现，本项目是 Python 技术栈
- 单操作者设计，不原生支持多用户

**结论：设计哲学和 Dream Cycle 模式最重要的参考源，代码层面仅作概念参考。**

---

### 3.6 ChromaDB — 向量数据库的轻量替代

**与本项目 Tech Design 中 Milvus 的对比：**

| 维度 | Milvus | ChromaDB | pgvector |
|------|--------|----------|----------|
| 部署方式 | 多组件微服务（etcd+MinIO+Pulsar） | `pip install chromadb` | PostgreSQL 扩展 |
| 内存占用 | 4GB+ | ~200-500MB | ~100MB |
| 学习成本 | 高 | 极低 | 低（会 SQL 即可） |
| Python 集成 | 中等 | ⭐⭐⭐⭐⭐ 原生 | ⭐⭐⭐⭐ |
| MVP 适用性 | ❌ 过度设计 | ✅ 最佳 | ✅ 最佳 |
| 生产扩展性 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 10万向量性能 | 过剩 | 够用 | 够用 |

**结论：MVP 阶段推荐用 ChromaDB 或 pgvector 替代 Milvus，V2 如有性能需求再迁移到 Milvus。**

---

## 4. 技术选型方案对比

### 方案 A：纯自建 + 概念参考（🏆 推荐）

```
FastAPI + LangGraph
    ↓
PostgreSQL + pgvector（单一数据库，结构化 + 向量检索）
    ↓
Redis（会话缓存 + 短期记忆）
    ↓
自定义 Memory Service（参考 Mem0 API + Letta 分层 + GBrain Dream Cycle）
    ↓
React + Vite
```

| 优势 | 劣势 |
|------|------|
| 单一数据库，部署最简单 | 所有记忆逻辑需要从零编写 |
| 完全掌控数据模型，5字段事件原生支持 | 没有现成的记忆管理 UI |
| 面试展示价值最高（"我设计的记忆架构"） | Pattern discovery 需要自己实现 |
| pgvector 成熟稳定，SQL 操作直观 | 图查询能力弱（V2 可加） |
| 架构最简洁，MVP 开发最快 | |

**适配本项目的数据库设计核心：**

```sql
-- 一条 SQL 同时搞定结构化存储 + 向量检索
CREATE TABLE memories (
    memory_id UUID PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    type VARCHAR NOT NULL,          -- emotion_event / goal / preference / reflection
    scenario VARCHAR,
    event TEXT,
    emotion VARCHAR,
    trigger_field VARCHAR,
    behavior VARCHAR,
    result TEXT,
    importance INTEGER DEFAULT 1,
    confidence FLOAT DEFAULT 0.0,
    evidence_ids UUID[] DEFAULT '{}',
    source VARCHAR,                 -- conversation / checkin / reflection
    embedding vector(1536),         -- pgvector 字段
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 向量索引
CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops);

-- 混合搜索：语义 + 结构化过滤
SELECT *, 1 - (embedding <=> $query_embedding) AS similarity
FROM memories
WHERE user_id = $user_id
  AND type = 'emotion_event'
  AND similarity > 0.7
ORDER BY embedding <=> $query_embedding
LIMIT 10;
```

---

### 方案 B：Mem0 作记忆后端 + 自建业务层

```
FastAPI + LangGraph
    ↓
Mem0（处理存储 + 检索，作为 Memory Infrastructure）
    ↓
自定义 LangGraph Nodes（GapDetection / PatternDiscovery / InterventionRouting）
    ↓
MongoDB（用户/对话/任务等业务数据）
    ↓
React + Vite
```

| 优势 | 劣势 |
|------|------|
| 记忆存储/检索开箱即用 | Mem0 的通用数据模型需要大量适配 |
| Mem0 的混合搜索（语义+BM25+实体）成熟 | 5字段结构化事件存到 metadata 不够优雅 |
| API 设计成熟，有社区支持 | 面试中可能被问"为什么用现成的而不是自建" |
| 后续可无缝迁移到 Mem0 Platform | 引入额外依赖，调试复杂度增加 |

**Mem0 适配本项目的数据模型方案：**

```python
# 将结构化事件存入 Mem0 的 memory + metadata
m.add(
    messages=[...],
    user_id="user_123",
    metadata={
        "type": "emotion_event",
        "scenario": "秋招准备",
        "event": "准备面试时学不进去",
        "emotion": "焦虑",
        "trigger": "任务压力过大",
        "behavior": "刷视频回避",
        "result": "学习中断并产生自责",
        "importance": 4,
        "confidence": 0.82,
        "source": "conversation"
    }
)
# Mem0 的 memory 字段存文本摘要，结构化字段存 metadata
# 问题：Mem0 的 search 主要基于 memory 文本，metadata 只做过滤不做语义匹配
```

---

### 方案 C：Graphiti 知识图谱 + 自建管道

```
FastAPI + LangGraph
    ↓
Graphiti（Episode提取 → 实体解析 → 关系抽取 → 图存储）
    ↓
Neo4j（知识图谱） + pgvector（向量检索）
    ↓
MongoDB（业务数据）
    ↓
React + Vite
```

| 优势 | 劣势 |
|------|------|
| 图查询对行为模式发现天然高效 | Neo4j 增加部署复杂度 |
| 时序模型追踪行为随时间变化 | MVP 阶段严重过度设计 |
| 社区检测自动发现记忆簇 | 学习曲线最陡 |
| V2 阶段最有扩展潜力 | 实体/关系模型适配工作量大 |

**结论：V2 候选方案。MVP 不推荐，但可以在架构上预留图数据库接口。**

---

### 方案 D：保持原 Tech Design（MongoDB + Milvus）

```
FastAPI + LangGraph
    ↓
MongoDB（主存储） + Milvus（向量检索）
    ↓
Redis（缓存）
    ↓
React + Vite
```

| 优势 | 劣势 |
|------|------|
| 已是现有设计，无需改动 | Milvus 对 MVP 过度设计（需 etcd+MinIO+Pulsar） |
| MongoDB 文档模型灵活，适合嵌套 JSON | 两套数据库运维成本翻倍 |
| Milvus 扩展性最强 | MongoDB 文本检索弱于 PostgreSQL |
| 已在 Tech Design 中完成设计 | 向量和结构化数据分离，查询需要两次请求 |

---

## 5. 综合推荐

### 5.1 MVP 阶段推荐：方案 A（PostgreSQL + pgvector）

| 对比维度 | 方案 A (PG+pgvector) | 方案 B (Mem0) | 方案 D (Mongo+Milvus) |
|------|:---:|:---:|:---:|
| 部署复杂度 | ⭐ 最低 | ⭐⭐ 中等 | ⭐⭐⭐ 高 |
| 开发效率 | ⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐⭐ 最高 | ⭐⭐⭐ 中等 |
| 面试展示价值 | ⭐⭐⭐⭐⭐ 最高 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 高 |
| 数据模型灵活度 | ⭐⭐⭐⭐ SQL+JSONB | ⭐⭐⭐ metadata | ⭐⭐⭐⭐⭐ 文档 |
| 向量检索能力 | ⭐⭐⭐ 够用 | ⭐⭐⭐⭐ 成熟 | ⭐⭐⭐⭐⭐ 最强 |
| 未来扩展性 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**推荐理由：**

1. **单一数据库** — 一个 PostgreSQL 实例同时处理结构化存储和向量检索，不需要维护 MongoDB + Milvus 两套系统。`docker compose up` 一行命令即可启动全部后端依赖。

2. **面试展示价值最高** — "为什么选择 pgvector 而不是 Milvus？因为 MVP 阶段数据量在 10 万条以内，pgvector 的 IVFFlat 索引完全够用，且避免了多组件微服务的运维复杂度。当数据量达到百万级且 QPS 超过 500 时，我会迁移到 Milvus 并利用其分布式索引能力。" — 这段话展示了工程判断力。

3. **SQL 的灵活性** — 行为模式发现可以用 SQL 窗口函数 + JSONB 聚合实现，比 MongoDB 的聚合管道更直观：
   ```sql
   SELECT trigger_field, emotion, behavior, result, COUNT(*) as freq
   FROM memories
   WHERE user_id = $1 AND type = 'emotion_event'
     AND created_at > NOW() - INTERVAL '30 days'
   GROUP BY trigger_field, emotion, behavior, result
   HAVING COUNT(*) >= 3;
   ```

4. **与 LangGraph 天然配合** — 每个 LangGraph Node 可以直接执行 SQL 查询和向量搜索，不需要跨数据库协调事务。

### 5.2 各开源项目的借鉴优先级

| 优先级 | 项目 | 借鉴内容 | 借鉴方式 |
|:---:|------|------|------|
| 🥇 | **GBrain** | Dream Cycle（夜间记忆巩固）、Tier系统（≥3次升级）、Compiled Truth + Timeline | 概念参考 + 架构设计 |
| 🥇 | **Letta** | 五层记忆分级模型、memory blocks 概念、Sleep-time Compute | 架构参考 |
| 🥈 | **Mem0** | `add()`/`search()` API 设计、V3 混合搜索（语义+BM25+实体）、metadata 过滤 | API 设计参考 |
| 🥈 | **Graphiti** | 双时序模型、Episode→Entity→Relationship 管道、图遍历增强检索 | V2 设计预留 |
| 🥉 | **Cognee** | ECL 管道概念、Pydantic DataPoint 驱动本体 | 管道设计参考 |
| 🥉 | **ChromaDB** | 嵌入式向量库的极简 API 设计 | 备选向量库方案 |

### 5.3 调整后的 MVP 技术栈

```yaml
后端框架: FastAPI + Pydantic v2
Agent编排: LangGraph
数据库:   PostgreSQL 16 + pgvector + JSONB  # 替代 MongoDB + Milvus
缓存:     Redis
前端:     React + Vite
LLM:      Qwen / DeepSeek / OpenAI（LLMService 统一抽象）
部署:     Docker Compose（PostgreSQL + Redis + FastAPI + 前端）
```

**相比原 Tech Design 的改动：**
- MongoDB → PostgreSQL + JSONB（结构化查询更强，单一数据库）
- Milvus → pgvector（MVP 数据量足够，免去 etcd/MinIO/Pulsar 组件）
- 其他不变

### 5.4 不建议引入的项目

| 项目 | 原因 |
|------|------|
| **Mem0** 作为依赖 | 通用模型与 5 字段事件不匹配，包装成本 > 自建成本 |
| **Letta** 作为依赖 | 完整 Agent 平台，与 LangGraph 框架冲突 |
| **Supermemory** | 部分闭源，不适合作为作品集项目的依赖 |
| **Cognee** 作为依赖 | 通用数据管道，与本项目需求差异大，学习曲线陡 |
| **Graphiti** 在 MVP | Neo4j 部署重，MVP 阶段数据量和查询复杂度不需要图数据库 |

---

## 6. Dream Cycle 设计（本项目核心创新点）

借鉴 GBrain 的 Dream Cycle，这是本项目在面试中的核心亮点：

### 6.1 夜间记忆巩固流程

```
每天凌晨 2:00 触发（Cron Job）

Phase 1: 记忆扫描
├── 拉取昨日所有新增 emotion_event 记忆
├── 按 (user_id, scenario) 分组
└── 标记 confidence < 0.6 的待复审记忆

Phase 2: 去重合并
├── 计算组内记忆的文本相似度
├── 相似度 > 0.85 → 合并为一条，更新 frequency + last_seen_at
└── 更新 evidence_memory_ids

Phase 3: 模式发现
├── 按 (trigger, emotion, behavior, result) 聚合
├── COUNT >= 3 → 生成候选 Pattern
├── 分配 confidence = f(frequency, recency, evidence_count)
└── 写入 patterns 表，status = 'detected'

Phase 4: 画像更新
├── 检查是否存在 ≥5 次重复出现的 trait 证据
├── 达到阈值 → 更新 user_profiles
└── 未达到 → 仅追加 evidence，不修改画像

Phase 5: 索引重建
├── 新记忆批量生成 embedding
├── 更新 pgvector IVFFlat 索引
└── 清理 90 天前的低 importance(≤2) 记忆的向量（保留结构化记录）
```

### 6.2 Dream Cycle 的面试讲法

> "我参考了 GBrain 的 Dream Cycle 设计，在本项目中实现了夜间记忆巩固机制。
> 白天 Agent 只做核心对话和实时记忆抽取，不做重计算。
> 凌晨通过 Cron Job 触发记忆合并、模式发现和画像更新，把重计算从用户请求路径上剥离。
> 这保证了对话延迟不受影响，同时记忆质量随时间持续提升。"

---

## 7. 开发阶段建议

### Phase 1: 基础架构 + 记忆 CRUD（2-3天）
- Docker Compose 搭建 PG + Redis
- FastAPI 项目结构 + LLMService
- Chat API + Memory CRUD API
- **参考 Mem0 的 API 设计风格**

### Phase 2: 主动记忆采集（2-3天）
- GapDetectionNode
- Follow-up question 生成
- 记忆抽取 Prompt 设计
- **参考 Mem0 的 metadata 扩展模式**

### Phase 3: 多层记忆 + 召回（2-3天）
- MemoryRetrievalNode（pgvector 语义搜索）
- Short-Term / Summary / Long-Term 分层
- 用户画像 CRUD
- **参考 Letta 的分层架构 + Mem0 的 V3 混合搜索**

### Phase 4: 行为模式发现（2-3天）
- SQL 聚合 + LLM 验证的 Pattern Discovery
- Pattern 确认/拒绝 API
- **参考 Graphiti 的图查询思路，用 SQL 模拟**

### Phase 5: 干预策略 + 行动任务（2-3天）
- 方法库初始化
- InterventionRoutingNode
- TaskGeneration + 跟踪
- **纯自建，项目核心差异化能力**

### Phase 6: Dream Cycle + 周总结（2-3天）
- 夜间记忆巩固 Cron Job
- 周总结生成
- **参考 GBrain 的 Dream Cycle + Compiled Truth 模式**

---

## 8. 总结

| 决策 | 结论 |
|------|------|
| 是否直接用 Mem0？ | ❌ 不直接依赖，但 API 设计全量参考 |
| 是否直接用 Letta？ | ❌ 框架冲突，但分层架构全量参考 |
| 是否直接用 Graphiti？ | ❌ MVP 太重，V2 候选，时序模型概念参考 |
| MongoDB + Milvus → PG + pgvector？ | ✅ 推荐切换，单一数据库 + 够用原则 |
| 最大借鉴源？ | 🥇 GBrain（Dream Cycle + Tier系统） |
| 面试核心亮点？ | 五层记忆架构 + Dream Cycle + 结构化情绪事件模型 |

**一句话：**
> 没有一个开源项目能直接满足本项目的需求，但 GBrain 的设计哲学 + Letta 的分层模型 + Mem0 的 API 风格 + 自建的领域模型 = 最佳方案。

---

*文档版本: V0 | 2026-06-04 | 全量开源项目调研对比（全自建推荐方案）*
