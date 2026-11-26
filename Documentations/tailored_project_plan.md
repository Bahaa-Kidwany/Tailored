# Project Plan: Tailored

## Overview
**Tailored** is a streamlined, purpose-built application focused exclusively on discovering jobs from LinkedIn and Wuzzuf and generating highly tailored CVs and cover letters. By extracting only the essential, high-value AI modules from the previous project, we will eliminate the bloat, dead code, and unnecessary complexity, resulting in a clean and maintainable architecture.

## 1. Core Objectives
1. **Ditch the Bloat:** Start with a clean slate. No legacy files, no unused mobile app code, and no complex automated browser extensions.
2. **Targeted Scraping:** Utilize `stealthyfetcher` specifically designed to scrape LinkedIn and Wuzzuf safely.
3. **Reusability:** Port over only the best AI-driven features from the old codebase: **CV Fit Scoring** and **Cover Letter Generation**.
4. **Modern Stack:** React (Vite) frontend + FastAPI (Python) backend + Dockerized PostgreSQL.

## 2. Architecture & Tech Stack

### Frontend (Web UI)
* **Framework:** React with Vite.
* **Styling:** Vanilla CSS (vibrant, modern, and highly polished as per our design philosophy).
* **Focus:** A completely redesigned, intuitive UI centered around viewing fetched jobs and quickly generating tailored documents.

### Backend (Python)
* **Framework:** FastAPI.
* **Database:** PostgreSQL (running in Docker) using `psycopg` and `SQLModel`/`SQLAlchemy` for clean, typed database interactions instead of raw JSON payloads.
* **Scraping Engine:** Custom integration using `stealthyfetcher` (or equivalent Playwright stealth setups). It will use a **Modular Scraper Plugin System**, meaning there will be a base scraper interface, allowing us to build modules for LinkedIn and Wuzzuf first, and easily drop in new modules for other websites later without touching the core logic.
* **AI Engine:** Reusing the proven Ollama/Vertex AI prompts and logic for CV tailoring.

## 3. Extraction Strategy (What we copy)
We will meticulously extract only the following specific logic from the old project:
* **CV Fit Engine:** The AI prompts and diff-generation logic (`cv_fit_service.py` / `job_extraction_service.py` equivalents) that compare a job description to a base CV.
* **Cover Letter Engine:** The email/cover letter generation prompts (`email_generation_service.py`).
* **Document Parsing:** The logic used to parse `.tex` or `.pdf` base CVs.

*Everything else—including the workflow store, form auto-fillers, crawler queues, and complex schedulers—will be left behind.*

## 4. Phased Implementation Plan

### Phase 1: Foundation & Database
* Initialize the new project directory (`Tailored`).
* Set up a clean Python virtual environment and Vite React app.
* Configure `docker-compose.yml` for a standard PostgreSQL 15 database.
* Design a simple, relational database schema (e.g., `Jobs`, `Profiles`, `GeneratedDocuments`).

### Phase 2: Scraping & Structured Job Evaluation
* **Base Scrapers:** Build lightweight, stealthy scraper plugins (`BaseJobScraper`) for LinkedIn and Wuzzuf to fetch search results and raw job descriptions.
* **Structured Extraction (Fast LLM):** Use a fast, cheap model to parse the unstructured job description into a strict, predefined JSON schema (e.g., extracting required skills, exact years of experience, location type, and core responsibilities).
* **The Evaluator Engine:** Implement a scoring algorithm that compares the extracted JSON metrics against the user's base profile (evaluating skill gap, location match, experience gap, and keyword relevance) to generate a **Fit Score**.
* **Filtering & Storage:** Only save jobs that pass a certain Fit Score threshold to the PostgreSQL database, keeping the database clean and highly relevant.

### Phase 3: AI Document Tailoring & Generation Engine
* **Base Formatter System:** Implement format parsers (`BaseCVFormatter`) for LaTeX and Markdown to cleanly extract and reassemble CV sections without breaking styling syntax.
* **CV Tailoring Engine:** Precision-tailor bullet points and skill sections to match target job requirements extracted in Phase 2, with strict anti-hallucination guardrails.
* **Cover Letter & Company Research Engine:** Generate personalized cover letters using the job description and optional company website background data.
* **Audit Diff & Storage:** Produce side-by-side diffs showing exact changes, and persist tailored documents in the PostgreSQL database (`generated_documents` table).

### Phase 4: UI Design & Integration
* Build the completely new React frontend.
* Implement a premium, dynamic, and highly aesthetic interface.
* Connect the UI to the backend to display jobs, trigger document generation, and download the tailored CVs.

## 5. Next Steps
Once you approve this plan, our immediate next step will be to create the new directory (e.g., `d:\Tailored`), initialize the backend/frontend skeletons, and set up the new Dockerized database.
