from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import projects, tasks, attempts, sessions

# Initialize KOR Kernel global (or singleton) integration
# Ideally KOR should be initialized once.
try:
    from kor import Kernel
except ImportError:
    Kernel = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize KOR Kernel if available
    print("Initializing KOR Kernel...")
    if Kernel:
        # Assuming Kernel has an async boot or similar. 
        # For now, we just ensure it's importable.
        pass
    yield
    # Shutdown logic if needed
    print("Shutting down KOR Kanban Backend...")

app = FastAPI(title="KOR Kanban API", lifespan=lifespan)

app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(attempts.router)
app.include_router(sessions.router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "kor-kanban-backend"}

@app.get("/api/status")
def get_status():
    return {
        "success": True,
        "data": {
            "logged_in": True,
            "profile": {
                "user_id": "kor-user",
                "username": "KOR User",
                "email": "user@kor.sdk",
                "providers": []
            },
            "degraded": False
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3001, reload=True)
