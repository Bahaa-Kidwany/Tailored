# User Profile Sequential Funnel — UX Architecture & Data Specification

**Document Version:** 1.0.0  
**Target:** Master UX Specification for Candidate Career Profile Creation  
**Scope:** Information Architecture, Field Specifications, Sequential Page Flow, and CV Translation Mapping  
**Design Constraint:** Pure UX Structure (Fields, Pages, Interactions, and Data Model). Styling, typography, and colors are excluded.

---

## 1. Executive UX Philosophy & CV Translation Model

The **User Profile** is the canonical, verified master record of a candidate’s professional identity. In Tailored, it serves two foundational purposes:
1. **The Ground-Truth for Zero-Hallucination CV Generation:** Every section of the ATS LaTeX/PDF resume is compiled directly from these verified facts. The AI tailoring engine is strictly prohibited from inventing companies, skills, or metrics not present in this master profile.
2. **The Ground-Truth for 5-Dimensional Match Scoring:** The candidate’s active persona, skills, experience, and mobility preferences are continuously matched against live job descriptions.

### Core UX Tenets for the Sequential Funnel:
* **Progressive Disclosure:** Grouped into **6 logical sequential pages** to avoid cognitive overload and prevent form fatigue.
* **The "Resume Drop" Fast-Forward:** On Page 1, users can drop an existing CV (`.pdf`, `.tex`, `.docx`). The background parser auto-populates 75–85% of all subsequent fields, converting the funnel from tedious manual entry into a quick review-and-edit experience.
* **Continuous Draft Persistence:** Every field change auto-saves to local state and the database, allowing users to pause, exit, and resume anytime without data loss.
* **Dynamic Multi-Geography Identity:** Allows candidates to define multiple regional contact numbers (`+20` for Egypt, `+966` for Saudi Arabia, etc.) and target multiple cities simultaneously.

---

## 2. Complete Data Inventory (All Collected Information)

The table below outlines every piece of data collected across the entire user profile, categorized by domain and mapped to its role in the generated CV:

| Domain | Field Name | Data Type | Required? | Final CV Translation Role |
| :--- | :--- | :--- | :---: | :--- |
| **Personal Identity** | `full_name` | String | **Required** | Document Header: Primary Candidate Name |
| | `primary_email` | Email String | **Required** | Document Header: Contact Email |
| | `contact_numbers` | Array of Objects | **Required (min 1)** | Document Header: Dynamic Regional Phone (e.g. `+20` for EG, `+966` for SA) |
| | `links.linkedin` | Clean URL | Optional | Document Header: Clickable LinkedIn Link |
| | `links.github` | Clean URL | Optional | Document Header: Clickable GitHub Link |
| | `links.portfolio` | Clean URL | Optional | Document Header: Clickable Portfolio / Website Link |
| **Mobility & Geography** | `current_residence.city` | String | **Required** | Document Header: Current Location |
| | `current_residence.country` | String | **Required** | Document Header: Current Country |
| | `willing_to_relocate` | Boolean | Optional | Job Radar Filter: Relocation match scoring |
| | `target_locations` | Array of Objects | **Required (min 1)** | Job Radar Feed: Cities & Work Modes (Remote/Hybrid/On-site) |
| **Career Persona** | `target_title` | String | **Required** | Document Subtitle / Target Role Headline |
| | `alternative_titles` | Array of Strings | Optional | Job Radar Query Generator: Expands search scope |
| | `seniority_level` | Enum | **Required** | Match Engine: Experience curve scoring |
| | `years_of_experience` | Integer | **Required** | Match Engine: Continuous proximity calculation |
| | `summary_bio` | Text (Paragraph) | **Required** | CV Section: Professional Summary / Executive Profile |
| **Skills & Tools** | `programming_languages` | Array of Strings | Optional | CV Skills Section: Categorized "Languages" row |
| | `frameworks_and_libraries` | Array of Strings | Optional | CV Skills Section: Categorized "Frameworks" row |
| | `tools_and_platforms` | Array of Strings | Optional | CV Skills Section: Categorized "Cloud & Tools" row |
| | `core_skills` | Array of Strings | **Required (min 3)**| CV Skills Section: Categorized "Core Competencies" row |
| **Work Experience** | `company` | String | **Required** | CV Experience Entry: Employer Name |
| | `role` | String | **Required** | CV Experience Entry: Job Title |
| | `start_date` / `end_date` | Date String / "Present" | **Required** | CV Experience Entry: Right-aligned Date Range |
| | `location` | String | Optional | CV Experience Entry: Role Location (City, Country, Remote) |
| | `achievements` | Array of Strings | **Required (min 1)**| CV Experience Entry: Bullet Points (Surgically tailored in Studio) |
| **Featured Projects** | `name` | String | Optional | CV Projects Section: Project Title |
| | `tech_stack` | Array of Strings | Optional | CV Projects Section: Inline Tech Stack Tags (`[Stack: ...]`) |
| | `summary` | Text | Optional | CV Projects Section: Project Impact Bullet |
| | `link` | Clean URL | Optional | CV Projects Section: Live Demo / Codebase Link |
| **Education & Credentials**| `institution` | String | Optional | CV Education Section: University / College Name |
| | `degree` | String | Optional | CV Education Section: Degree (e.g., B.Sc. Computer Science) |
| | `graduation_year` | Integer | Optional | CV Education Section: Right-aligned Year |
| | `grade_or_gpa` | String | Optional | CV Education Section: Honors / GPA |
| | `certifications` | Array of Objects | Optional | CV Certifications Section: Issuer, Title, Date |
| | `languages` | Array of Objects | Optional | CV Languages Section: Language & Proficiency level |
| **Custom Sections** | `custom_sections` | Array of Objects | Optional | Dynamic Custom Sections: Publications, Patents, Honors |

---

## 3. The 6-Page Sequential Funnel Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   STEPPER PROGRESSION                                  │
│  [1. Track & Goal] ─► [2. Identity & Mobility] ─► [3. Skills] ─► [4. Experience] ─►   │
│                      ─► [5. Featured Projects] ─► [6. Education & Review]              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Page 1: Career Track, Target Role & Fast-Forward Shortcut

#### UX Objective:
Capture the candidate's immediate career goal, define their primary persona, and offer the 1-click CV upload shortcut to eliminate manual typing for the rest of the wizard.

#### Fields & Input Controls:
1. **The Fast-Forward Shortcut (Top Hero Card):**
   - **Control:** Large, drag-and-drop file target.
   - **Accepted Formats:** `.pdf`, `.tex`, `.docx`.
   - **UX Behavior:** Dropping a file triggers immediate background parsing (`POST /api/v1/profiles/parse-latex` or `/upload-resume`). A progress bar reads: *"Extracting work history, skills, and credentials..."*. Once complete, all subsequent pages are pre-populated with extracted facts.
   - **Micro-copy:** *"Have an existing CV? Drop it here to auto-fill your profile in 3 seconds. You can review and refine every section."*
2. **Primary Target Job Title (Required):**
   - **Control:** Single-line search/autocomplete input + quick recommendation chips (`Senior Data Scientist`, `Fullstack Engineer`, `AI Engineer`, `Backend Systems Architect`).
   - **Validation:** Minimum 3 characters.
3. **Alternative Job Titles (Optional):**
   - **Control:** Multi-tag input (type and press Enter).
   - **Purpose:** Expands the automated query generator for job board scraping.
4. **Seniority Stage & Years of Experience (Required):**
   - **Control A:** Segmented pill selector (`Junior: 0–2 yrs`, `Mid-Level: 2–5 yrs`, `Senior: 5–8 yrs`, `Lead / Principal: 8+ yrs`).
   - **Control B:** Number slider ($0\text{ to }20+\text{ years}$).
5. **Executive Summary / Bio (Required):**
   - **Control:** Multi-line textarea (character count indicator: $150\text{--}400$ characters recommended).
   - **UX Assist:** An *"AI Draft Suggestion"* button based on the target title and years selected.
   - **CV Mapping:** Translates directly into the bold narrative summary at the top of the CV.

#### Navigation Actions:
* `[Continue to Identity & Locations →]`
* Status indicator: *"Auto-saved just now"*.

---

### Page 2: Personal Identity, Regional Contacts & Mobility

#### UX Objective:
Collect essential contact information, establish multi-country telephone identifiers for cross-border recruitment, and configure search geographies.

#### Fields & Input Controls:
1. **Full Legal Name (Required):**
   - **Control:** Text input (pre-filled from initial account sign-up).
2. **Primary Email (Required):**
   - **Control:** Email input (pre-filled from account sign-up; editable).
3. **Regional Contact Numbers Registry (Required — min 1 number):**
   - **Control:** Dynamic list builder. Each entry contains:
     - Country flag/dial code dropdown (`🇪🇬 +20`, `🇸🇦 +966`, `🇦🇪 +971`, `🇺🇸 +1`, etc.).
     - Phone number text input.
     - Label tag (`Egypt Mobile`, `Saudi Roaming/Zain`, `WhatsApp Only`).
     - Radio button: `[●] Set as Primary Contact`.
   - **UX Value:** When applying to Saudi jobs, Tailored automatically renders the Saudi number on the CV; for Egyptian jobs, it switches to the Egyptian number.
4. **Professional Links (Optional):**
   - **Control:** Grouped link inputs with automatic protocol stripping:
     - `LinkedIn URL:` Auto-strips `https://www.linkedin.com/in/` to show clean handles on the CV.
     - `GitHub URL:` Auto-strips `https://github.com/`.
     - `Portfolio / Personal Website URL:` Clean link display.
5. **Current Residence (Required):**
   - **Control:** Two side-by-side inputs: `City` (e.g. *Cairo*) and `Country` (e.g. *Egypt*).
6. **Target Locations & Mobility (Required — min 1 target):**
   - **Control:** Dynamic multi-location chip builder:
     - City search input (e.g., *Riyadh*, *Dubai*, *Remote*).
     - Per-city work mode checkboxes: `[✓] Remote`, `[✓] Hybrid`, `[✓] On-site`.
     - Relocation toggle: `[✓] Open to international relocation`.

#### Navigation Actions:
* `[← Back to Career Track]`
* `[Continue to Skills & Tools →]`

---

### Page 3: Categorized Skills & Tools Taxonomy

#### UX Objective:
Structure candidate capabilities into verified, categorized taxonomy buckets. This ensures ATS parsers see categorized keyword rows rather than an unstructured keyword dump.

#### Fields & Input Controls:
1. **Core Competencies & Domain Concepts (Required — min 3):**
   - **Control:** Multi-tag input with auto-suggest chips (`System Architecture`, `Dynamic Pricing`, `Microservices`, `ETL Pipelines`, `Distributed Systems`).
   - **CV Mapping:** Translates to the first row of the Technical Skills block.
2. **Programming Languages (Optional):**
   - **Control:** Tag selector chips (`Python`, `TypeScript`, `SQL`, `Go`, `Java`, `C++`, `Rust`, `+ Custom`).
3. **Frameworks & Libraries (Optional):**
   - **Control:** Tag selector chips (`FastAPI`, `PyTorch`, `React`, `Django`, `Node.js`, `TensorFlow`, `Pandas`, `+ Custom`).
4. **Tools, Platforms & Cloud Infrastructure (Optional):**
   - **Control:** Tag selector chips (`Docker`, `Kubernetes`, `PostgreSQL`, `AWS`, `Redis`, `Git`, `Kafka`, `GCP`, `+ Custom`).

#### UX Assist Features:
* **"Suggested for your role" Section:** Based on the target title selected in Page 1, surfaces 10 high-probability industry skills with 1-click `[+]` add buttons.
* **Drag-to-Reorder:** Users can re-order skills so their strongest competencies appear first on the compiled CV.

#### Navigation Actions:
* `[← Back to Identity]`
* `[Continue to Work Experience →]`

---

### Page 4: Work Experience & Measurable Achievements

#### UX Objective:
Capture chronological employment history and proven impact. This data forms the primary body of the CV and provides the factual substrate for surgical tailoring.

#### Fields & Input Controls:
Dynamic chronological entry list (`[+ Add Another Experience]`). Each job card contains:
1. **Company Name (Required):** Text input with company logo autocomplete.
2. **Job Title / Role (Required):** Text input.
3. **Location (Optional):** E.g. *"Cairo, Egypt (Hybrid)"* or *"Remote"*.
4. **Date Range (Required):**
   - Start Date: Month / Year picker.
   - End Date: Month / Year picker OR `[✓] Currently Working Here (Present)`.
5. **Measurable Achievements & Bullet Points (Required — min 1 per role):**
   - **Control:** Multi-bullet dynamic list.
   - **Bullet Point Writing Assist (Inline UX Guide):**
     - Prompt hint: *"Start with an action verb + context + measurable result (e.g. 'Architected dynamic route pricing algorithms using FastAPI and PyTorch, reducing calculation latency by 42%')."*
     - **Inline Tag Support:** Supports special directives such as `[Role Summary]` for team/scope overviews, and `[Stack: Python, Docker, PostgreSQL]` for inline tech stack tagging.

#### Navigation Actions:
* `[← Back to Skills]`
* `[Continue to Featured Projects →]`

---

### Page 5: Featured Projects & Proof of Execution

#### UX Objective:
Document specific technical projects with explicit tech stacks. In modern ATS and technical recruitment, project stacks often qualify candidates who lack direct enterprise years.

#### Fields & Input Controls:
Dynamic entry list (`[+ Add Project]` or `[Skip this section — I have enough work experience]`):
1. **Project Name (Required if adding entry):** Text input.
2. **Project URL / Repository (Optional):** GitHub, Live Demo, or Paper link.
3. **Technologies Used (Required if adding entry):** Multi-tag selector (`Python`, `FastAPI`, `Docker`, etc.).
4. **Project Impact / Summary (Required if adding entry):**
   - 1–2 concise bullet points explaining problem solved, architecture used, and quantifiable outcome.

#### Navigation Actions:
* `[← Back to Experience]`
* `[Skip / Continue to Education & Credentials →]`

---

### Page 6: Education, Languages, Certifications & Final Review

#### UX Objective:
Collect academic background, spoken languages, and professional accreditations, then present a unified review card before saving the master profile.

#### Fields & Input Controls:
1. **Education Entries (Dynamic list):**
   - Institution Name (e.g., *Cairo University*).
   - Degree (e.g., *B.Sc. in Computer Science & Engineering*).
   - Field of Study.
   - Graduation Year (e.g., *2021*).
   - Optional GPA or Academic Honors (e.g., *Graduated with First Class Honors*).
2. **Language Proficiencies (Dynamic list):**
   - Language name (e.g., *English*, *Arabic*, *German*).
   - Proficiency level dropdown (`Native / Bilingual`, `Professional Working`, `Fluent`, `Intermediate`).
3. **Certifications & Accreditations (Optional):**
   - Certification Title (e.g., *AWS Certified Solutions Architect*).
   - Issuer Organization (e.g., *Amazon Web Services*).
   - Year / Credential URL.
4. **Dynamic Custom Sections (Optional — e.g. Publications, Patents, Honors):**
   - Ability to add a custom titled section with bullet points.
5. **Master Review Card:**
   - Visual readiness check: Shows completed sections with green verification badges (`✓ Identity Complete`, `✓ 14 Skills Added`, `✓ 3 Roles Documented`).
   - Action: **`[Save Master Profile & Unlock Job Radar 🚀]`**.

---

## 4. Direct Field-to-CV LaTeX Rendering Matrix

The table below illustrates how the profile fields assemble into the standard executive ATS LaTeX document:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  ATS CV DOCUMENT ANATOMY                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ HEADER:           {full_name}                                                          │
│                   {target_title} • {dynamic_regional_phone} • {primary_email}          │
│                   {linkedin_handle} • {github_handle} • {current_city, country}        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ SUMMARY:          {summary_bio}                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ EXPERIENCE:       \textbf{{role}} — \textbf{{company}} \hfill {start_date} -- {end}   │
│                   \textit{{location}}                                                  │
│                   • {achievements[0]} [Injected job keywords during Studio tailor]    │
│                   • {achievements[1]}                                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PROJECTS:         \textbf{{name}} | \textit{{tech_stack}} \hfill {link}               │
│                   • {summary}                                                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ SKILLS:           \textbf{Core Competencies:} {core_skills}                            │
│                   \textbf{Languages:} {programming_languages}                          │
│                   \textbf{Frameworks & Tools:} {frameworks_and_libraries, tools}       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ EDUCATION:        \textbf{{degree}}, {institution} \hfill {graduation_year}            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ LANGUAGES:        {language}: {proficiency}                                            │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Navigation, State & Validation Mechanics

1. **Progress Tracker:**
   - Linear header indicator displaying: `Step X of 6: {Step Name}`.
   - Clickable completed steps allowing candidates to jump backward to edit previous pages without losing forward progress.
2. **Draft Auto-Saving:**
   - Every input blur immediately syncs state to browser storage and backend via `PATCH /api/v1/profiles/{id}`.
   - If the user drops off on Page 4 and returns next week, the application prompts: *"Resume where you left off on Work Experience? [Resume] [Start Fresh]"*.
3. **Soft Validation:**
   - Only minimum viable fields are strictly required (Full Name, Target Title, Years, 1 Contact, 1 Role or Skills). 
   - Sections like Projects, Certifications, and Custom Sections include explicit `[Skip this step]` controls to prevent user frustration.
4. **Completion Destination:**
   - Upon clicking `Save Master Profile`, the user seamlessly transitions to **Step 3 of Onboarding (The 30-Day Free Trial Gate with the Skip button)**, followed immediately by their personalized, pre-scored Job Radar feed!

