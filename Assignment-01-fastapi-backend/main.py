from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Backend is running"}


@app.get("/api/hello")
def read_hello():
    return {"success": True, "message": "Hello from my FastAPI backend!"}
