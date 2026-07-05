from app.jd_parser import parse_jd
from app.matching_engine import build_evidence_map, evidence_for_term, match_skills
from app.models import AnalyzeRequest
from app.report_generator import generate_report
from app.resume_parser import parse_resume


class TestEvidence:
    def test_direct_crm_evidence_is_strong(self, mixed_resume):
        resume = parse_resume(mixed_resume)
        ev = evidence_for_term("crm", resume)
        assert ev.strength == "strong"
        assert ev.line is not None
        assert "hubspot" in ev.line.lower() or "crm" in ev.line.lower()

    def test_club_experience_translates_to_project_management(self, club_resume):
        resume = parse_resume(club_resume)
        ev = evidence_for_term("project management", resume)
        assert ev.strength in ("strong", "moderate")

    def test_missing_tool_is_missing(self, sparse_finance_resume):
        resume = parse_resume(sparse_finance_resume)
        ev = evidence_for_term("power bi", resume)
        assert ev.strength == "missing"

    def test_evidence_map_covers_all_requirements(self, marketing_jd, mixed_resume):
        jd = parse_jd(marketing_jd)
        resume = parse_resume(mixed_resume)
        evidence = build_evidence_map(jd, resume)
        expected = len(jd.required) + len(jd.preferred) + len(jd.responsibilities)
        assert len(evidence) == expected
        assert all(e.explanation for e in evidence)
        # Every strong item must quote actual resume evidence.
        for item in evidence:
            if item.match_strength == "strong":
                assert item.resume_evidence


class TestReport:
    def test_good_match_scores_well(self, marketing_jd, mixed_resume):
        report = generate_report(
            AnalyzeRequest(
                resume_text=mixed_resume, job_description_text=marketing_jd
            )
        )
        assert 60 <= report.overall_score <= 100
        assert report.detected_disciplines[0].discipline_id == "marketing"

    def test_sparse_resume_scores_lower_than_strong_resume(
        self, finance_jd, sparse_finance_resume, mixed_resume
    ):
        sparse = generate_report(
            AnalyzeRequest(
                resume_text=sparse_finance_resume, job_description_text=finance_jd
            )
        )
        strong = generate_report(
            AnalyzeRequest(resume_text=mixed_resume, job_description_text=finance_jd)
        )
        # The sparse resume must not out-score a substantive one.
        assert sparse.overall_score < strong.overall_score
        assert sparse.overall_score < 65

    def test_breakdown_weights_sum_to_100(self, marketing_jd, mixed_resume):
        report = generate_report(
            AnalyzeRequest(
                resume_text=mixed_resume, job_description_text=marketing_jd
            )
        )
        assert sum(item.max_score for item in report.score_breakdown) == 100
        assert sum(item.score for item in report.score_breakdown) >= report.overall_score
        assert all(0 <= i.score <= i.max_score for i in report.score_breakdown)

    def test_missing_tools_are_reported(self, finance_jd, sparse_finance_resume):
        report = generate_report(
            AnalyzeRequest(
                resume_text=sparse_finance_resume, job_description_text=finance_jd
            )
        )
        missing = (
            report.missing_skills.tools_missing
            + report.missing_skills.required_missing
            + report.missing_skills.preferred_missing
        )
        assert "excel" in missing or "power bi" in missing

    def test_suggestions_are_specific(self, finance_jd, sparse_finance_resume):
        report = generate_report(
            AnalyzeRequest(
                resume_text=sparse_finance_resume, job_description_text=finance_jd
            )
        )
        assert report.improvement_suggestions
        # Suggestions must go beyond "improve your resume" — they should
        # reference a concrete skill, place, or action.
        for s in report.improvement_suggestions:
            assert len(s.suggestion) > 60

    def test_student_translation_appears_for_club_resume(self, btm_jd, club_resume):
        report = generate_report(
            AnalyzeRequest(resume_text=club_resume, job_description_text=btm_jd)
        )
        text = " ".join(
            s.suggestion + s.title for s in report.improvement_suggestions
        ) + " ".join(e.explanation for e in report.evidence_map)
        assert (
            "club" in text.lower()
            or "case competition" in text.lower()
            or "transferable" in text.lower()
        )

    def test_no_crash_on_tiny_inputs(self):
        report = generate_report(
            AnalyzeRequest(resume_text="a", job_description_text="b")
        )
        assert 0 <= report.overall_score <= 100

    def test_no_crash_on_messy_inputs(self, mixed_resume):
        messy_jd = "!!!\n\n•• apply now ••\nmust have excel??\n\t\t~~~\n" * 30
        report = generate_report(
            AnalyzeRequest(resume_text=mixed_resume, job_description_text=messy_jd)
        )
        assert 0 <= report.overall_score <= 100
