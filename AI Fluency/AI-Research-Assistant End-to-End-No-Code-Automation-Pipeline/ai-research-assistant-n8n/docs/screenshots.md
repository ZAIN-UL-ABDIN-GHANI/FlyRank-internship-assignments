# Screenshots to Capture for Documentation

This project's documentation is complete without screenshots, but the following should be captured from a live n8n instance and added to `assets/screenshots/` (with these exact filenames) before publishing this repository publicly, since they materially strengthen a portfolio/job-application deliverable.

| # | Filename | What to Capture | Where It's Used |
|---|---|---|---|
| 1 | `01-full-workflow-canvas.png` | The entire n8n canvas showing all nodes and connections, zoomed to fit | README.md hero image |
| 2 | `02-set-topic-node.png` | The Set Topic node's parameter panel, showing the `topic` field | `docs/installation-guide.md` |
| 3 | `03-http-request-search.png` | The Search API HTTP Request node's configuration panel (URL, auth, body) | `docs/n8n-configuration.md` |
| 4 | `04-llm-summarizer-node.png` | The LLM Summarizer HTTP Request node's configuration panel | `docs/n8n-configuration.md` |
| 5 | `05-successful-execution.png` | An execution view with all nodes green (successful run) | README.md, `docs/testing.md` |
| 6 | `06-failed-execution-example.png` | An execution view showing one node red with the error panel open (e.g., a deliberately triggered Search API auth failure) | `docs/troubleshooting-guide.md` |
| 7 | `07-generated-markdown-report.png` | The final `.md` report opened in Google Drive's preview | README.md, `docs/testing.md` |
| 8 | `08-drive-folder-listing.png` | The target Drive folder showing several filed reports with the naming convention visible | `docs/n8n-configuration.md` |
| 9 | `09-gmail-notification.png` | The received notification email in an inbox | README.md |
| 10 | `10-credentials-list.png` | The n8n Credentials settings page showing the four configured credentials (names only, values redacted) | `docs/api-setup-guide.md` |

**Security note:** before capturing #10, ensure no credential value is visible anywhere in the screenshot (n8n masks secret fields by default — do not screenshot with a field actively being edited/revealed).
