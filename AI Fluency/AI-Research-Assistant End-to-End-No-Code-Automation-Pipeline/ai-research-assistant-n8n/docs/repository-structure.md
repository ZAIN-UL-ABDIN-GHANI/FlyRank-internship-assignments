# GitHub Repository Structure

```
ai-research-assistant-n8n/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
│
├── workflows/
│   └── ai-research-assistant.json        # Importable n8n workflow (no secrets)
│
├── prompts/
│   ├── 01-research-prompt.md
│   ├── 02-summarization-prompt.md
│   ├── 03-report-generation-prompt.md
│   ├── 04-quality-review-prompt.md
│   └── 05-email-notification-prompt.md
│
├── diagrams/
│   ├── architecture-diagram.md
│   └── workflow-diagram.md
│
├── docs/
│   ├── srs.md                            # Requirement Analysis (SRS)
│   ├── solution-planning.md              # n8n vs Make.com vs Zapier
│   ├── architecture.md                   # System architecture, component detail
│   ├── workflow-design.md                # Node-by-node design
│   ├── n8n-configuration.md              # Credentials, parameters, expressions, env vars
│   ├── error-handling.md
│   ├── security.md
│   ├── performance.md
│   ├── testing.md                        # 5 real test runs
│   ├── human-review.md
│   ├── future-improvements.md
│   ├── deployment-guide.md
│   ├── installation-guide.md
│   ├── configuration-guide.md
│   ├── api-setup-guide.md
│   ├── troubleshooting-guide.md
│   ├── screenshots.md                    # Screenshot capture checklist
│   ├── demo-video-script.md
│   ├── resume-bullets.md
│   └── repository-structure.md           # This file
│
└── assets/
    └── screenshots/                      # Populated per docs/screenshots.md before publishing
        └── .gitkeep
```

## Design Rationale
- **`workflows/`** is separated from `docs/` because it is the one directory a user imports directly into n8n — keeping it free of documentation clutter.
- **`prompts/`** is its own top-level directory (not nested under `docs/`) because prompts are a versioned engineering artifact in their own right, not narrative documentation — this mirrors how a conventional software repo separates `src/` from `docs/`.
- **`diagrams/`** is separated from `docs/` so diagrams can be referenced identically from the README, the architecture doc, and the workflow-design doc without duplicating the ASCII art three times.
- **`assets/screenshots/`** ships with only a `.gitkeep` placeholder in this deliverable, since no live n8n instance was screenshotted for this exercise — see `docs/screenshots.md` for exactly what to capture before treating this as publish-ready.
