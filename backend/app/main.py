from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db
from app.api.routes.jobs import router as jobs_router
from app.api.routes.cv_fit import router as cv_fit_router
from app.api.routes.cover_letter import router as cover_letter_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.pipeline import router as pipeline_router

app = FastAPI(title="Tailored API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(jobs_router, prefix="/api/v1")
app.include_router(cv_fit_router, prefix="/api/v1")
app.include_router(cover_letter_router, prefix="/api/v1")
app.include_router(profiles_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "tailored-api"}
