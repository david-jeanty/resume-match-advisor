from pathlib import Path

from app import context_engine
from app.jd_parser import parse_jd
from app.models import AnalyzeRequest
from app.report_generator import generate_report
from app.resume_parser import parse_resume

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
TELFER_RESUME = (EXAMPLES / "sample_resumes/telfer_btm_student.txt").read_text(
    encoding="utf-8"
)


def _uottawa_pack():
    from app.knowledge_loader import get_universities

    return get_universities()["uottawa_telfer"]


def _detect(resume_text: str, completed_courses=None):
    resume = parse_resume(resume_text)
    return context_engine.detect_courses(_uottawa_pack(), resume, completed_courses)


class TestCourseDetection:
    def test_detects_adm_codes_in_resume_text(self):
        courses = _detect(TELFER_RESUME)
        codes = {c.code for c in courses}
        assert {"ADM 1370", "ADM 2372", "ADM 2302", "ADM 2381"} <= codes

    def test_detects_courses_from_provided_list(self):
        courses = _detect("A short resume with no course codes.",
                          completed_courses="ADM 1370, ADM 2320")
        assert {c.code for c in courses} == {"ADM 1370", "ADM 2320"}

    def test_french_equivalent_maps_to_same_course(self):
        courses = _detect("Cours pertinents: ADM 1770, ADM 2772")
        assert {c.code for c in courses} == {"ADM 1370", "ADM 2372"}

    def test_adm1370_maps_to_business_it_skills(self):
        (course,) = _detect("Completed ADM 1370.")
        assert "excel" in course.related_skills
        assert "dashboards" in course.related_skills
        assert "btm_mis" in course.disciplines

    def test_adm2372_maps_to_mis(self):
        (course,) = _detect("Completed ADM 2372.")
        assert "business analysis" in course.related_skills
        assert course.disciplines == ["btm_mis"]

    def test_adm2302_maps_to_business_analytics(self):
        (course,) = _detect("Completed ADM 2302.")
        assert "data analysis" in course.related_skills
        assert "business_analytics" in course.disciplines

    def test_adm2320_maps_to_marketing(self):
        (course,) = _detect("Completed ADM 2320.")
        assert "market research" in course.related_skills
        assert course.disciplines == ["marketing"]

    def test_finance_accounting_courses_map_correctly(self):
        courses = {c.code: c for c in _detect("Took ADM 1340, ADM 2341, ADM 2350.")}
        assert "accounting" in courses["ADM 1340"].disciplines
        assert "budgeting" in courses["ADM 2341"].related_skills
        assert "financial modeling" in courses["ADM 2350"].related_skills

    def test_course_only_is_weak(self):
        (course,) = _detect(
            "Education\nBCom at Telfer, uOttawa\nRelevant coursework: ADM 2372"
        )
        assert course.strength == "weak"
        assert "not enough evidence" in course.note or "weak" in course.note.lower()

    def test_course_plus_applied_work_is_stronger(self):
        resume = (
            "Education\nBCom, uOttawa — ADM 2372\n"
            "Projects\n"
            "- Documented business requirements and built a process map in Visio "
            "for a 10-store retail case, presenting to 3 stakeholders"
        )
        (course,) = _detect(resume)
        assert course.strength in ("moderate", "strong")


class TestScoreInflationGuards:
    JD = (EXAMPLES / "sample_job_descriptions/business_analyst_btm.txt").read_text(
        encoding="utf-8"
    )
    BARE_RESUME = (
        "Sam Student\nOttawa, ON\n\nEducation\n"
        "Bachelor of Commerce, Telfer School of Management, University of Ottawa\n\n"
        "Work Experience\n"
        "Cashier — Metro, Ottawa (2024 - Present)\n"
        "- Served customers and handled cash in a fast-paced grocery store\n"
    )

    def test_course_codes_do_not_inflate_score(self):
        without = generate_report(
            AnalyzeRequest(resume_text=self.BARE_RESUME, job_description_text=self.JD)
        )
        with_courses = generate_report(
            AnalyzeRequest(
                resume_text=self.BARE_RESUME,
                job_description_text=self.JD,
                completed_courses="ADM 1370, ADM 2372, ADM 2302, ADM 2320, ADM 2350",
            )
        )
        assert with_courses.overall_score - without.overall_score <= 8
        assert with_courses.overall_score < 65

    def test_club_membership_alone_does_not_inflate_score(self):
        member_resume = self.BARE_RESUME + (
            "\nInvolvement\nMember — Telfer Business Technology Association (BTA)\n"
        )
        without = generate_report(
            AnalyzeRequest(resume_text=self.BARE_RESUME, job_description_text=self.JD)
        )
        with_club = generate_report(
            AnalyzeRequest(resume_text=member_resume, job_description_text=self.JD)
        )
        assert with_club.overall_score - without.overall_score <= 8

    def test_location_context_does_not_change_score(self):
        base = generate_report(
            AnalyzeRequest(resume_text=self.BARE_RESUME, job_description_text=self.JD)
        )
        located = generate_report(
            AnalyzeRequest(
                resume_text=self.BARE_RESUME,
                job_description_text=self.JD,
                location="Kanata",
            )
        )
        assert located.overall_score == base.overall_score
        assert located.location_context is not None


class TestClubDetection:
    def _clubs(self, resume_text: str):
        resume = parse_resume(resume_text)
        return {c.name: c for c in context_engine.detect_clubs(_uottawa_pack(), resume)}

    def test_detects_tcct_ticc_jdc(self):
        clubs = self._clubs(
            "Involvement\n"
            "Delegate — Telfer Competitions Committee (TCCT)\n"
            "Competed at JDC and the Telfer Internal Case Competition (TICC)\n"
        )
        names = " ".join(clubs)
        assert "TCCT" in names
        assert any("JDC" in n or "Jeux" in n for n in clubs)
        assert any("TICC" in n for n in clubs)

    def test_bta_maps_to_btm_and_analytics(self):
        clubs = self._clubs("Member of the Business Technology Association at Telfer")
        (bta,) = clubs.values()
        assert "btm_mis" in bta.disciplines
        assert "business_analytics" in bta.disciplines
        assert bta.strength == "weak"  # membership only

    def test_tma_maps_to_marketing(self):
        clubs = self._clubs("Member — Telfer Marketing Association")
        (tma,) = clubs.values()
        assert tma.disciplines == ["marketing"]

    def test_tfs_and_tac_map_to_finance_accounting(self):
        clubs = self._clubs(
            "Involvement\nTelfer Finance Society workshops\nTelfer Accounting Club events"
        )
        disciplines = {d for c in clubs.values() for d in c.disciplines}
        assert "finance" in disciplines
        assert "accounting" in disciplines

    def test_aetsa_vp_role_is_moderate_or_better(self):
        clubs = self._clubs(
            "Leadership\nVP Internal — Telfer Students' Association (AÉTSA)\n"
            "- Coordinated between 15 clubs and the school administration"
        )
        (aetsa,) = clubs.values()
        assert aetsa.strength in ("moderate", "strong")
        assert "leadership" in aetsa.supports or "stakeholder management" in aetsa.supports

    def test_leadership_with_outcomes_is_strong(self):
        clubs = self._clubs(
            "VP Events — Telfer Marketing Association\n"
            "- Organized 6 events with 100+ attendees and secured $3,000 in sponsorship"
        )
        (tma,) = clubs.values()
        assert tma.strength == "strong"


class TestLocationContext:
    def test_detects_ottawa_from_jd(self):
        jd = parse_jd("Marketing Intern\nBrightpath, Kanata North, ON\nMust have Excel.")
        request = AnalyzeRequest(resume_text="x", job_description_text="y")
        pack, source = context_engine.resolve_location(request, jd)
        assert pack["id"] == "ottawa_kanata"
        assert source == "job_description"

    def test_tech_jd_gets_b2b_tech_angle(self):
        jd = parse_jd(
            "Marketing Intern — SaaS company in Kanata\n"
            "Responsibilities\n- Support B2B campaigns for our cybersecurity software"
        )
        request = AnalyzeRequest(resume_text="x", job_description_text="y", location="Ottawa")
        context, _ = context_engine.build_location_context(request, jd)
        assert any("B2B technology" in a for a in context.positioning_advice)

    def test_unknown_location_falls_back_to_generic(self):
        jd = parse_jd("Analyst role. Excel required.")
        request = AnalyzeRequest(
            resume_text="x", job_description_text="y", location="Whitehorse"
        )
        pack, _ = context_engine.resolve_location(request, jd)
        assert pack["id"] == "generic_canada"


class TestContextInReport:
    def test_telfer_resume_gets_context_sections(self):
        report = generate_report(
            AnalyzeRequest(
                resume_text=TELFER_RESUME,
                job_description_text=(
                    EXAMPLES / "sample_job_descriptions/business_analyst_btm.txt"
                ).read_text(encoding="utf-8"),
            )
        )
        section_ids = {s.section_id for s in report.contextual_feedback}
        assert "university_program" in section_ids
        assert "school_involvement" in section_ids
        assert report.university_context is not None
        assert report.university_context.coop_detected
        assert report.university_context.bilingual_detected

    def test_no_context_sections_without_context(self, mixed_resume, marketing_jd):
        report = generate_report(
            AnalyzeRequest(resume_text=mixed_resume, job_description_text=marketing_jd)
        )
        assert report.university_context is None
        section_ids = {s.section_id for s in report.contextual_feedback}
        assert "university_program" not in section_ids
        assert "school_involvement" not in section_ids

    def test_context_evidence_surfaces_in_suggestions(self):
        jd = (EXAMPLES / "sample_job_descriptions/business_analyst_btm.txt").read_text(
            encoding="utf-8"
        )
        bare_telfer = (
            "Sam Student\nEducation\nBCom, Telfer School of Management, uOttawa\n"
            "Relevant coursework: ADM 2372\n"
            "Experience\nCashier — Metro, Ottawa\n- Served customers in a busy store\n"
        )
        report = generate_report(
            AnalyzeRequest(resume_text=bare_telfer, job_description_text=jd)
        )
        text = " ".join(
            s.title + " " + s.suggestion for s in report.improvement_suggestions
        ) + " ".join(e.explanation for e in report.evidence_map)
        assert "ADM 2372" in text
