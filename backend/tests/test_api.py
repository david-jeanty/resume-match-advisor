from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_full_response(mixed_resume, marketing_jd):
    response = client.post(
        "/analyze",
        json={
            "resume_text": mixed_resume,
            "job_description_text": marketing_jd,
            "company_name": "Brightpath Software",
        },
    )
    assert response.status_code == 200
    data = response.json()
    for key in (
        "overall_score", "score_interpretation", "score_breakdown",
        "detected_disciplines", "extracted_job_requirements",
        "extracted_resume_signals", "evidence_map", "missing_skills",
        "weak_areas", "improvement_suggestions", "company_card", "privacy_note",
    ):
        assert key in data
    assert isinstance(data["overall_score"], int)
    assert "not stored" in data["privacy_note"]
    # COMPANY_LOOKUP=off in tests, so the card must be the offline fallback.
    assert data["company_card"]["source"] == "fallback"
    assert data["company_card"]["company_name"] == "Brightpath Software"


def test_analyze_without_company(club_resume, btm_jd):
    response = client.post(
        "/analyze",
        json={"resume_text": club_resume, "job_description_text": btm_jd},
    )
    assert response.status_code == 200
    assert response.json()["company_card"] is None


def test_analyze_rejects_empty_resume(marketing_jd):
    response = client.post(
        "/analyze",
        json={"resume_text": "", "job_description_text": marketing_jd},
    )
    assert response.status_code == 422


def test_analyze_with_target_discipline(mixed_resume, marketing_jd):
    response = client.post(
        "/analyze",
        json={
            "resume_text": mixed_resume,
            "job_description_text": marketing_jd,
            "target_discipline": "sales_revops",
        },
    )
    assert response.status_code == 200
    assert response.json()["detected_disciplines"][0]["discipline_id"] == "sales_revops"
