# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered bookkeeping and tax preparation platform for Canadian accounting firms. Automates document processing, transaction categorization, reconciliation, and tax preparation (BK, T1, T2) using an agent-based workflow where each step is handled by a specialized Claude agent.

## Tech Stack

| Service | Stack | Hosting |
|---------|-------|---------|
| Frontend + dashboard API | Next.js 15, React 19, Prisma, shadcn/ui, TypeScript | AWS App Runner / ECS Fargate |
| Agent processing service | FastAPI, Python 3.12, Celery, Claude API | AWS EC2 / ECS |
| Scheduled jobs | n8n (self-hosted) | AWS EC2 |

Shared data: RDS PostgreSQL 16 + pgvector, ElastiCache Redis 7, S3 — all AWS, `ca-central-1` for PIPEDA compliance.

**Local dev services** (docker-compose.dev.yml): PostgreSQL + pgvector, Redis, MinIO (local S3 at `localhost:9000`).

## Key Directories

```
processing-service/
  app/agents/     # One file per agent, all extend BaseAgent (app/agents/base.py)
  app/api/        # FastAPI routers: engagements, documents, checklist, review, gl, workpapers, plan
  app/tools/      # Deterministic tool functions + TOOL_REGISTRY (__init__.py)
  app/flows/      # bookkeeping.py, t1_personal.py, t2_corporate.py
  app/models/     # LLM wrapper (llm.py), model router (router.py), Pydantic schemas
  app/memory/     # lesson_store.py, client_profile.py
  app/state_machine.py  # processing_run lifecycle + human evaluation recording
  prompts/        # System prompts with YAML frontmatter (version field)
  workers/        # celery_tasks.py
db/migrations/    # 001_initial_schema.sql, 002_state_machine.sql
```

## Build & Validation Commands

IMPORTANT: After every code change, validate the build succeeds.

```bash
# Local dev services
docker compose -f docker-compose.dev.yml up -d

# FastAPI
cd processing-service && uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs

# Celery worker
cd processing-service && celery -A workers.celery_tasks worker --loglevel=info

# Tests
cd processing-service && /opt/homebrew/bin/python3.10 -m pytest tests/test_tools/ -v
cd processing-service && /opt/homebrew/bin/python3.10 -m pytest tests/integration/ -v  # needs real DB
```

Required env vars (see `.env.example`): `DATABASE_URL`, `REDIS_URL`, `CLAUDE_API_KEY`, `MISTRAL_API_KEY`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`.

MinIO local dev: set `AWS_ENDPOINT_URL=http://localhost:9000`, `AWS_ACCESS_KEY_ID=devaccess`, `AWS_SECRET_ACCESS_KEY=devsecret1`.

```bash
# Seed CRA/ITA knowledge base (run once after first DB init)
cd processing-service && PYTHONPATH=. python scripts/seed_knowledge_base.py
```

## Critical Rules

- **Never generate financial numbers with the LLM.** All calculations (GST, CCA, amortization, tax payable) must go through tools in `app/tools/calculations.py`. The agent decides which tool to call; the tool produces the number.
- **Never insert into `gl_entries` directly.** Always use `write_gl_entry()` (`app/tools/gl_writer.py`). `source_chain JSONB NOT NULL` is enforced at the DB level.
- **Never skip a human checkpoint.** Plan steps with `requires_human=true` must pause the pipeline and wait for CPA action via `POST /api/plan/steps/{step_id}/complete`. Do not mark them complete programmatically.
- **Always scope DB queries by `firm_id`.** Every table is multi-tenant; unscoped queries are a data leak.
- **PII must be scrubbed before every LLM call.** `_scrub_pii()` in `app/models/llm.py` handles this. Always go through `call_llm()` — never call the Claude API directly.
- **Agents always restart from scratch.** `BaseAgent.run()` creates a new `processing_run` each time. On failure → status FAILED. Next dispatch always starts fresh — no state is resumed from a previous run.
- **Prompt versions are tracked.** Every prompt file starts with YAML frontmatter (`version: "x.y.z"`). `BaseAgent._load_prompt()` extracts and stores the version in the `processing_run` record.
- **Document extraction uses Claude Sonnet.** `app/tools/ocr.py::extract_document()` uses Claude vision API — not Mistral OCR. Mistral is retained only for embeddings (`get_embedding()` in llm.py).

## Workflow Triggers

- **"add agent `<name>`"** — scaffold `app/agents/<name>_agent.py` extending `BaseAgent` (no `_load_prompt` override needed — base handles YAML frontmatter), create `prompts/<name>_agent.md` with version frontmatter, register in `app/models/router.py`, wire tools in `_register_tools()`.
- **"add tool `<name>`"** — implement async function in the appropriate `app/tools/*.py` file, add to `TOOL_REGISTRY` in `app/tools/__init__.py`.
- **"human checkpoint"** — create review item via `create_review_item()`, pause run via `state_machine.pause_for_human()`, CPA acts via `POST /api/review/{item_id}/decide` which calls `record_human_evaluation()`.

## Additional Documentation

- [`.claude/docs/architectural_patterns.md`](.claude/docs/architectural_patterns.md) — BaseAgent loop, tool registry, source_chain invariant, lesson system, PII scrubbing, frontend↔agent flow, engagement mode state machine, build phases
- [`.claude/docs/agent_specs.md`](.claude/docs/agent_specs.md) — per-agent: model assignment, tools, and key prompt rules for all 12 agents
- [`.claude/docs/data_model.md`](.claude/docs/data_model.md) — full table list, non-obvious constraints, key indexes
