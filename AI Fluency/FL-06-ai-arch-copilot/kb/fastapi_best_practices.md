# FastAPI Best Practices

## Request and Response Models
- Define Pydantic schemas for every request and response body. Never accept or return raw dicts.
- Validate inputs at the boundary so route handlers can assume well-formed data.

## Route Handlers
- Keep business logic out of route handlers. Handlers should call into services or graphs and format the response.
- Return proper HTTP status codes: 400 for bad input, 404 for missing resources, 500 only for unexpected failures.

## Configuration
- Load configuration (API keys, model names, paths) from environment variables, not hardcoded values.
- Provide a `.env.example` so the required variables are discoverable without exposing real secrets.

## Errors
- Raise HTTPException with a clear message for expected error cases. Do not let unhandled exceptions leak stack traces to clients.
