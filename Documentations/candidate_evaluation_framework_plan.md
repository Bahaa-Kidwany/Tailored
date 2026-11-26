# Technical Plan: 9-Pillar Candidate-to-Job Fit Evaluation Framework

This document specifies the technical design, mathematical scoring algorithms, and multi-dimensional evaluation metrics for **Story 2: Candidate Evaluation & Fit Scoring Engine**.

---

## 1. Why the Naive 4-Point System Fails

In traditional simple evaluators, candidate fit is calculated using 4 shallow checks:
1. Flat keyword overlap (`set(candidate_skills) ∩ set(job_skills)`)
2. Binary experience check (`years >= min_years`)
3. String match on location (`"Remote" == "Remote"`)
4. String match on seniority (`"Senior" in title`)

### The Fatal Flaws of That Approach:
* **The "Flat Skill" Fallacy:** Missing `Python` for a Senior Python Developer is fatal, while missing `DynamoDB` is a minor nice-to-have. Treating all skills as equal creates misleading scores (e.g., someone with Git, Docker, and Agile gets 60% match without knowing Python!).
* **Zero Project/Impact Evidence:** Recruiter screening looks for *proof of work*. If the job requires "architecting event-driven microservices", does the candidate have a project or achievement proving they built one?
* **Ignored Domain Context:** A Python developer from a digital marketing agency is fundamentally different from a Python developer who built payment gateways at a Fintech startup.
* **No Multi-Persona Awareness:** Real candidates have distinct career tracks (e.g. *Data Scientist* vs *Data Analyst*). Evaluating against a single static profile distorts the match.

---

## 2. The 9-Pillar Candidate Evaluation Matrix

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           GATE: DEALBREAKER FILTER                               │
│  • Unpaid / Volunteer role?                                                      │
│  • Excluded negative keywords matched?                                           │
│  • Hard visa / geographic restriction violated?                                  │
│  (If Gate FAILS ──► is_passed = False, score = 0.0, Skip scoring)                │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ Passed Gate
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   MULTI-DIMENSIONAL FIT SCORING ENGINE (0-100%)                  │
│                                                                                  │
│  1. Core Stack Competency (Mandatory vs Nice-to-Have)        [Weight: 30%]       │
│  2. Project & Achievement Alignment (Proof of Execution)     [Weight: 20%]       │
│  3. Seniority & Autonomy Scope (IC vs Lead vs Architect)     [Weight: 10%]       │
│  4. Experience Depth & Trajectory (Years & Career Growth)    [Weight: 10%]       │
│  5. Domain & Industry Relevance (Fintech, SaaS, E-com)       [Weight: 10%]       │
│  6. Career Persona Track Specificity                         [Weight: 5%]        │
│  7. Education & Accreditations (Degree & Certifications)     [Weight: 5%]        │
│  8. Work Mode & Geographic Practicality                      [Weight: 5%]        │
│  9. Language & Communication Compatibility                    [Weight: 5%]        │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
                         Total Fit Score (0.0 to 100.0)
                        + Actionable Gap Analysis Report
```

---

## 3. Mathematical Metric Formulations

### Metric 1: Core Stack Competency (Weight: 30%)
Splits skills into **Mandatory** and **Nice-to-Have**:
$$\text{Score}_{\text{skills}} = 0.80 \times \left( \frac{|\text{Mandatory} \cap \text{CandidateSkills}|}{|\text{Mandatory}|} \right) + 0.20 \times \left( \frac{|\text{NiceToHave} \cap \text{CandidateSkills}|}{|\text{NiceToHave}|} \right)$$
* **Non-Linear Penalty:** If the candidate matches less than 50% of the mandatory core stack, a $0.5\times$ penalty multiplier is applied.

### Metric 2: Project & Achievement Alignment (Weight: 20%)
Evaluates whether the candidate has built systems solving the job's `core_responsibilities`:
* Compares candidate's `featured_projects` and `experience_highlights.achievements` against job responsibilities.
* Computes token/semantic overlap and keyword co-occurrence (e.g. *API Gateway*, *Microservices*, *ETL*, *XGBoost*).

### Metric 3: Seniority & Autonomy Scope (Weight: 10%)
Assesses leadership and engineering maturity:
* **Senior/Lead Roles:** Checks achievements for high-leverage actions: *"mentored"*, *"architected"*, *"designed"*, *"code review"*, *"scaled"*.
* **Mid-Level Roles:** Checks for independent implementation and delivery.
* **Junior Roles:** Focuses on foundational technical execution.

### Metric 4: Experience Gap & Trajectory (Weight: 10%)
$$\text{Ratio} = \frac{\text{CandidateYears}}{\text{JobMinYears}}$$
* If $\text{Ratio} \ge 1.0 \implies 1.0$ (Full score).
* If $0.7 \le \text{Ratio} < 1.0 \implies 0.8$ (Within acceptable buffer).
* If $\text{Ratio} < 0.7 \implies \text{Ratio} \times 0.7$ (Steep penalty for under-qualification).

### Metric 5: Domain & Industry Relevance (Weight: 10%)
* Extracts industry from job company/description (e.g. *Fintech*, *Healthtech*, *E-commerce*, *Cloud Infrastructure*).
* Compares against candidate's previous employers and project summaries.

### Metric 6: Career Persona Track Specificity (Weight: 5%)
* Evaluates how closely the job title aligns with the active `CareerPersona.target_title` and `alternative_titles`.
* Multi-Persona Matching: Scores the job across **all** candidate personas to recommend: *"Best match for your Backend Track (91%) vs Data Analyst (45%)"*.

### Metric 7: Education & Accreditations (Weight: 5%)
* Checks degree alignment (e.g. B.S. in CS / Engineering).
* Awards bonus points for specialized industry certifications (e.g. AWS Solutions Architect, DeepLearning.AI, PMP).

### Metric 8: Work Mode & Geographic Compatibility (Weight: 5%)
* Evaluates `Remote` vs `Hybrid` vs `On-site` practicality against user's target cities and relocation willingness.

### Metric 9: Language & Communication Capabilities (Weight: 5%)
* Verifies English proficiency requirements (e.g. Upper-Intermediate / Fluent for multinational roles).
* Verifies Arabic bilingual requirements for local/Gulf roles.

---

## 4. Evaluation Output Contract (`JobEvaluationReport`)

```json
{
  "job_id": "wuzzuf_rcqxngwvzmck",
  "evaluated_persona_id": "backend_engineer_track",
  "total_fit_score": 87.5,
  "is_passed": true,
  "passing_threshold": 65.0,
  "pillar_breakdown": [
    {"pillar": "Core Stack Competency", "score": 90.0, "weight": 0.30, "details": "Matched 11/13 mandatory skills: Python, FastAPI, Docker, AWS, PostgreSQL."},
    {"pillar": "Project & Achievement Alignment", "score": 85.0, "weight": 0.20, "details": "Demonstrated proof in projects: REST APIs, microservices, dynamic routing."},
    {"pillar": "Seniority & Autonomy Scope", "score": 90.0, "weight": 0.10, "details": "Candidate has 3+ years mentoring junior engineers and leading code reviews."},
    {"pillar": "Experience Trajectory", "score": 100.0, "weight": 0.10, "details": "Candidate has 5 years experience (exceeds 5-year requirement)."},
    {"pillar": "Domain & Industry Relevance", "score": 80.0, "weight": 0.10, "details": "Shared tech and SaaS project background."},
    {"pillar": "Career Persona Fit", "score": 95.0, "weight": 0.05, "details": "Exact match for Backend Engineer persona."},
    {"pillar": "Education & Certifications", "score": 85.0, "weight": 0.05, "details": "B.S. in Computer Science from Cairo University."},
    {"pillar": "Work Mode & Geography", "score": 80.0, "weight": 0.05, "details": "Located in Cairo, willing to work Hybrid in Smart Village."},
    {"pillar": "Language & Communication", "score": 95.0, "weight": 0.05, "details": "Professional English + Native Arabic."}
  ],
  "skill_gap_analysis": {
    "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
    "missing_mandatory": ["React/Vue"],
    "missing_nice_to_have": ["Kubernetes", "AWS CDK"]
  },
  "tailoring_directives": [
    "Emphasize FastAPI and PostgreSQL query optimization in Summary.",
    "Highlight microservices architecture and AWS workloads in Swvl experience bullets.",
    "Downplay frontend gap by framing experience as backend-first with collaborative REST API integration."
  ]
}
```

---

## 5. Next Implementation Steps

1. **Implement 9 Evaluation Metric Classes (`backend/app/evaluator/metrics/`):**
   - Implement each isolated metric class inheriting from `BaseEvaluationMetric`.
2. **Implement Evaluator Engine (`backend/app/evaluator/engine.py`):**
   - Runs gate checks $\rightarrow$ calculates weighted scores $\rightarrow$ outputs `JobEvaluationReport`.
3. **Multi-Persona Auto-Ranker:**
   - Evaluates a job against all personas in `user_profile.json` and reports the winning track.
4. **Test Harness (`backend/tests/test_candidate_evaluation.py`):**
   - Evaluates the user profile against [extracted_job_insights.json](file:///d:/Tailored/backend/tests/fixtures/extracted_job_insights.json).
