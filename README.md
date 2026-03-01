# ColdRead

> I built this to see my resume the way a machine does.

ColdRead is a portfolio project and technical demo exploring AI-assisted resume analysis, built to understand how modern hiring pipelines actually evaluate candidates, and to surface that process transparently.

It operates from a dual-perspective workflow: it evaluates my resume the way an AI screener would, identifies coverage gaps and terminology mismatches, then generates a tailored variant that closes those gaps using only my verified experience. The goal is transparency by showing me the scoring logic, not just the output.

---

## Why This Exists

Modern hiring is increasingly filtered by AI systems before a human ever reads a resume. Most engineers have no visibility into how their applications are being scored. I built ColdRead to make that process transparent for myself, and to compete in it without compromising the truthfulness of my claims.

The other problem ColdRead solves: resumes built from other resumes accumulate drift. Claims get inflated, gaps get papered over, and the result is a document that looks polished but doesn't survive a technical interview. I built ColdRead around canonical experience narratives — ground truth I author once, from which all tailored variants are derived.

---

## Features

### For Me
- **Fit Assessment** — I paste a job description and get a structured fit analysis: strong matches, soft gaps (adjacent or partial experience), and hard gaps (no experience). Categorized as Strong / Moderate / Borderline / Poor with concrete reasoning.
- **Resume Generation** — Generate a tailored resume variant for a specific role, derived from my canonical experience narrative. Every claim is grounded in verified experience.
- **AI Screener Simulation** — See my resume scored from the perspective of an AI screening system. Keyword coverage report, terminology alignment check, semantic similarity analysis against the JD.
- **Gap Detection** — Explicit identification of JD requirements where my experience is missing, adjacent, or inconsistently represented. Gaps remain gaps — ColdRead doesn't paper over them.
- **Terminology Alignment** — Identifies where I have the right experience but am using different words than the JD. Fixes the words, not the experience.
- **Coverage Heatmap** — Visual breakdown of my skill domain coverage: which areas are strong, which are thin, and which are dated. Gives me an honest picture of my profile at a glance rather than a flat list of technologies.
- **Interview Prep Mode** — Generates likely interview questions based on my tailored resume, so I can anticipate what my claims will invite.
- **Export** — Download tailored resumes as ATS-friendly `.docx` or plain text. PDF coming.

### For Recruiters & Hiring Managers (Planned)
- **Recruiter Portal** — Upload a job posting or paste a JD and get a fit assessment against my verified experience, along with a tailored resume variant.
- **Honest Q&A** — Ask specific questions about my background and receive accurate, evidence-grounded answers — including honest acknowledgment of gaps.
- **Coverage Heatmap** — Visual representation of skill domain coverage, strength, and recency. Gives an immediate, honest picture of where my experience is strong, where it's thin, and where it's dated — without wading through bullet points.

---

## How It Works

ColdRead is built around three core concepts:

**1. Canonical Narratives**
Rather than building resumes from other resumes, ColdRead starts from first-person experience narratives — detailed accounts of what I actually did on each project. These are the ground truth. All resume variants are derived from them, not from each other.

**2. Dual-Perspective Workflow**
Every resume generation runs through two perspectives:
- *AI Screener* — evaluates the JD requirements and scores coverage against my narrative
- *Resume Generator* — produces a tailored variant guided by the screener's coverage report
- *Screener Re-evaluation* — validates the generated resume against the original requirements before delivery

**3. Versioned, Branching Variants**
Each role produces a new resume variant branched from the canonical baseline. Changes are deltas — reweighting emphasis, aligning terminology, de-emphasizing irrelevant experience — not full rewrites. Prior validated phrasing is preserved unless explicitly overridden.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Testing | Vitest, React Testing Library, Playwright |
| Backend | FastAPI (Python) |
| Database | PostgreSQL (via Supabase) |
| File Storage | Supabase Storage |
| AI | Anthropic Claude API |
| Deployment | Vercel (frontend), Railway or Fly.io (backend) |

### Architecture Notes

Prompts are stored in the database, not hardcoded in the codebase. This prevents prompt exposure through source inspection and enables prompt versioning and iteration without redeployment.

Resume generation runs through the Anthropic API server-side. The Claude API key never touches the client.

---

## Project Status

🚧 **Active development.** Core fit assessment and resume generation are being built first. Recruiter portal is planned for a later phase.

See [Issues](../../issues) for current priorities and [Projects](../../projects) for the roadmap.

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/mdaxtman/coldread.git
cd coldread

# Frontend
cd client
npm install
npm run dev

# Backend
cd ../server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Environment variables required — see `.env.example` in both `client/` and `server/`.

---

## Design Principles

- **Truthfulness over optimization.** Every claim must be interview-defensible. Gaps remain gaps.
- **Transparency.** Show the screener's scoring report, not just the output. I should understand why the resume looks the way it does.
- **Narrative-first.** Ground truth comes from what I actually did, not from previous resume versions.
- **No hidden text, no keyword stuffing, no prompt injection.** Optimization happens through accurate positioning, not manipulation.

---

## License

MIT
