# Prompt 5 — Email Notification

**Used by:** Optionally invoked before the Gmail Notification node, to write a short, human-friendly summary line for the email body. In the default configuration (see `docs/n8n-configuration.md`) this text is templated directly without an extra LLM call, to save latency and cost; this prompt is provided for the case where a more natural, varied notification tone is wanted.

```
Write a 1-2 sentence email notification telling a colleague that a research
report is ready.

Topic: {{topic}}
Number of sources used: {{summaryCount}}
Review status: {{reviewStatus}}   (PASS or FAIL)

If review status is FAIL, the tone should gently flag that a quick human
check is recommended before sharing the report further. If PASS, the tone
should be a simple, professional "ready to read" notification.

Return only the 1-2 sentences, no subject line, no greeting/signoff (the
node adds those separately).
```

**Design notes:**
- Kept deliberately short — this is a notification, not the report itself; the report's actual content lives only in the Drive file, never duplicated into the email body, to avoid two diverging copies of the same content existing in two places.
- The FAIL-path tone instruction is what keeps a failed Quality Review from being silently forwarded as if everything were fine.
