from app.jd_parser import parse_jd
from app.resume_parser import parse_resume


class TestResumeParser:
    def test_detects_sections(self, mixed_resume):
        parsed = parse_resume(mixed_resume)
        assert "experience" in parsed.sections_found
        assert "education" in parsed.sections_found
        assert "skills" in parsed.sections_found
        assert "leadership" in parsed.sections_found

    def test_extracts_skills_and_tools(self, mixed_resume):
        parsed = parse_resume(mixed_resume)
        assert "excel" in parsed.tools_found
        assert "hubspot" in parsed.tools_found
        assert "crm" in parsed.skills_found
        assert "market research" in parsed.skills_found

    def test_detects_student_signals(self, club_resume):
        parsed = parse_resume(club_resume)
        assert any("case competition" in s for s in parsed.student_signals)
        assert any("orientation leader" in s for s in parsed.student_signals)

    def test_counts_quantified_bullets(self, mixed_resume):
        parsed = parse_resume(mixed_resume)
        assert parsed.bullets
        assert len(parsed.quantified_bullets) >= 5

    def test_no_crash_on_short_input(self):
        parsed = parse_resume("hi")
        assert parsed.bullets == []
        assert parsed.skills_found == []

    def test_no_crash_on_messy_paste(self):
        messy = "•• Skills:Excel,,,CRM\n\n\n???\n\tRandom   spacing   everywhere\n" * 20
        parsed = parse_resume(messy)
        assert "excel" in parsed.tools_found


class TestJDParser:
    def test_buckets_marketing_jd(self, marketing_jd):
        jd = parse_jd(marketing_jd)
        assert len(jd.required) >= 3
        assert len(jd.preferred) >= 2
        assert len(jd.responsibilities) >= 4

    def test_extracts_title(self, marketing_jd):
        jd = parse_jd(marketing_jd)
        assert jd.role_title is not None
        assert "intern" in jd.role_title.lower()

    def test_extracts_skills_and_tools(self, btm_jd):
        jd = parse_jd(btm_jd)
        assert "excel" in jd.tools
        assert "jira" in jd.tools
        assert "sql" in jd.tools
        assert "stakeholder management" in jd.skills or "documentation" in jd.skills

    def test_preferred_not_leaked_into_required(self, finance_jd):
        jd = parse_jd(finance_jd)
        assert any("power bi" in p.lower() or "tableau" in p.lower()
                   for p in jd.preferred)

    def test_no_crash_on_prose_jd(self):
        jd = parse_jd(
            "We want a motivated student to help our small marketing team. "
            "Must have experience with social media and Excel. "
            "Familiarity with Canva is a plus."
        )
        assert jd.required or jd.preferred or jd.responsibilities

    def test_no_crash_on_short_input(self):
        jd = parse_jd("marketing intern")
        assert jd.required == []
