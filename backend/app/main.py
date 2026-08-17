from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import capstone, quiz, report, scan, sessions, tasks, terminal

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EduVAPT-IoT",
    description=(
        "Guided, HTB-style VAPT lab for teaching IoT/CCTV network security. "
        "Only operates against targets within the configured lab scope."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(tasks.router)
app.include_router(scan.router)
app.include_router(report.router)
app.include_router(quiz.router)
app.include_router(capstone.router)
app.include_router(terminal.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
