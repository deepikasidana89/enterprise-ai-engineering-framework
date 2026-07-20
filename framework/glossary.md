# Glossary of Terms

## Key Framework Concepts

### A/B Testing
Running two versions of a model in production with a portion of traffic to each, measuring outcomes to determine which performs better.

### Adversarial Attack
Attempts to fool a machine learning model by providing carefully crafted inputs that cause incorrect predictions. Testing for resilience to these attacks is part of comprehensive model testing.

### Alerting
Automated notifications triggered when monitored metrics breach defined thresholds or anomalies are detected.

### Assessment Pillar
One of the 8 key dimensions evaluated in EARF:
1. Business Strategy & Alignment
2. Data Governance & Quality
3. Data Architecture & Infrastructure
4. Model Development & Experimentation
5. Model Deployment & Operations
6. Monitoring, Observability & Maintenance
7. Security, Compliance & Governance
8. Team, Skills & Organization

### Bias
Systematic errors in model predictions related to protected characteristics (gender, race, age, etc.). Models can amplify bias present in training data.

### Business Alignment
The degree to which AI initiatives support documented business strategy and objectives with clear, measurable outcomes.

### Canary Deployment
A deployment strategy where new models are released to a small subset of traffic first, gradually increasing traffic while monitoring for issues.

### CI/CD Pipeline
Continuous Integration/Continuous Deployment - automated systems for building, testing, and deploying code changes frequently and reliably.

### Compliance
Adherence to regulatory requirements and standards (GDPR, HIPAA, SOX, industry standards, etc.).

### Data Drift
Changes in the statistical properties of input data over time, which can cause model performance to degrade.

### Data Governance
Systems and policies for managing data assets, including ownership, quality, privacy, security, and usage.

### Data Lineage
Tracking the origin and transformations of data as it flows through systems, enabling root cause analysis and compliance auditing.

### Data Quality
The degree to which data is accurate, complete, consistent, and trustworthy for its intended use.

### Deployment
The process of moving a trained model from development/staging to production where it makes real predictions.

### Drift Detection
Automated monitoring and alerting for changes in model performance, data distribution, or prediction patterns.

### Fairness
Ensuring models make equitable predictions across different demographic groups and use cases.

### Feature Engineering
The process of creating input variables (features) for machine learning models from raw data.

### Feature Store
A centralized system that manages feature creation, storage, and access for ML models.

### Governance
Systems and processes for managing risk, compliance, and decision-making authority for AI systems.

### Infrastructure as Code (IaC)
Defining and provisioning infrastructure (servers, networks, storage) through code rather than manual configuration.

### Maturity Level
One of five progression levels in EARF (Initial, Managed, Defined, Quantitatively Managed, Optimized).

### Model Drift
Changes in model performance over time due to data drift, concept drift, or other factors.

### Model Registry
A centralized system for storing, versioning, and tracking deployed ML models.

### Model Review
A formal process where models are evaluated for quality, fairness, compliance, and business impact before deployment.

### MLOps
Machine Learning Operations - engineering practices for productionizing, operating, and maintaining ML systems.

### Observability
The ability to understand system state and behavior through metrics, logs, traces, and other signals.

### Operational Excellence
A state where systems run reliably, issues are quickly detected and resolved, and continuous improvement is practiced.

### Operations (Ops)
The team and processes responsible for running and maintaining systems in production.

### Production-Ready
A system that meets minimum requirements for deployment to production with acceptable risk levels (EARF 2.6+ score typically).

### Readiness Score
A numerical rating (1-5) representing maturity level in a specific assessment area, pillar, or organization-wide.

### Reproducibility
The ability to recreate the exact same model results given the same data and code/configuration.

### Rollback
The process of reverting to a previous model version when a new deployment causes issues.

### Root Cause Analysis
Investigating why a failure occurred to identify the underlying cause rather than just symptoms.

### SLA (Service Level Agreement)
A commitment to specific performance levels (uptime, latency, accuracy) for a system.

### SLI (Service Level Indicator)
A measured metric that indicates whether an SLA is being met.

### SLO (Service Level Objective)
A target level for an SLI (e.g., "99.9% uptime" is an SLO).

### Scoring Methodology
EARF's approach to evaluating maturity:
- Questions scored 1-5
- Categories aggregate question scores
- Pillars aggregate category scores
- Overall score aggregates pillar scores

### Security
Systems and practices to protect AI systems from unauthorized access, attacks, and misuse.

### SRE (Site Reliability Engineering)
Engineering practices and culture focused on making systems reliable, scalable, and maintainable.

### Staging
A pre-production environment that mimics production for testing before release.

### Transparency
The degree to which a model's decisions can be understood and explained.

### Version Control
Systems (like Git) for tracking changes to code, models, and data configurations.

### Vulnerability
A weakness or defect that could be exploited to compromise system security or performance.

---

## Role Definitions

### Assessment Lead
The person or team orchestrating the EARF assessment, responsible for timeline, coordination, and result compilation.

### Data Engineer
The team member responsible for building and maintaining data pipelines, data warehouses, and feature engineering infrastructure.

### Data Governance Lead
The person responsible for data policies, standards, quality assurance, and compliance with data regulations.

### Data Science Lead
The team member responsible for model development, experimentation, and model performance optimization.

### Executive Sponsor
Senior leadership person providing air cover, resources, and accountability for AI initiatives.

### Head of Data/AI
The organizational leader responsible for all data and AI initiatives.

### Infrastructure/Platform Lead
The person responsible for ML infrastructure, platforms, deployment systems, and technical architecture.

### Operations Lead / SRE
The team member responsible for production system health, monitoring, incident response, and reliability.

### Security/Compliance Lead
The person responsible for security practices, compliance with regulations, and governance policies.

---

## EARF-Specific Terms

### Assessment Cycle
One complete assessment of an organization's AI readiness, typically taking 4-6 weeks for initial assessment.

### Category (Assessment)
A group of related assessment questions within a pillar.

### Conditional Production Approval
Approval to deploy to production with specific conditions that must be met.

### Framework
The complete EARF system including principles, maturity model, pillars, scoring methodology, and assessment process.

### Gap Analysis
Identifying the difference between current state and desired state.

### Improvement Initiative
A specific project designed to improve readiness in one or more pillars.

### Improvement Roadmap
A prioritized plan of improvement initiatives showing sequencing and expected impact.

### Overall Readiness Score
The aggregated score across all 8 pillars (1-5 scale).

### Pillar Score
The maturity level for one specific pillar.

### Production Readiness Assessment
The determination of whether a system meets minimum requirements for production deployment.

### Question Score
The 1-5 maturity rating for an individual assessment question.

### Readiness Level
The named level corresponding to a score range (Initial, Managed, Defined, Quantitatively Managed, Optimized).

---

## Abbreviations and Acronyms

- **AI:** Artificial Intelligence
- **CI/CD:** Continuous Integration/Continuous Deployment
- **EARF:** Enterprise AI Readiness Framework
- **GDPR:** General Data Protection Regulation
- **HIPAA:** Health Insurance Portability and Accountability Act
- **IaC:** Infrastructure as Code
- **K8s:** Kubernetes
- **ML:** Machine Learning
- **MLOps:** Machine Learning Operations
- **OKR:** Objectives and Key Results
- **PII:** Personally Identifiable Information
- **ROI:** Return on Investment
- **SLA:** Service Level Agreement
- **SLI:** Service Level Indicator
- **SLO:** Service Level Objective
- **SRE:** Site Reliability Engineering

---

For more information, see:
- [Core Principles](core-principles.md)
- [Assessment Pillars](pillars.md)
- [Scoring Methodology](scoring.md)
- [Example Assessment](../examples/example-assessment-midcorp.md)
