# AGENTS.md

This file gives coding agents project-specific instructions for **Memory-Driven Growth Agent**.

## Project Positioning

This project is an AI Agent / LLM application portfolio project for a memory-driven growth coaching system.

The product is **not** a psychotherapy replacement, medical diagnosis tool, crisis intervention service, or generic emotional chatbot. The core value is:

```text
structured memory collection
-> long-term memory retrieval
-> repeated behavior pattern discovery
-> intervention method routing
-> lightweight action task generation
-> task feedback and memory update
```

Keep the implementation focused on this loop.

## MVP Scope

This list expands PRD V1.md §7.2 into implementation-level items for coding agents.

MVP must implement only the smallest demonstrable closed loop:

1. Free-form user conversation.
2. Short-term context reading.
3. Structured emotion event extraction.
4. Missing-field detection and one-question follow-up.
5. Long-term memory storage.
6. Historical memory retrieval.
7. Candidate pattern discovery based on at least 3 evidence memories.
8. Pattern evidence display and user confirmation / rejection.
9. Intervention method matching.
10. Lightweight action task generation.
11. Completed / failed task feedback recording.
12. Memory view / edit / delete.
13. High-risk input safety flow.

Do **not** implement these in MVP unless explicitly requested:

1. Redis session cache, rate limiting, or task cache.
2. Full weekly summary page.
3. 18-day growth plan.
4. Growth Story generation.
5. Dynamic advanced user profile evolution.
6. Multi-session management.
7. Growth report export.
8. Mobile reminders.

If a feature is not needed for the MVP loop, defer it.

## Architecture Decisions

Use the current architecture from `TECH DESIGN V1.md`:

```text
FastAPI
Pydantic v2
LangGraph
MongoDB
Milvus / Vector Store
React + Vite
```

### Storage Responsibilities

MongoDB is the structured memory and business data source of truth.

MongoDB stores:

```text
users
conversations
memories
user_profiles
patterns
tasks
methods
summaries (P1)
```

Milvus stores semantic retrieval indexes only. It must not become the only memory store.

Each vector record must be traceable to a MongoDB `memory_id` / `embedding_id`. When memory is deleted or modified, the vector index must be deleted, invalidated, or regenerated accordingly.

## Open-Source Memory Projects

Do not replace the MVP architecture with Mem0, Letta, Graphiti, Cognee, or similar open-source memory / agent platforms.

These projects may be used as design references only.

The project should expose a stable `MemoryService` interface:

```text
add_memory(memory)
search_memories(query, filters, top_k)
list_memories(user_id, filters)
update_memory(memory_id, patch)
delete_memory(memory_id)
```

MVP implementation:

```text
MongoMilvusMemoryProvider
```

Possible P2 implementations:

```text
Mem0MemoryProvider
LangMemMemoryProvider
```

Agent nodes must depend on `MemoryService`, not directly on third-party SDKs.

## LangGraph Workflow

The workflow must use conditional branching, not a fixed linear chain.

Expected MVP flow:

```text
START
-> RiskDetectionNode
   -> high risk: SafetyResponseNode -> END
-> MemoryRetrievalNode
-> GapDetectionNode
   -> need_follow_up=true: ResponsePlannerNode -> ResponseGenerationNode -> MemoryExtractionNode -> MemoryUpdateNode -> END
-> ResponsePlannerNode
-> ResponseGenerationNode
-> MemoryExtractionNode
-> MemoryUpdateNode
-> PatternDiscoveryNode
   -> no candidate pattern: END
   -> candidate not confirmed: PatternFeedbackPrompt -> END
-> InterventionRoutingNode
-> TaskGenerationNode
-> END
```

Rules:

1. High-risk input must not continue through ordinary growth coaching.
2. Missing information should trigger one natural follow-up question, not a questionnaire.
3. Pattern discovery must cite at least 3 `evidence_memory_ids`.
4. Rejected patterns must not trigger intervention routing or task generation.
5. Tasks should be specific, low difficulty, and usually completable in 15-30 minutes.

## Core Data Shape

Emotion event memory should preserve these fields:

```json
{
  "type": "emotion_event",
  "scenario": "string",
  "event": "string",
  "emotion": "string",
  "trigger": "string",
  "behavior": "string",
  "result": "string",
  "importance": 1,
  "confidence": 0.8,
  "source": "conversation | checkin | reflection"
}
```

Only save information that is explicitly stated by the user or inferred with high confidence.

Do not save:

1. Medical diagnosis labels.
2. Low-confidence personality judgments.
3. Ordinary small talk unrelated to growth.
4. Sensitive guesses without evidence.
5. Information the user asked to delete.

## Safety Requirements

Risk levels:

```text
none: ordinary growth conversation
low: negative emotion, no self-harm / suicide / violence intent
medium: strong hopelessness, self-denial, or vague danger expression
high: self-harm, suicide, harm to others, explicit dangerous plan, or imminent risk
```

For `high` risk:

1. Enter `SafetyResponseNode`.
2. Do not generate growth tasks.
3. Do not update normal user profile.
4. Do not use the message for behavior pattern discovery.
5. Store only minimal safety handling metadata if needed.

The system must not diagnose, provide medical advice, discuss self-harm methods, or imply it can provide crisis intervention.

## Intervention Method Library

MVP method library should include these low-complexity methods:

1. `15 分钟启动法`
2. `认知记录表`
3. `注意力回收训练`
4. `人生意义探索写作`

`18 天成长计划` is P1. Do not implement it in MVP.

## Frontend Scope

MVP frontend should be a practical workbench, not a marketing site.

MVP views / panels:

1. Chat page.
2. Memory panel.
3. Pattern panel.
4. Action task panel.

P1 views:

1. Full summary page.
2. 18-day plan page.
3. Growth trend visualization.
4. Multi-session management.

Use restrained, task-focused UI. Avoid decorative landing-page design.

## Engineering Baseline

Before starting implementation work:

1. Read `PRD V1.md`, `TECH DESIGN V1.md`, and this file.
2. Confirm local services are available when the task needs persistence or retrieval:
   `docker compose up -d`.
3. Use `scripts/init_project.ps1` only to create the initial skeleton; do not treat it as business implementation.
4. Use `scripts/init_db.py` to create MongoDB indexes, Milvus collection, and MVP method seed data.

Backend conventions:

1. Python version: `>=3.11,<3.13`.
2. Dependency source: `pyproject.toml`.
3. Format/lint: `ruff format .` and `ruff check .`.
4. Test framework: `pytest` and `pytest-asyncio`.
5. Backend entrypoint: `app.main:app`.

Frontend conventions:

1. Use React + Vite + TypeScript.
2. Keep the first screen a practical workbench, not a marketing page.
3. API client code belongs in `frontend/src/services`.
4. Shared UI components belong in `frontend/src/components`.

## Testing And Acceptance

Before claiming the MVP works, verify:

1. At least 3 demo inputs run through conversation, memory extraction, memory retrieval, pattern discovery, method routing, task generation, and feedback recording.
2. At least 1 high-risk input enters `SafetyResponseNode` and stops normal coaching.
3. At least 1 candidate pattern cites 3 or more `evidence_memory_ids`.
4. Memory delete / edit stops that memory from being used in retrieval, pattern discovery, and profile updates.
5. Top 3 memory retrieval results contain at least 1 relevant historical memory in the main demo scenario.

Prompt test set target:

1. 30 manually labeled inputs.
2. Include anxiety, procrastination, high sensitivity, rumination, confusion, ordinary small talk, and high-risk expression.
3. Core field extraction pass rate for `emotion`, `trigger`, and `behavior` should be at least 80%.
4. Single-question follow-up pass rate should be at least 90%.

## Implementation Style

Prefer simple, explicit code over generic abstractions.

Do not add flexibility unless it directly supports the documented MVP or the `MemoryService` provider boundary.

Keep changes surgical:

1. Do not refactor unrelated modules.
2. Do not add P1 features while implementing P0.
3. Do not introduce extra databases or frameworks.
4. Do not bypass MongoDB as the memory source of truth.
5. Do not let third-party memory SDKs leak into agent nodes.

If a requirement conflicts with the PRD or tech design, stop and surface the tradeoff before implementing.
