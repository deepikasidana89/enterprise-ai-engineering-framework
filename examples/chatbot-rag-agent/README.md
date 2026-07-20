# Customer Support Chatbot with RAG and Agents

## Overview

A production AI system for handling customer support tickets with intelligent routing, context retrieval, and human escalation.

## Architecture at a Glance

```
User Query
    ↓
[Intent Classification]
    ↓
[RAG Retrieval from Knowledge Base]
    ↓
[Agent Decision Making]
    ├─→ [Answer from KB] → Confidence Check
    ├─→ [Need Tool Use] → Execute Tools
    └─→ [Escalate to Human]
    ↓
[Response + Human Handoff if needed]
```

## Key Decisions

- **RAG vs Fine-tuning:** RAG chosen for knowledge freshness and cost
- **Autonomous vs Human-in-Loop:** Hybrid approach with confidence thresholds
- **Routing Strategy:** Intent-based routing to specialized agents
- **Memory Management:** Session-level context with fallback to KB

## Topics Covered

See full details in:
- [Architecture Decision](architecture.md)
- [Implementation Code](code/)
- [Deployment Strategy](deployment.md)
- [Lessons Learned](lessons-learned.md)

---

**Status:** Ready for reference  
**Last Updated:** 2024-07-14
