# RetailOps AI: Enterprise Feedback & Action Plan System

## 1. Background

RetailOps AI is a production-ready B2B platform designed for large-scale retail operations.

- **Customer**: Regional Managers and Operations Teams.
- **Problem**: Manual processing of customer feedback, identifying category-specific issues (e.g., sofas, beds), and creating actionable improvement plans takes 20-40 minutes per entry. High volumes lead to backlogs and missed SLAs.
- **Solution**: A web application that automates data entry, performs strict integrity checks, and uses LLMs to generate "Action Plans" to improve store performance and compliance.

## 2. Key Features

- **Intelligent Data Entry**: Web form for customer, store, and feedback data.
- **Real-time Validation**: Strict validation for Store IDs, Customer IDs, and category codes.
- **Advanced Duplicate Detection**: Multi-layered logic to prevent redundant processing of the same complaint across different channels (e.g., Taobao, JD.com, SMS).
- **AI-Powered Action Plans**: Automatically generates Problem Lists, SMART Goals, and Manager Interventions using LLM (Claude/OpenAI).
- **High Performance**: Multi-level caching (Redis) and asynchronous task queues (SQS/Celery) to support 5,000+ QPS and reduce response times from 2s to 800ms.
- **Compliance & Reporting**: One-click export for regional performance audits.

## 3. Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django 5.0, Django REST Framework (DRF) |
| Database | PostgreSQL (AWS RDS) |
| Caching | Redis (Local Memory Cache) |
| Task Queue | AWS SQS / Celery + Redis |
| AI Engine | Anthropic Claude / OpenAI API |
| Infrastructure | Docker, Terraform, AWS (EC2, S3, Lambda) |
| Testing | Pytest, TDD Methodology |

## 4. Duplicate Detection & Integrity Logic

### Customer/Store Integrity

| Scenario | Condition | Result |
|----------|-----------|--------|
| Exact Match | CID same + Name/Phone same | Reuse existing customer record |
| ID Conflict | CID same + Name/Phone different | ⚠️ WARNING: Acknowledge to continue |
| Store Conflict | Store ID same + Store Name different | ❌ ERROR: Blocked, must correct name |

### Feedback Duplicates

| Scenario | Condition | Result |
|----------|-----------|--------|
| Exact Duplicate | Same Customer + Same Category + Same Day | ❌ ERROR: Blocked (Prevent double-processing) |
| Possible Duplicate | Same Customer + Same Category + Different Day | ⚠️ WARNING: Flag as follow-up |

## 5. Quick Start

### Prerequisites

- Docker & Docker Compose
- AWS CLI (for SQS/S3 integration)

### Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd retailops-ai

# 2. Configure Environment
cp backend/.env.example backend/.env
# Add your ANTHROPIC_API_KEY or OPENAI_API_KEY

# 3. Spin up Infrastructure (DB, Redis, Django, Worker)
docker-compose up -d

# 4. Initialize Database & Admin
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

## 6. Action Plan Generation (LLM Output)

The system analyzes raw feedback and clinical notes to generate a structured report with these mandatory headers:

1. Problem List / Root Cause Analysis
2. Goals (SMART)
3. Manager Interventions / Operational Plan
4. Monitoring Plan & SLA Tracking
