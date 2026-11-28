"""Phase 1 Verification Gate: auth_db, privacy_vault_db, profile_db, Auth Flows, ForwardAuth, Profile & LaTeX Parser."""

import secrets
import subprocess
import sys
import httpx
import pyotp

BASE = "http://localhost"


def assert_tables(db: str, role: str, expected: list[str]) -> None:
    out = subprocess.check_output(
        [
            "docker", "exec", "tailored-postgres",
            "psql", "-U", "tailored_admin", "-d", db, "-Atc",
            "SELECT tablename FROM pg_tables WHERE schemaname='public';",
        ],
        text=True,
    )
    tables = {line.strip() for line in out.splitlines() if line.strip()}
    missing = [t for t in expected if t not in tables]
    assert not missing, f"Missing tables in {db}: {missing} (found: {sorted(tables)})"
    print(f"[PASS] {db} schema verified ({len(expected)} tables).")


def main() -> int:
    assert_tables(
        "auth_db",
        "auth_svc",
        [
            "users",
            "oauth_identities",
            "user_sessions",
            "otp_verifications",
            "totp_mfa",
            "workspace_preferences",
            "privacy_consents",
            "feature_flags",
            "feature_flag_overrides",
            "outbox_events",
            "processed_events",
        ],
    )
    assert_tables("privacy_vault_db", "privacy_vault_svc", ["identity_pseudonyms"])
    assert_tables(
        "profile_db",
        "profile_svc",
        [
            "master_profiles",
            "contact_numbers",
            "target_locations",
            "career_personas",
            "education_records",
            "spoken_languages",
            "base_cv_templates",
            "outbox_events",
            "processed_events",
        ],
    )

    email = f"phase1_{secrets.token_hex(4)}@tailored.test"
    password = "SecurePassword123!"

    with httpx.Client(base_url=BASE, timeout=15.0) as client:
        # 1. Protected route blocks unauthenticated requests at Traefik ForwardAuth
        unauth = client.get("/api/v1/profiles/me")
        assert unauth.status_code == 401, f"Expected 401 on unauth, got {unauth.status_code}"

        # 2. Register + Verify OTP
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Mostafa Phase1"},
        )
        assert reg.status_code == 201, reg.text
        reg_data = reg.json()
        dev_otp = reg_data["dev_otp"]
        access_token = reg_data["access_token"]
        refresh_token = reg_data["refresh_token"]

        ver = client.post("/api/v1/auth/verify-email", json={"email": email, "code": dev_otp})
        assert ver.status_code == 200 and ver.json()["verified"] is True, ver.text

        # 3. Wrong password rejected
        bad_login = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass!"})
        assert bad_login.status_code == 401

        # 4. OAuth sole-login unlink guard test
        oauth_email = f"oauth_{secrets.token_hex(4)}@tailored.test"
        oauth_reg = client.post(
            "/api/v1/auth/oauth/google/callback",
            json={"provider_user_id": f"goog_{secrets.token_hex(4)}", "email": oauth_email, "full_name": "OAuth User"},
        )
        assert oauth_reg.status_code == 200, oauth_reg.text
        oauth_tok = oauth_reg.json()["access_token"]
        blocked_unlink = client.delete(
            "/api/v1/account/oauth/google",
            headers={"Authorization": f"Bearer {oauth_tok}"},
        )
        assert blocked_unlink.status_code == 400, f"Expected sole-login unlink block 400, got {blocked_unlink.status_code}"
        set_pw = client.post(
            "/api/v1/account/change-password",
            headers={"Authorization": f"Bearer {oauth_tok}"},
            json={"new_password": "AddedPassword123!"},
        )
        assert set_pw.status_code == 200
        ok_unlink = client.delete(
            "/api/v1/account/oauth/google",
            headers={"Authorization": f"Bearer {oauth_tok}"},
        )
        assert ok_unlink.status_code == 200, ok_unlink.text

        # 5. Setup & Enable TOTP 2FA + Login with 2FA
        auth_h = {"Authorization": f"Bearer {access_token}"}
        tfa_setup = client.post("/api/v1/account/2fa/setup", headers=auth_h)
        assert tfa_setup.status_code == 200, tfa_setup.text
        secret = tfa_setup.json()["secret"]
        code = pyotp.TOTP(secret).now()
        tfa_en = client.post("/api/v1/account/2fa/enable", headers=auth_h, json={"code": code})
        assert tfa_en.status_code == 200 and tfa_en.json()["enabled"] is True

        need_2fa = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert need_2fa.status_code == 401
        ok_2fa = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password, "totp_code": pyotp.TOTP(secret).now()},
        )
        assert ok_2fa.status_code == 200, ok_2fa.text

        # 6. Refresh token rotation & immediate Redis session revocation check
        ref = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert ref.status_code == 200, ref.text
        new_access = ref.json()["access_token"]
        new_h = {"Authorization": f"Bearer {new_access}"}
        assert client.get("/api/v1/account/sessions", headers=new_h).status_code == 200

        # Old access token session_id was revoked in Redis during refresh!
        revoked_check = client.get("/api/v1/account/preferences", headers=auth_h)
        assert revoked_check.status_code == 401, f"Expected revoked session 401, got {revoked_check.status_code}"

        # 7. Preferences, Privacy, Feature Flags
        pref_upd = client.patch(
            "/api/v1/account/preferences",
            headers=new_h,
            json={"preferred_currency": "SAR", "list_density": "dense"},
        )
        assert pref_upd.status_code == 200 and pref_upd.json()["preferred_currency"] == "SAR"
        flags = client.get("/api/v1/flags")
        assert flags.status_code == 200 and "ai.ambient.proactive_nudges" in flags.json()

        # 8. Profile CRUD + Optimistic Lock + LaTeX CV Parse + Base Template Synthesis
        prof_put = client.put(
            "/api/v1/profiles/me",
            headers=new_h,
            json={
                "personal_info": {
                    "full_name": "Mostafa Ibrahim",
                    "primary_email": email,
                    "contact_numbers": [
                        {"country_code": "EG", "dial_code": "+20", "phone_number": "1004829102", "is_primary": True},
                        {"country_code": "SA", "dial_code": "+966", "phone_number": "551234567", "is_primary": False},
                    ],
                    "links": {"github": "https://github.com/mostafa-ai"},
                },
                "residence_and_mobility": {
                    "current_residence": {"city": "Cairo", "country": "Egypt"},
                    "willing_to_relocate": True,
                    "target_locations": [{"location_id": "loc_1", "city": "Riyadh", "country": "Saudi Arabia", "work_modes": ["Remote", "Hybrid"], "is_active_for_search": True}],
                },
                "education": [{"institution": "Cairo University", "degree": "B.Sc. Computer Engineering", "graduation_year": 2021}],
                "languages": [{"language": "Arabic", "proficiency": "Native"}, {"language": "English", "proficiency": "Fluent"}],
                "career_personas": [
                    {
                        "persona_id": "data_scientist_track",
                        "target_title": "Lead Data Scientist",
                        "alternative_titles": ["ML Engineer"],
                        "is_primary": True,
                        "seniority_level": "Senior",
                        "years_of_experience": 4,
                        "summary_bio": "Production ML & FastAPI pricing systems.",
                        "skills_and_tools": {"core_skills": ["Python", "PyTorch", "SQL", "FastAPI", "Docker"]},
                        "experience_highlights": [{"company": "Swvl", "role": "Senior Data Scientist", "achievements": ["Cut dynamic pricing latency by 42% across 1,400 daily routes"]}],
                        "featured_projects": [{"name": "Dynamic Route Pricer", "tech_stack": ["PyTorch", "FastAPI"], "summary": "Sub-50ms pricing inference."}],
                    }
                ],
            },
        )
        assert prof_put.status_code == 200, prof_put.text
        v = prof_put.json()["version"]
        stale = client.put("/api/v1/profiles/me", headers={**new_h, "If-Match": str(v - 1)}, json=prof_put.json()["profile"])
        assert stale.status_code == 409, f"Expected 409 optimistic lock, got {stale.status_code}"

        tpls = client.get("/api/v1/profiles/me/base-templates", headers=new_h)
        assert tpls.status_code == 200 and "\\documentclass" in tpls.json()[0]["latex_content"]

        parsed = client.post(
            "/api/v1/profiles/parse-latex",
            json={"latex_content": tpls.json()[0]["latex_content"]},
        )
        assert parsed.status_code == 200 and parsed.json()["success"] is True

    print("\nALL PHASE 1 VERIFICATION GATES PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
