# Memory-Driven Growth Agent

Memory-Driven Growth Agent is a portfolio MVP for a memory-driven growth coaching agent.

It is not a psychotherapy replacement, medical diagnosis tool, crisis intervention service, or generic emotional chatbot. The MVP focuses on this closed loop:

```text
structured memory collection
-> long-term memory retrieval
-> repeated behavior pattern discovery
-> intervention method routing
-> lightweight action task generation
-> task feedback and memory update
```

## Tech Stack

Backend:

- FastAPI
- Pydantic v2
- LangGraph
- MongoDB
- Milvus / vector store

Frontend:

- React
- Vite
- TypeScript

## Quick Start

1. Copy `.env.example` to `.env` and fill in the LLM provider settings.
2. Start local infrastructure:

```powershell
docker compose up -d
```

3. Create the project skeleton if it has not been generated yet:

```powershell
.\scripts\init_project.ps1
```

4. Create MongoDB indexes, Milvus collection, and seed the MVP method library:

```powershell
python .\scripts\init_db.py
```

5. Start the backend:

```powershell
uvicorn app.main:app --reload
```

6. Start the frontend after installing dependencies in `frontend/`:

```powershell
cd frontend
npm install
npm run dev
```

## Environment Variables

See `.env.example` for the full local development template.

Important variables:

- `MONGODB_URI`
- `MONGODB_DATABASE`
- `VECTOR_BACKEND`
- `MILVUS_HOST`
- `MILVUS_PORT`
- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_MODEL`

## Documentation

- `PRD V1.md`: product scope and user journey
- `TECH DESIGN V1.md`: architecture, data model, workflow, testing, and engineering baseline
- `AGENTS.md`: project-specific implementation rules for coding agents

## Formal Chat API

Use `POST /api/chat` for the complete MVP graph:

```json
{
  "user_id": "demo-user",
  "message": "I wanted to study, but I watched short videos for two hours instead."
}
```

High-risk input is routed first through `RiskDetectionNode`. If the level is
`high`, the graph returns a safety response and stops before memory retrieval,
memory update, pattern discovery, intervention routing, or task generation.

`POST /api/chat/simple` is retained only as a development smoke-test endpoint.

## Memory Governance

Memory mutation goes through `MemoryService`:

- `PATCH /api/memories/{memory_id}` updates structured memory fields and refreshes the vector index through the provider.
- `DELETE /api/memories/{memory_id}` soft-deletes the MongoDB memory and removes the related vector embedding.

MongoDB remains the source of truth. Milvus is only the semantic retrieval index.

## Demo Data

- `data/demo/phase6_demo_inputs.json`: demo inputs for learning procrastination, high sensitivity, long-term confusion, and high-risk safety flow.
- `data/prompt_tests/mvp_prompt_test_set.jsonl`: 30 labeled prompt test cases covering anxiety, procrastination, high sensitivity, rumination, confusion, small talk, and high-risk input.

## Safety Boundary

This product supports self-growth reflection and daily planning. It is not a
medical diagnosis tool, psychotherapy service, crisis intervention service, or
emergency support tool. If a user may be in immediate danger, the system should
encourage contacting local emergency services, a trusted nearby person, or
qualified crisis support.

## MVP Acceptance

Before claiming the MVP works, verify the acceptance criteria in `AGENTS.md`, especially:

- 3 demo inputs run through the full growth loop.
- 1 high-risk input enters `SafetyResponseNode` and stops normal coaching.
- 1 candidate pattern cites at least 3 `evidence_memory_ids`.
- Memory edit/delete prevents that memory from being used in retrieval, pattern discovery, and profile updates.

Useful local checks:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
cd frontend
npm run build
```
