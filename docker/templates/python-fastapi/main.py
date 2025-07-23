from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(
    title="{{PROJECT_NAME}}",
    description="{{PROJECT_NAME}} API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>{{PROJECT_NAME}}</title>
        </head>
        <body>
            <h1>Welcome to {{PROJECT_NAME}}!</h1>
            <p><a href="/api/docs">API Documentation</a></p>
        </body>
    </html>
    """

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "project": "{{PROJECT_NAME}}"}

@app.get("/api/info")
async def project_info():
    return {
        "name": "{{PROJECT_NAME}}",
        "version": "1.0.0",
        "environment": os.getenv("NODE_ENV", "development")
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["./"]
    )
