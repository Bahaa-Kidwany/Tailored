import logging
from sqlmodel import SQLModel, create_engine, Session, text
from app.core.config import settings

logger = logging.getLogger(__name__)

def create_db_engine():
    # Attempt PostgreSQL first if configured
    if "postgresql" in settings.database_url:
        try:
            pg_engine = create_engine(settings.database_url, echo=False, connect_args={"connect_timeout": 1})
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to PostgreSQL at %s", settings.database_url)
            return pg_engine
        except Exception as exc:
            logger.warning("PostgreSQL connection failed (%s). Falling back to local SQLite.", exc)
            
    sqlite_path = settings.base_dir / "tailored.db"
    return create_engine(f"sqlite:///{sqlite_path}", echo=False, connect_args={"check_same_thread": False})

engine = create_db_engine()

def init_db():
    # Ensure all SQLModel table models are registered
    import app.models.job  # noqa: F401
    import app.models.document  # noqa: F401
    import app.models.profile  # noqa: F401
    import app.models.pipeline  # noqa: F401
    SQLModel.metadata.create_all(engine)

    # Safe automated column migration for SQLite
    new_cols = [
        ("user_profiles", "custom_sections_json", "TEXT"),
        ("user_profiles", "active_persona_id", "VARCHAR"),
        ("generated_documents", "profile_id", "INTEGER"),
        ("generated_documents", "persona_id", "VARCHAR"),
        ("generated_documents", "company_about_text", "TEXT"),
        ("generated_documents", "location", "VARCHAR"),
        ("generated_documents", "location_type", "VARCHAR"),
        ("generated_documents", "fit_score", "FLOAT"),
        ("generated_documents", "parsed_skills_json", "TEXT"),
        ("generated_documents", "base_latex_content", "TEXT"),
        ("generated_documents", "tailored_latex_content", "TEXT"),
    ]
    with engine.connect() as conn:
        for table, col, col_type in new_cols:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                conn.rollback()

def get_session():
    with Session(engine) as session:
        yield session

