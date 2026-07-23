from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import exploit, quiz, recon, report, sessions, vuln

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EduVAPT-IoT",
    description=(
        "Guided and automated VAPT tool for teaching IoT/CCTV network security. "
        "Only operates against targets within the configured lab scope."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(recon.router)
app.include_router(vuln.router)
app.include_router(exploit.router)
app.include_router(report.router)
app.include_router(quiz.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
