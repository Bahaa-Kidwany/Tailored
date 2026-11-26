import sys
import json
from pathlib import Path


# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import init_db

from app.schemas.user_profile import UserProfile, CareerPersona

client = TestClient(app)

def test_profile_lifecycle_and_db_persistence():
    # 1. Initialize tables
    init_db()

    # 2. Check DB status endpoint
    db_resp = client.get("/api/v1/profiles/system/db-status")
    assert db_resp.status_code == 200
    db_info = db_resp.json()
    assert "engine_type" in db_info
    assert db_info["status"] == "healthy"
    print(f"Active DB Engine: {db_info['engine_type']}")

    # 3. Load sample user profile fixture
    fixture_path = Path(__file__).parent / "fixtures" / "sample_user_profile.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        profile_json = json.load(f)

    # 4. POST /api/v1/profiles
    create_resp = client.post("/api/v1/profiles", json=profile_json)
    assert create_resp.status_code == 201, f"Failed to create profile: {create_resp.text}"
    created_data = create_resp.json()
    profile_id = created_data["id"]
    profile_obj = created_data["profile"]

    assert profile_id is not None
    assert profile_obj["personal_info"]["full_name"] == "Ahmed El-Sayed"
    assert len(profile_obj["personal_info"]["contact_numbers"]) >= 2
    assert profile_obj["personal_info"]["contact_numbers"][0]["dial_code"] == "+20"
    assert profile_obj["personal_info"]["contact_numbers"][1]["dial_code"] == "+966"
    assert len(profile_obj["residence_and_mobility"]["target_locations"]) >= 3
    assert len(profile_obj["career_personas"]) >= 2
    print(f"Created profile ID: {profile_id} with {len(profile_obj['career_personas'])} personas.")

    # 5. GET /api/v1/profiles (List)
    list_resp = client.get("/api/v1/profiles")
    assert list_resp.status_code == 200
    summaries = list_resp.json()
    assert len(summaries) >= 1
    found_summary = next((s for s in summaries if s["id"] == profile_id), None)
    assert found_summary is not None
    assert found_summary["full_name"] == "Ahmed El-Sayed"
    assert found_summary["persona_count"] >= 2
    print(f"Listing confirmed profile summary: {found_summary['primary_persona_title']}")

    # 6. GET /api/v1/profiles/{id}
    get_resp = client.get(f"/api/v1/profiles/{profile_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()["profile"]
    assert retrieved["personal_info"]["primary_email"] == "ahmed.elsayed@example.com"
    assert retrieved["education"][0]["institution"] == "Cairo University"

    # 7. GET /api/v1/profiles/{id}/search-request/{persona_id}
    persona_id = retrieved["career_personas"][0]["persona_id"]
    search_req_resp = client.get(f"/api/v1/profiles/{profile_id}/search-request/{persona_id}")
    assert search_req_resp.status_code == 200
    search_req = search_req_resp.json()
    assert search_req["persona_id"] == persona_id
    assert "Data Scientist" in search_req["query_terms"]
    assert len(search_req["target_locations"]) >= 3
    print(f"Derived search request successfully generated {len(search_req['target_locations'])} target locations.")

    # 8. POST /api/v1/profiles/{id}/personas (Add 3rd persona track)
    new_persona = {
        "persona_id": "ai_engineer_track",
        "target_title": "AI & LLM Solutions Engineer",
        "alternative_titles": ["Generative AI Engineer", "NLP Specialist"],
        "is_primary": False,
        "seniority_level": "Senior",
        "years_of_experience": 4,
        "summary_bio": "Specialist in deploying production LLM inference pipelines and RAG systems.",
        "skills_and_tools": {
            "core_skills": ["RAG", "Prompt Engineering", "Fine-tuning"],
            "programming_languages": ["Python"],
            "frameworks_and_libraries": ["LangChain", "LlamaIndex", "HuggingFace"],
            "tools_and_platforms": ["vLLM", "Docker", "ChromaDB"]
        },
        "experience_highlights": [],
        "featured_projects": [],
        "certifications": []
    }
    add_persona_resp = client.post(f"/api/v1/profiles/{profile_id}/personas", json=new_persona)
    assert add_persona_resp.status_code == 200
    updated_profile = add_persona_resp.json()["profile"]
    assert len(updated_profile["career_personas"]) == len(profile_obj["career_personas"]) + 1
    print("Successfully appended 3rd persona track.")

    # 9. PATCH /api/v1/profiles/{id}/personas/{persona_id}/primary
    switch_resp = client.patch(f"/api/v1/profiles/{profile_id}/personas/ai_engineer_track/primary")
    assert switch_resp.status_code == 200
    switched_profile = switch_resp.json()["profile"]
    switched_primary = next((p for p in switched_profile["career_personas"] if p["persona_id"] == "ai_engineer_track"), None)
    assert switched_primary is not None and switched_primary["is_primary"] is True
    print("Switched active primary persona to AI & LLM Solutions Engineer.")

    # 10. Clean up: DELETE /api/v1/profiles/{id}
    del_resp = client.delete(f"/api/v1/profiles/{profile_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    # Confirm deletion
    not_found_resp = client.get(f"/api/v1/profiles/{profile_id}")
    assert not_found_resp.status_code == 404
    print("Cleaned up profile and verified cascading deletion.")

if __name__ == "__main__":
    test_profile_lifecycle_and_db_persistence()
    print("All Profile API & DB tests passed successfully!")
