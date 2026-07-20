# Scoring Methodology

## Overview

The EARF uses a structured scoring approach to quantify organizational AI readiness. Scores are assigned at multiple levels: assessment questions, pillar categories, pillars, and an overall maturity score.

---

## Score Hierarchy

```
Overall Readiness Score (1-5)
    ↓
Pillar Scores (8 pillars, each 1-5)
    ↓
Category Scores (within each pillar, 1-5)
    ↓
Question Scores (1-5 for each assessment question)
```

---

## Question-Level Scoring

Each assessment question is scored on a scale of 1-5 based on implementation maturity:

### Scale Definition

| Score | Level | Definition | Evidence |
|-------|-------|-----------|----------|
| **1** | Initial | Not addressed or minimal effort | No documentation, manual processes only |
| **2** | Managed | Basic processes in place | Documented procedures, partially implemented |
| **3** | Defined | Standardized and documented | Automated workflows, consistent application |
| **4** | Quantitatively Managed | Measured and optimized | Metrics tracked, data-driven improvements |
| **5** | Optimized | Continuous improvement | Proactive optimization, innovation culture |

### Scoring Criteria

For each question, evaluators assess:
- **Implementation:** Is this practice implemented?
- **Coverage:** How broadly is it applied across the organization?
- **Automation:** How much is automated vs. manual?
- **Monitoring:** Is there measurement and feedback?
- **Maturity:** Is there continuous improvement?

---

## Category-Level Scoring

Categories group related assessment areas within a pillar.

**Category Score = Average of related question scores**

Example (Data Quality category):
- Q1: Data quality standards defined - Score: 3
- Q2: Automated quality monitoring - Score: 2
- Q3: Root cause analysis process - Score: 3
- **Category Score = (3 + 2 + 3) / 3 = 2.67** → rounded to **3**

---

## Pillar-Level Scoring

Each pillar contains multiple categories.

**Pillar Score = Weighted average of category scores**

### Weighting Strategy

Within each pillar, categories may have different weights based on importance:
- **Critical (40%):** Essential for production readiness
- **Important (35%):** Strongly recommended
- **Valuable (25%):** Nice to have

### Calculation Example

Business Strategy & Alignment pillar:
- Strategic Vision (40%) - Score: 3
- Business Case (40%) - Score: 2
- Use Case Prioritization (20%) - Score: 2

**Pillar Score = (3 × 0.4) + (2 × 0.4) + (2 × 0.2) = 1.2 + 0.8 + 0.4 = 2.4** → rounded to **2**

---

## Overall Readiness Score

**Overall Score = Weighted average of all 8 pillar scores**

### Pillar Weights

Different weighting strategies can be applied based on organizational context:

#### Default (Balanced) Weighting
Each pillar weighted equally at 12.5%:
1. Business Strategy & Alignment - 12.5%
2. Data Governance & Quality - 12.5%
3. Data Architecture & Infrastructure - 12.5%
4. Model Development & Experimentation - 12.5%
5. Model Deployment & Operations - 12.5%
6. Monitoring, Observability & Maintenance - 12.5%
7. Security, Compliance & Governance - 12.5%
8. Team, Skills & Organization - 12.5%

#### Foundation-First (Data-Centric) Weighting
Emphasizes data as foundation:
- Pillars 2 & 3 (Data): 20% each
- Pillars 1, 4, 5, 6, 8: 12% each
- Pillar 7 (Security): 4%

#### Production-First (Operations-Centric) Weighting
Emphasizes operational excellence:
- Pillars 5 & 6 (Deployment & Operations): 18% each
- Pillars 2, 3, 4, 7, 8: 11% each
- Pillar 1: 5%

---

## Scoring Interpretation

### Overall Readiness Levels

| Score | Level | Readiness | Recommendation |
|-------|-------|-----------|-----------------|
| **1.0 - 1.5** | Initial | Not ready for production | Focus on foundational practices; don't deploy |
| **1.6 - 2.5** | Managed | Minimal readiness | Limited production use; controlled scope |
| **2.6 - 3.5** | Defined | Ready for production | Deploy with standard practices; active monitoring |
| **3.6 - 4.5** | Quantitatively Managed | Highly ready | Deploy with high confidence; continuous optimization |
| **4.6 - 5.0** | Optimized | Exceptional readiness | Industry best practices; innovation ready |

### Production Readiness Thresholds

**Minimum production readiness:** 2.5 overall score

**Pillar-specific minimums (for critical pillars):**
- Data Quality (Pillar 2): ≥ 2.5
- Monitoring & Observability (Pillar 6): ≥ 2.5
- Security & Governance (Pillar 7): ≥ 2.0

---

## Scoring Best Practices

### 1. Multi-Stakeholder Assessment
- Involve representatives from each function
- Use independent assessments and reconcile differences
- Document disagreements and their reasons

### 2. Evidence-Based Scoring
- Require documentary evidence (policies, runbooks, dashboards)
- Score based on actual implementation, not planned state
- Request demonstrations of processes

### 3. Contextual Adjustments
- Consider organization size and maturity
- Adjust expectations based on industry standards
- Account for risk profile and regulatory environment

### 4. Trend Analysis
- Track scores over time
- Celebrate improvements
- Identify stalled areas

### 5. Avoid Common Pitfalls
- ❌ Don't score aspirational state (score actual state)
- ❌ Don't apply same standards to all organizations
- ❌ Don't score without evidence
- ❌ Don't use scores punitively

---

## Reassessment Cycle

**Recommended Schedule:**
- **Initial Assessment:** Baseline measurement (1-2 months)
- **Quarterly Lightweight:** 2-week check-in on key areas
- **Annual Full Assessment:** Comprehensive reassessment (6-8 weeks)

---

## Score Reporting

### Dashboard Components

1. **Overall Readiness Score** - Primary metric
2. **Pillar Breakdown** - 8 pillar scores with trends
3. **Strengths & Weaknesses** - Top 3 in each category
4. **Gap Analysis** - Comparison to target state
5. **Improvement Roadmap** - Prioritized actions
6. **Benchmark Comparison** - Industry and peer comparison (optional)

### Report Structure

1. Executive Summary (1 page)
   - Overall score and readiness level
   - Top 3 strengths and improvement areas
   - Recommended next steps

2. Detailed Findings (10-15 pages)
   - Pillar-by-pillar analysis
   - Category-level scores with commentary
   - Evidence and supporting documentation

3. Improvement Roadmap (5-10 pages)
   - Prioritized improvement initiatives
   - Resource requirements
   - Timeline and milestones
   - Success metrics

---

## Adjustment for Context

### Organization Size
- **Startup (<50 people):** May score lower on governance but same on technical execution
- **Mid-market (50-500):** Balanced scoring across all pillars
- **Enterprise (>500):** Higher governance and compliance expectations

### Industry/Regulation
- **Highly regulated (Finance, Healthcare):** Higher security/compliance expectations
- **Fast-moving (Tech, Consumer):** Higher experimentation expectations
- **Critical infrastructure:** Higher reliability expectations

### AI Use Case Type
- **Real-time (Recommendations):** Higher operations/monitoring expectations
- **Batch (Analytics):** Higher data quality expectations
- **High-risk (Autonomous systems):** Higher governance expectations
