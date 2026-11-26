import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env", override=True)
load_dotenv(_BACKEND_ROOT / ".env", override=True)

class Settings(BaseModel):
    app_name: str = "Tailored"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    artifact_root: Path = Path(__file__).resolve().parent.parent.parent / "artifacts" / "generated"
    
    # Database URL (Postgres default with SQLite fallback for offline work)
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://tailored_user:tailored_password@localhost:5432/tailored_db"
    )
    
    # AI / Vertex Configuration
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0898783307").strip()
    google_cloud_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "global").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    ai_provider: str = os.getenv("AI_PROVIDER", "gemini").strip()  # "gemini", "mock", "ollama"

    # Apify Configuration & Credit Protection Cap ($5 testing budget -> max 2 items per actor)
    apify_api_token: Optional[str] = os.getenv("APIFY_API_TOKEN")
    apify_linkedin_actor_id: str = os.getenv("APIFY_LINKEDIN_ACTOR_ID", "curious_coder/linkedin-jobs-scraper")
    apify_linkedin_posts_actor_id: str = os.getenv(
        "APIFY_LINKEDIN_POSTS_ACTOR_ID", "codetr/linkedin-hiring-posts-scraper"
    )
    apify_max_items_per_actor: int = int(os.getenv("APIFY_MAX_ITEMS_PER_ACTOR", "2"))

settings = Settings()
