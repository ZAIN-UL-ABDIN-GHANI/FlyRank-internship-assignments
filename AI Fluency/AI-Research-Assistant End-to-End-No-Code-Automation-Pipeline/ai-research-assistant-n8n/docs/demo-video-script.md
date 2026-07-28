# Demo Video Script (2–3 Minutes)

**Format:** Screen recording with voiceover. Suggested length: 2:30.

---

**[0:00–0:15] Hook + Problem**
*(Screen: a blank document, a timer graphic)*

> "Researching a topic properly — searching, reading, summarizing, writing it up — takes most people 45 minutes to an hour. I built a no-code AI workflow that does it end to end in under two minutes. Let me show you."

**[0:15–0:35] Architecture Overview**
*(Screen: `diagrams/architecture-diagram.md` or the rendered n8n canvas)*

> "This is an n8n workflow. You give it a topic. It searches the web for current sources, summarizes each one with an LLM, assembles a Markdown report, runs an automated quality check, files the report in Google Drive, and emails you a notification — all without writing a line of backend code."

**[0:35–1:15] Live Run**
*(Screen: n8n editor, Set Topic node)*

> "Let's run it live. I'll type a topic — let's say 'Cybersecurity' — and click Execute."
*(Nodes light up green one by one)*
> "Watch the nodes execute: it's hitting the search API now... splitting the results into individual items... summarizing each one with the LLM... and now it's assembling everything into a report."

**[1:15–1:45] Show the Output**
*(Screen: the generated Markdown report in Google Drive, then the Gmail notification)*

> "Here's the finished report in Google Drive — a title, an executive summary, sourced key findings, and a full source list. And here's the email notification that just landed in my inbox with a direct link."

**[1:45–2:10] Engineering Highlights**
*(Screen: `docs/error-handling.md` or `docs/security.md` briefly)*

> "This isn't just a happy-path demo. Every external API call has retry logic and a documented fallback — if the search API fails, if the LLM times out, if Drive upload fails, nothing silently breaks or gets lost. Credentials are scoped to least privilege, and there's an automated quality-review pass before anything gets filed or sent."

**[2:10–2:30] Close**
*(Screen: README.md, GitHub repo structure)*

> "Full documentation — architecture, every prompt, five tested runs across different industries, and a complete setup guide — is in the repo, linked below. Thanks for watching."

---

**Production notes:**
- Capture the "Live Run" section using one of the five topics already validated in `docs/testing.md`, so the on-screen result matches documented, expected behavior.
- Keep the LLM Summarizer's per-item execution visible for at least 2–3 items before cutting away, so viewers see the looping pattern, not just a single call.
