"""Tests for the optional advisor engine.

Proves: the base scanner works without any advisor, the rule-based default
adds notes without external calls, LLM providers are opt-in stubs that are
never used by default, and the advisor cannot change the score.
"""

import socket

import pytest

from app.advisor_engine import get_advisor
from app.advisor_engine.optional_llm_provider import OptionalLLMProvider
from app.advisor_engine.rule_based_provider import RuleBasedProvider
from app.models import AnalyzeRequest
from app.report_generator import generate_report

UAT_JD = """QA Co-op Student
DataCorp — Ottawa, ON

Responsibilities
- Support user acceptance testing (UAT) for our reporting platform
- Document test results and coordinate fixes with the development team

Requirements
- Currently enrolled in a business or technology program
- Experience with Excel and data validation
"""

VALIDATION_RESUME = """Jo Chen
Ottawa, ON

Education
Bachelor of Commerce, Business Technology Management — Expected 2027

Experience
Operations Assistant — RetailCo (May 2025 - Present)
- Audited weekly reports in Excel to verify data accuracy and flag anomalies for 12 store locations
- Performed data validation and exception identification on 500+ records per week, documenting quality checks for managers
"""

GTM_JD = """Consulting & GTM Intern
AdviseCo — Toronto, ON

Responsibilities
- Support go-to-market and sales operations activities
- Prepare research and preparation materials for client pursuits

Requirements
- Currently enrolled in a business program
- Interest in consulting and GTM strategy
"""

GTM_ADJACENT_RESUME = """Sam Roy
Toronto, ON

Education
Bachelor of Commerce — Expected 2027

Experience
Operations Intern — BrightCo (May 2025 - Aug 2025)
- Prepared structured reporting summaries for stakeholders across multiple workstreams
- Maintained CRM records and coordinated stakeholder follow-up with internal teams
- Served as primary point of contact for client service questions in a high-volume environment
"""


class TestProviderSelection:
    def test_default_is_rule_based(self, monkeypatch):
        monkeypatch.delenv("ADVISOR_PROVIDER", raising=False)
        advisor = get_advisor()
        assert isinstance(advisor, RuleBasedProvider)
        assert advisor.name == "rule_based"

    def test_off_disables_advisor(self, monkeypatch):
        monkeypatch.setenv("ADVISOR_PROVIDER", "off")
        assert get_advisor() is None

    def test_llm_provider_is_optin_stub(self, monkeypatch):
        monkeypatch.setenv("ADVISOR_PROVIDER", "anthropic")
        advisor = get_advisor()
        assert isinstance(advisor, OptionalLLMProvider)
        with pytest.raises(RuntimeError, match="optional placeholder"):
            advisor.advise(None)  # type: ignore[arg-type]

    def test_unknown_value_falls_back_to_rule_based(self, monkeypatch):
        monkeypatch.setenv("ADVISOR_PROVIDER", "definitely-not-a-provider")
        assert isinstance(get_advisor(), RuleBasedProvider)


class TestScannerIndependence:
    def test_scanner_works_with_advisor_off(self, monkeypatch, btm_data_resume, cibc_jd):
        monkeypatch.setenv("ADVISOR_PROVIDER", "off")
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        assert 0 <= report.overall_score <= 100
        assert report.advisor_notes == []
        assert report.advisor_provider == "off"
        assert report.evidence_map  # the scan itself is unaffected

    def test_advisor_never_changes_score(self, monkeypatch, btm_data_resume, cibc_jd):
        request = AnalyzeRequest(
            resume_text=btm_data_resume, job_description_text=cibc_jd
        )
        monkeypatch.setenv("ADVISOR_PROVIDER", "off")
        without = generate_report(request)
        monkeypatch.setenv("ADVISOR_PROVIDER", "rule_based")
        with_advisor = generate_report(request)
        assert with_advisor.overall_score == without.overall_score
        assert [b.score for b in with_advisor.score_breakdown] == [
            b.score for b in without.score_breakdown
        ]
        assert with_advisor.advisor_notes  # but it did add notes

    def test_no_network_access_needed(self, monkeypatch, btm_data_resume, cibc_jd):
        def _no_network(*args, **kwargs):
            raise AssertionError("network access attempted during scan")

        monkeypatch.setattr(socket, "getaddrinfo", _no_network)
        monkeypatch.setattr(socket.socket, "connect", _no_network)
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        assert report.advisor_provider == "rule_based"
        assert report.advisor_notes

    def test_advisor_failure_never_breaks_scan(self, monkeypatch, btm_data_resume, cibc_jd):
        # Explicitly selecting the LLM stub raises inside advise(); the scan
        # must still succeed with empty notes.
        monkeypatch.setenv("ADVISOR_PROVIDER", "anthropic")
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        assert 0 <= report.overall_score <= 100
        assert report.advisor_notes == []


class TestRuleBasedQuality:
    def test_uat_false_gap_detected(self):
        report = generate_report(
            AnalyzeRequest(resume_text=VALIDATION_RESUME, job_description_text=UAT_JD)
        )
        uat_notes = [
            n for n in report.advisor_notes
            if n.category == "false_gap" and ("uat" in n.related_terms or "testing" in n.related_terms)
        ]
        assert uat_notes, "expected a false-gap note for UAT/testing"
        assert "adjacent" in uat_notes[0].message.lower()
        # And UAT must still be listed as a gap — adjacency is advice, not credit.
        missing = (
            report.missing_skills.required_missing
            + report.missing_skills.preferred_missing
        )
        assert "uat" in missing or "testing" in missing

    def test_consulting_gtm_false_gap_detected(self):
        report = generate_report(
            AnalyzeRequest(resume_text=GTM_ADJACENT_RESUME, job_description_text=GTM_JD)
        )
        gtm_notes = [
            n for n in report.advisor_notes
            if n.category == "false_gap" and "sales operations" in n.related_terms
        ]
        assert gtm_notes
        assert "consulting or gtm language" in gtm_notes[0].message.lower()

    def test_advisor_adds_notes_beyond_suggestions(self, btm_data_resume, cibc_jd):
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        assert len(report.advisor_notes) >= 3
        categories = {n.category for n in report.advisor_notes}
        assert "false_gap" in categories
        assert "positioning" in categories or "experience_translation" in categories

    def test_genuine_gaps_stay_honest(self, btm_data_resume, cibc_jd):
        report = generate_report(
            AnalyzeRequest(resume_text=btm_data_resume, job_description_text=cibc_jd)
        )
        # Capital markets has no adjacent evidence in this resume — the
        # advisor must call it a genuine gap, not explain it away.
        genuine = [n for n in report.advisor_notes if n.category == "gap_explanation"]
        assert any("capital markets" in n.related_terms for n in genuine)

    def test_course_context_note_when_course_covers_gap(self, cibc_jd):
        resume = (
            "Jo Student\n\nEducation\n"
            "Bachelor of Commerce, Telfer School of Management, uOttawa — Expected 2028\n"
            "Relevant coursework: ADM 3379\n\n"
            "Experience\nCashier — Metro (2024 - Present)\n"
            "- Served customers and handled cash in a fast-paced store\n"
        )
        report = generate_report(
            AnalyzeRequest(resume_text=resume, job_description_text=cibc_jd)
        )
        course_notes = [
            n for n in report.advisor_notes
            if n.category == "context_advice" and "ADM 3379" in n.related_terms
        ]
        assert course_notes
        assert "weak evidence" in course_notes[0].message
