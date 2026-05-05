from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import jobs, generate

app = FastAPI(title="Job Search Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
