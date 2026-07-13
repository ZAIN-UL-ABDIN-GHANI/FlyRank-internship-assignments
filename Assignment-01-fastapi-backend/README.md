# FastAPI Minimal Backend

## Project Overview

This is the smallest possible backend server built with **FastAPI** and **Uvicorn**. It exposes exactly two JSON endpoints and includes automatic interactive API documentation (Swagger UI and ReDoc) out of the box, with no extra configuration required.

No authentication, no database, no Docker, no environment variables — just a clean, minimal API.

## Technologies Used

- **Python 3.12+**
- **FastAPI** — web framework for building the API
- **Uvicorn** — ASGI server used to run the FastAPI app

## Project Structure

```
fastapi-backend/
├── main.py            # Application code (2 endpoints)
├── requirements.txt    # Python dependencies
└── README.md            # Project documentation
```

## Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/<USERNAME>/<REPOSITORY>.git
cd <REPOSITORY>

python3 -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn main:app --reload
```

The server will start at:

```
http://127.0.0.1:8000
```

## API Endpoints

### GET `/`

Returns a status message confirming the server is running.

**Response:**
```json
{
  "message": "Backend is running"
}
```

### GET `/api/hello`

Returns a sample greeting message.

**Response:**
```json
{
  "success": true,
  "message": "Hello from my FastAPI backend!"
}
```

## Browser Testing

With the server running, open either URL directly in a browser:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/api/hello

The JSON response will render directly in the browser window.

### Interactive API Docs

FastAPI automatically generates interactive documentation for every endpoint:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

## curl Examples

**macOS/Linux (Terminal):**
```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/hello
```

**Windows CMD:**
```cmd
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/hello
```

**Windows PowerShell:**
```powershell
curl.exe http://127.0.0.1:8000/
curl.exe http://127.0.0.1:8000/api/hello
```

> Note: In PowerShell, `curl` is aliased to `Invoke-WebRequest`, which has different output formatting. Use `curl.exe` to invoke the real curl binary and get raw JSON output.

## License

This project is provided as-is for educational purposes.
