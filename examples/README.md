# Examples Directory

This directory contains detailed case studies showing real-world architecture decisions and trade-offs for Enterprise AI systems.

Each example includes:

- **README.md** – Overview and context
- **architecture.md** – Architecture decisions and rationale
- **code/** – Sample implementation patterns
- **deployment.md** – How to roll out to production
- **lessons-learned.md** – What worked, what didn't, and why

## Case Studies

### [Customer Support Chatbot](chatbot-rag-agent/)

**Problem:** Support team processing 1000+ tickets/day with increasing volume  
**Solution:** AI-assisted chatbot with RAG + agents + human handoff  
**Challenges:** Ensuring accuracy, handling escalations, controlling costs

**Topics covered:**
- RAG implementation for knowledge base
- Agent decision-making and tool use
- Human-in-the-loop workflows
- Cost management and rate limiting
- Monitoring and quality metrics

### [Code Generation Tool](code-generation/)

**Problem:** Accelerating developer productivity for boilerplate code  
**Solution:** Deterministic templates + AI completion + human review  
**Challenges:** Quality consistency, latency, cost per suggestion

**Topics covered:**
- When NOT to use fully autonomous AI
- Hybrid deterministic + AI workflows
- Evaluation metrics for code quality
- Performance optimization
- A/B testing of model versions

### [Document Analysis System](document-analysis/)

**Problem:** Extracting structured data from unstructured documents at scale  
**Solution:** RAG for context + structured output + validation workflow  
**Challenges:** Consistency, accuracy, handling edge cases

**Topics covered:**
- Document chunking strategies
- Structured output and JSON schemas
- Validation and error handling
- Batch processing vs real-time
- Scaling to large document volumes

### [Content Moderation Pipeline](content-moderation/)

**Problem:** Reviewing user-generated content for policy violations  
**Solution:** Classification model + rule engine + human escalation  
**Challenges:** False positives, cultural sensitivity, cost at scale

**Topics covered:**
- When to use fine-tuned models vs APIs
- Ensemble approaches for safety
- False positive reduction
- SLA management for human review
- Fairness and bias monitoring

---

## How to Use These Examples

**If you're designing a similar system:**
- Read architecture.md for decision rationale
- Review deployment.md for operational patterns
- Study lessons-learned.md for gotchas

**If you're learning the framework:**
- Read one full example to see decisions in context
- Compare trade-offs across examples
- Map your system to similar patterns

**If you're implementing:**
- Use code/ as reference implementations
- Adapt deployment patterns to your infrastructure
- Use evaluation metrics as baseline

---

## Common Patterns Across Examples

| Pattern | Where Used | Rationale |
|---------|-----------|-----------|
| RAG for knowledge | Chatbot, Documents | Grounding to reduce hallucination |
| Human escalation | Chatbot, Moderation | Safety and quality gates |
| Structured output | Documents, Code | Programmatic consumption |
| Evaluation metrics | All | Measuring success and drift |
| Cost tracking | All | Managing inference costs |
| A/B testing | Code gen | Comparing model versions |

---

## Contributing New Examples

We welcome contributions of additional case studies. See [CONTRIBUTING.md](../CONTRIBUTING.md) for:

- What makes a good case study
- Template and structure
- How to submit

---

**Note:** These examples reflect patterns as of 2024. As LLM capabilities, costs, and best practices evolve, some details may shift. The underlying decision frameworks remain relevant.
