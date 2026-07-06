"""Regression tests for the CIBC co-op posting quality patch.

Covers: application-logistics/section-header filtering, education-field
matching, expanded data/process/testing/collaboration alias groups, soft
corporate-values filtering, and score calibration (materially better than
the pre-patch 34/100, but not inflated into a strong match).
"""

from app.jd_parser import parse_jd
from app.models import AnalyzeRequest
from app.report_generator import generate_report


class TestLogisticsAndHeaderFiltering:
    def test_logistics_lines_are_dropped(self, cibc_jd):
        jd = parse_jd(cibc_jd)
        all_text = " ".join(jd.required + jd.preferred + jd.responsibilities).lower()
        for phrase in [
            "recruitment timeline", "duration of term", "multiple positions available",
            "unofficial transcript", "cover letters are optional",
            "no more than one page", "competitive compensation",
        ]:
            assert phrase not in all_text

    def test_ignore_section_headers_dont_leak_as_items(self, cibc_jd):
        jd = parse_jd(cibc_jd)
        all_items = jd.required + jd.preferred + jd.responsibilities
        for header in ["Important information", "What CIBC Offers", "Application instructions"]:
            assert header not in all_items

    def test_how_youll_succeed_header_is_not_an_item(self, cibc_jd):
        jd = parse_jd(cibc_jd)
        all_items = jd.required + jd.preferred + jd.responsibilities
        assert "How You'll Succeed" not in all_items
        assert "Who You Are" not in all_items

    def test_offer_boilerplate_not_in_required(self, cibc_jd):
        jd = parse_jd(cibc_jd)
        required_text = " ".join(jd.required).lower()
        for phrase in ["hybrid work environment", "build your network", "inclusive team culture"]:
            assert phrase not in required_text


class TestSoftValueFiltering:
    def test_soft_values_are_not_hard_requirements(self, cibc_jd):
        jd = parse_jd(cibc_jd)
        all_text = " ".join(jd.required + jd.preferred + jd.responsibilities).lower()
        for phrase in [
            "values matter", "you love to learn", "you bring your real self",
            "live our values", "you give meaning to data",
        ]:
            assert phrase not in all_text

    def test_required_bucket_is_not_dominated_by_soft_lines(self, cibc_jd):
        jd = parse_jd(cibc_jd)
        # Only the two genuinely hard lines from "Who You Are" should survive:
        # the degree/enrollment requirement and the Capital Markets/regulatory
        # reporting line (it names real vocabulary terms).
        assert len(jd.required) == 2


class TestEducationMatching:
    def test_bcom_btm_satisfies_degree_requirement(self, cibc_jd, btm_data_resume):
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        degree_items = [
            e for e in report.evidence_map if "degree in Business" in e.requirement
        ]
        assert degree_items
        assert degree_items[0].match_strength == "strong"
        assert "Bachelor of Commerce" in (degree_items[0].resume_evidence or "")

    def test_enrollment_not_satisfied_by_intern_alone(self, cibc_jd):
        bare_resume = (
            "Sam Student\nExperience\nMarketing Intern — Acme Co\n"
            "- Supported campaigns and reporting\n"
        )
        report = generate_report(
            AnalyzeRequest(resume_text=bare_resume, job_description_text=cibc_jd)
        )
        degree_items = [
            e for e in report.evidence_map if "degree in Business" in e.requirement
        ]
        assert degree_items
        assert degree_items[0].match_strength == "missing"

    def test_education_field_without_dates_is_moderate_not_strong(self, cibc_jd):
        resume = (
            "Sam Student\nEducation\nBachelor of Commerce, Finance\nTelfer School of Management\n"
            "Experience\nCashier — Metro\n- Handled cash and customer service\n"
        )
        report = generate_report(
            AnalyzeRequest(resume_text=resume, job_description_text=cibc_jd)
        )
        degree_items = [
            e for e in report.evidence_map if "degree in Business" in e.requirement
        ]
        assert degree_items[0].match_strength == "moderate"


class TestExpandedAliasGroups:
    def test_excel_pivot_lookup_conditional_formatting_match_excel(self, btm_data_resume):
        from app.matching_engine import evidence_for_term
        from app.resume_parser import parse_resume

        resume = parse_resume(btm_data_resume)
        ev = evidence_for_term("excel", resume)
        assert ev.strength == "strong"

    def test_data_accuracy_and_anomalies_match_data_quality(self, btm_data_resume):
        from app.matching_engine import evidence_for_term
        from app.resume_parser import parse_resume

        resume = parse_resume(btm_data_resume)
        ev = evidence_for_term("data quality", resume)
        assert ev.strength == "strong"

    def test_audited_matches_data_investigation(self, btm_data_resume):
        from app.matching_engine import evidence_for_term
        from app.resume_parser import parse_resume

        resume = parse_resume(btm_data_resume)
        ev = evidence_for_term("data investigation", resume)
        assert ev.strength == "strong"

    def test_stakeholder_followup_crm_point_of_contact_match_client_service(self, btm_data_resume):
        from app.matching_engine import evidence_for_term
        from app.resume_parser import parse_resume

        resume = parse_resume(btm_data_resume)
        ev = evidence_for_term("client service", resume)
        assert ev.strength == "strong"


class TestRemainingGapsAndScore:
    def test_uat_agile_scrum_capital_markets_remain_gaps(self, cibc_jd, btm_data_resume):
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        missing = (
            report.missing_skills.required_missing
            + report.missing_skills.preferred_missing
            + report.missing_skills.tools_missing
        )
        for term in ["uat", "testing", "agile", "scrum", "capital markets", "regulatory reporting"]:
            assert term in missing, f"expected {term} to remain a gap"

    def test_score_is_materially_better_than_pre_patch_but_not_inflated(
        self, cibc_jd, btm_data_resume
    ):
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        assert 50 <= report.overall_score <= 72
        assert report.overall_score > 34 + 15

    def test_evidence_map_is_clean(self, cibc_jd, btm_data_resume):
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        # No logistics/offer/header noise should reach the evidence map.
        for item in report.evidence_map:
            lowered = item.requirement.lower()
            assert "transcript" not in lowered
            assert "cover letter" not in lowered
            assert "what cibc offers" not in lowered
            assert "important information" not in lowered
        assert len(report.evidence_map) <= 16

    def test_required_score_is_not_zero(self, cibc_jd, btm_data_resume):
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        required_breakdown = next(
            b for b in report.score_breakdown if b.category == "required_qualifications"
        )
        assert required_breakdown.score > 0
