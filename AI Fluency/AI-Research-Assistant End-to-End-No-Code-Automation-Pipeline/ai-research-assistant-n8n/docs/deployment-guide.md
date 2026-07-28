# Deployment Guide

This guide covers deploying n8n itself. For importing and configuring *this* workflow once n8n is running, see `docs/installation-guide.md`.

## Option A — n8n Cloud (fastest path)
1. Create an account at n8n's cloud offering.
2. Create a new workflow.
3. Skip to `docs/installation-guide.md` to import `workflows/ai-research-assistant.json`.

This option requires no server management and is recommended for evaluating the project quickly.

## Option B — Self-Hosted via Docker (recommended for production/portfolio use)

### Prerequisites
- Docker and Docker Compose installed
- A domain or subdomain (optional, for a stable webhook/OAuth redirect URL if you later add triggers beyond Manual Trigger)

### docker-compose.yml
```yaml
version: "3.7"
services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=${N8N_HOST:-localhost}
      - N8N_PORT=5678
      - N8N_PROTOCOL=${N8N_PROTOCOL:-http}
      - GENERIC_TIMEZONE=${TZ:-UTC}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
```

### Steps
1. Copy `.env.example` (repo root) to `.env` and fill in real values, including a strong random `N8N_ENCRYPTION_KEY` (used by n8n to encrypt stored credentials at rest).
2. Run: `docker compose up -d`
3. Open `http://localhost:5678` (or your configured host) and complete n8n's first-run owner-account setup.
4. Continue to `docs/installation-guide.md`.

### Production Notes
- Put n8n behind a reverse proxy (nginx/Caddy) with HTTPS if exposing it beyond localhost — required for Google OAuth redirect URIs to work correctly in production.
- Back up the `n8n_data` volume regularly; it contains the encrypted credential store and all workflow definitions.
- Set `N8N_ENCRYPTION_KEY` once and never change it after credentials have been saved, or existing encrypted credentials will become unreadable.

## Environment Variables Reference
See `docs/n8n-configuration.md`, Section 2, and the repository's `.env.example` for the full list of variables this specific workflow needs (as opposed to n8n-instance-level variables like `N8N_ENCRYPTION_KEY` above).
