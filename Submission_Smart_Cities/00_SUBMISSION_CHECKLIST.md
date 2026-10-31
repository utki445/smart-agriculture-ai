# Submission Checklist — Design of Smart Cities

**Project:** Smart Water Management for Urban Green Infrastructure
A low-cost, network-resilient edge-IoT irrigation node with deep-learning soil analysis.

## Deadlines

| Where | What | Due |
|---|---|---|
| **VTOP** | Project report (SRS, SDS, Implementation, Testing, Outcome) + unique outcome | **3 November 2026** |
| **MS Teams** | All files below | **4 November 2026** |

Only one team member needs to submit.

---

## Status

| # | Deliverable | Status | File |
|---|---|---|---|
| 1 | Final Project Report | **Ready** | `01_Project_Report/Final_Project_Report_Smart_Cities.docx` (+ PDF) |
| 2 | Project Presentation (PPT) | **Ready** | `02_Presentation/Project_Presentation_Smart_Cities.pptx` (+ PDF) |
| 3 | Demonstration Video (10 min max) | **You have this** | Place it in `03_Demonstration_Video/` |
| 4 | Plagiarism Report | **You must generate** | See `04_Plagiarism_Report/HOW_TO_GENERATE.md` |
| 5 | GitHub Repository Link | **Ready** | `05_GitHub_Link/GitHub_Repository_Link.md` |
| 6 | IEEE research paper *or* Form B | **Ready (paper)** | `06_Research_Paper_IP/Research_Paper_IEEE_Format.docx` |

**Before submitting, fill in the name fields on the title page of items 1 and 2.**
They are deliberately left blank.

---

## What each deliverable contains

### 1. Final Project Report — 22 pages

Structured exactly to the format the faculty specified:

| Section | Contents |
|---|---|
| 1. Introduction | Purpose, scope, smart-city context, definitions |
| **2. SRS** | Product perspective and functions, stakeholders, FR-1…FR-10, NFR-1…NFR-6, external interfaces, constraints |
| **3. SDS** | Architecture, deployment design, hardware, circuit, **data design**, module design, control law, ML pipeline, design rationale |
| 4. Implementation | Firmware, calibration, collector, classifier, dashboard, prototype, stack |
| 5. Testing | Strategy, 7 fault-injection tests, control-law validation, classifier evaluation |
| 6. Outcome | Traceability matrix, measured outcomes, **6.3 unique outcome**, limitations, future scope, conclusion |

Includes an auto-generated table of contents, 6 figures and 20 tables.

> **Section 6.3 is the "unique outcome" the faculty asked for.** It reports the
> measurement of how much conventional evaluation inflates soil-image classification
> accuracy — 45.0 to 47.9 percentage points on this dataset. This is also the basis
> of the research paper in item 6.

### 2. Project Presentation — 21 slides

Same spine as the report: Opening → SRS → SDS → Implementation → Testing → Outcome.
Speaker notes are included on the substantive slides. Roughly 20–25 minutes at
1.5–2 min per slide.

### 5. GitHub Repository

`https://github.com/utki445/smart-agriculture-ai`

**Check before submitting:** the repository must be **public**, and the README should
be the current version (it was corrected on 31 Oct 2026 — the previous one quoted
accuracy figures that contradicted this report).

---

## Suggested order of work

1. **Fill in the title-page fields** on the report and the PPT (5 min)
2. **Run the plagiarism check** on the report — this usually has a queue, so start it first
3. **Drop the demo video** into `03_Demonstration_Video/`
4. **Verify the GitHub repo is public** and the README renders correctly
5. **Submit the report to VTOP** by 3 Nov
6. **Upload everything to MS Teams** by 4 Nov

---

## One consistency note

The report states soil-type accuracy as **44.6–46.8 %** (source-disjoint) rather than the
~94 % figure that appeared in older project documents. This is deliberate and is explained
in Sections 5.4 and 6.3 — it is the project's central finding, not an error.

Make sure the demonstration video and any slides you add do not quote the old figure.
If the video does, mention the correction verbally when presenting.
