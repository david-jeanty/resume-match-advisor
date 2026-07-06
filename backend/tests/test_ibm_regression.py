"""Regression tests for the IBM Salesforce Consulting/GTM quality patch.

Covers: curly-quote normalization, education eligibility strength,
IBM-style section-header filtering, behavioral/soft-attribute matching,
evidence-quote hierarchy (never quote a section header; prefer work and
leadership bullets over skills lists), and honest gaps for user stories /
process flows / solution overviews.
"""

import pytest

from app.jd_parser import parse_jd
from app.models import AnalyzeRequest
from app.report_generator import generate_report


@pytest.fixture
def ibm_report(ibm_jd, btm_gtm_resume):
    return generate_report(
        AnalyzeRequest(resume_text=btm_gtm_resume, job_description_text=ibm_jd)
    )


def _item(report, fragment):
    matches = [e for e in report.evidence_map if fragment.lower() in e.requirement.lower()]
    assert matches, f"no evidence item matching {fragment!r}"
    return matches[0]


class TestEducation:
    def test_bachelors_degree_is_strong(self, ibm_report):
        item = _item(ibm_report, "Bachelor")
        assert item.match_strength == "strong"
        assert "Bachelor of Commerce" in (item.resume_evidence or "")

    def test_currently_enrolled_related_program_is_strong(self, ibm_report):
        item = _item(ibm_report, "Currently enrolled in Business, Commerce")
        assert item.match_strength == "strong"


class TestHeaderFiltering:
    HEADERS = [
        "Required Technical And Professional Expertise",
        "Preferred Technical And Professional Experience",
        "Skills & Experience",
        "What We’re Looking For",
        "Preferred Education",
        "Your Role And Responsibilities",
        "Why This Role?",
        "Introduction",
        "About Business Unit",
    ]

    def test_headers_never_appear_as_evidence_items(self, ibm_report):
        for header in self.HEADERS:
            for item in ibm_report.evidence_map:
                assert item.requirement.strip() != header

    def test_headers_route_buckets_correctly(self, ibm_jd):
        jd = parse_jd(ibm_jd)
        # The degree line under "Required Technical And Professional
        # Expertise" must land in required, not responsibilities.
        assert any("Currently enrolled" in r for r in jd.required)
        # "Preferred Education" content lands in preferred.
        assert any("Bachelor" in p for p in jd.preferred)
        # "Why This Role?" content is ignored entirely.
        all_items = jd.required + jd.preferred + jd.responsibilities
        assert not any("build consulting skills" in i for i in all_items)


class TestSoftAttributes:
    def test_curiosity_analytical_thinking_not_missing(self, ibm_report):
        item = _item(ibm_report, "Curiosity")
        assert item.match_strength in ("strong", "moderate")

    def test_people_first_not_missing(self, ibm_report):
        item = _item(ibm_report, "People-first")
        assert item.match_strength in ("strong", "moderate")

    def test_organization_matched_from_work_bullets(self, ibm_report, btm_gtm_resume):
        item = _item(ibm_report, "Strong organization")
        assert item.match_strength == "strong"
        # Quote must be a real bullet, not the skills list.
        assert item.resume_evidence
        assert "Salesforce certification in progress" not in item.resume_evidence

    def test_clear_communicator_at_least_moderate(self, ibm_report):
        item = _item(ibm_report, "Clear communicator")
        assert item.match_strength in ("strong", "moderate")


class TestEvidenceQuotes:
    def test_leadership_never_quotes_section_header(self, ibm_report):
        item = _item(ibm_report, "leadership experience")
        assert item.match_strength in ("strong", "moderate")
        assert item.resume_evidence
        assert "LEADERSHIP EXPERIENCE & ACTIVITIES" not in item.resume_evidence
        assert (
            "Vice President" in item.resume_evidence
            or "Coordinated communication" in item.resume_evidence
            or "Onboarded 20 members" in item.resume_evidence
        )

    def test_no_evidence_quote_is_a_section_header(self, ibm_report):
        for item in ibm_report.evidence_map:
            if item.resume_evidence:
                quote = item.resume_evidence.rstrip("…")
                assert quote.upper() != quote or not quote.isupper(), (
                    f"section-header-like quote: {item.resume_evidence!r}"
                )

    def test_salesforce_crm_quotes_work_bullet_over_skills_list(self, ibm_report):
        item = _item(ibm_report, "Exposure to Salesforce")
        assert item.match_strength == "strong"
        assert "3,500+ CRM inquiries" in (item.resume_evidence or "")


class TestHonestGaps:
    def test_user_stories_and_process_flows_remain_gaps(self, ibm_report):
        missing = (
            ibm_report.missing_skills.required_missing
            + ibm_report.missing_skills.preferred_missing
            + ibm_report.missing_skills.tools_missing
        )
        assert "user stories" in missing
        assert "process mapping" in missing
        assert "solution overviews" in missing

    def test_user_stories_line_not_strong(self, ibm_report):
        item = _item(ibm_report, "user stories and process flows")
        assert item.match_strength in ("moderate", "weak", "missing")

    def test_education_and_soft_attributes_not_in_missing_skills(self, ibm_report):
        missing = (
            ibm_report.missing_skills.required_missing
            + ibm_report.missing_skills.preferred_missing
        )
        for term in ["communication", "process execution", "problem solving",
                     "stakeholder management", "crm"]:
            assert term not in missing

    def test_score_good_but_not_inflated(self, ibm_report):
        assert 70 <= ibm_report.overall_score <= 88
        required = next(
            b for b in ibm_report.score_breakdown
            if b.category == "required_qualifications"
        )
        assert required.score >= 18
