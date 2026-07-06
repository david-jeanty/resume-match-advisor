"""Default advisor provider: deterministic rules and templates.

No AI, no network, no cost. Cross-references the evidence map, missing
skills, discipline packs, university packs, and location context to produce
richer explanations than the per-item evidence map can — especially
false-gap detection ("you have adjacent evidence, name it explicitly")
versus genuine gaps ("this is real, here's how to close or address it").
"""

from .. import knowledge_loader
from ..matching_engine import evidence_for_term
from ..models import AdvisorNote
from .base import AdvisorInput, AdvisorProvider

MAX_NOTES = 8

# How many adjacent skills must be evidenced before a missing term is
# called a "possible false gap" rather than a plain gap.
ADJACENCY_THRESHOLD = 2

# Industry label (from the company card) -> what to emphasize.
INDUSTRY_EMPHASIS = {
    "Banking / Financial services": "attention to detail, data accuracy, and comfort with regulated, process-driven work",
    "Financial services": "attention to detail, data accuracy, and comfort with regulated, process-driven work",
    "Insurance": "process discipline, documentation, and client-service evidence",
    "Software / Technology": "technical curiosity, cross-functional collaboration, and comfort learning new tools",
    "Technology": "technical curiosity, cross-functional collaboration, and comfort learning new tools",
    "Consulting / Professional services": "structured problem solving, client-ready communication, and deliverables",
    "Accounting / Professional services": "accuracy, working papers, and CPA-track signals",
    "Retail": "operations under volume, customer insight, and inventory/process evidence",
    "E-commerce": "conversion, analytics, and campaign evidence",
    "Grocery / Retail": "operations under volume and process reliability",
    "Telecommunications": "B2B context, process discipline, and customer operations",
    "Healthcare": "process reliability, documentation, and stakeholder sensitivity",
    "Non-profit": "resourcefulness, fundraising/sponsorship, and community outcomes",
}


class RuleBasedProvider(AdvisorProvider):
    name = "rule_based"

    def advise(self, data: AdvisorInput) -> list[AdvisorNote]:
        notes: list[AdvisorNote] = []
        notes += self._gap_notes(data)
        note = self._positioning_note(data)
        if note:
            notes.append(note)
        note = self._translation_note(data)
        if note:
            notes.append(note)
        notes += self._role_suggestion_notes(data, notes)
        note = self._course_context_note(data)
        if note:
            notes.append(note)
        note = self._location_note(data)
        if note:
            notes.append(note)
        note = self._company_note(data)
        if note:
            notes.append(note)
        return notes[:MAX_NOTES]

    # ---------------------------------------------- gaps and false gaps

    def _adjacent_hits(self, data: AdvisorInput, adjacent: list[str]) -> list[str]:
        hits = []
        for term in adjacent:
            ev = evidence_for_term(term, data.resume)
            if ev.strength in ("strong", "moderate") and ev.origin in ("resume", "translation"):
                hits.append(term)
        return hits

    def _gap_notes(self, data: AdvisorInput) -> list[AdvisorNote]:
        adjacency_map = knowledge_loader.get_common().get("adjacent_evidence", {})
        missing_terms = (
            data.missing_skills.required_missing
            + data.missing_skills.tools_missing
            + data.missing_skills.preferred_missing
        )
        false_gaps: list[AdvisorNote] = []
        real_gaps: list[AdvisorNote] = []
        for term in missing_terms:
            entry = adjacency_map.get(term)
            hits = self._adjacent_hits(data, entry["adjacent"]) if entry else []
            if entry and len(hits) >= ADJACENCY_THRESHOLD:
                false_gaps.append(AdvisorNote(
                    category="false_gap",
                    title=f"{term}: possibly a wording gap, not an experience gap",
                    message=(
                        f"The posting asks for {term}, and your resume already shows "
                        f"related evidence ({', '.join(hits[:3])}). {entry['advice']}"
                    ),
                    related_terms=[term] + hits[:3],
                ))
            else:
                advice = entry["advice"] if entry else (
                    f"Nothing in your resume relates to {term} yet. If you genuinely "
                    "have this experience, add it with context; if not, treat it as a "
                    "skill to build or a point to address honestly in a cover letter."
                )
                real_gaps.append(AdvisorNote(
                    category="gap_explanation",
                    title=f"{term}: a genuine gap to address",
                    message=advice,
                    related_terms=[term],
                ))
        return false_gaps[:3] + real_gaps[:2]

    # ------------------------------------------------------ positioning

    def _positioning_note(self, data: AdvisorInput) -> AdvisorNote | None:
        strongest = [
            m for m in data.skill_matches
            if m.status in ("direct", "alias") and m.evidence_line
        ]
        if len(strongest) < 2 or not data.disciplines:
            return None
        top_terms = [m.term for m in strongest[:3]]
        discipline = data.disciplines[0].discipline
        return AdvisorNote(
            category="positioning",
            title="Lead with your strongest proof",
            message=(
                f"For this {discipline} role, your most convincing evidence is "
                f"{', '.join(top_terms)}. Put the bullets that show these at the top "
                "of their sections, and mirror the posting's wording for them where "
                "it's honest — recruiters skim, so your best proof should be first."
            ),
            related_terms=top_terms,
        )

    # ----------------------------------------- student experience translation

    def _translation_note(self, data: AdvisorInput) -> AdvisorNote | None:
        translated = [m for m in data.skill_matches if m.status in ("translated", "context")]
        if not translated:
            return None
        by_source: dict[str, list[str]] = {}
        for m in translated:
            by_source.setdefault(m.matched_via or "student experience", []).append(m.term)
        source, terms = max(by_source.items(), key=lambda kv: len(kv[1]))
        return AdvisorNote(
            category="experience_translation",
            title="Experience you already have — just not in these words",
            message=(
                f"Your {source} plausibly covers {', '.join(sorted(set(terms))[:4])}, "
                "but the resume never says so. This is a wording fix, not a new "
                "experience requirement: rewrite those bullets to name the skill, the "
                "stakeholders, and the outcome the posting is asking about."
            ),
            related_terms=sorted(set(terms))[:4],
        )

    # ------------------------------------------------- role-specific advice

    def _role_suggestion_notes(
        self, data: AdvisorInput, existing: list[AdvisorNote]
    ) -> list[AdvisorNote]:
        if not data.disciplines:
            return []
        pack = knowledge_loader.get_pack(data.disciplines[0].discipline_id) or {}
        covered = {t for n in existing for t in n.related_terms}
        notes = []
        for angle in pack.get("improvement_angles", []):
            mentioned = [
                t for t in data.missing_skills.required_missing
                + data.missing_skills.tools_missing
                if t in angle.lower() and t not in covered
            ]
            if mentioned:
                notes.append(AdvisorNote(
                    category="role_suggestion",
                    title=f"{data.disciplines[0].discipline}: close the {mentioned[0]} gap",
                    message=angle,
                    related_terms=mentioned,
                ))
            if len(notes) >= 2:
                break
        return notes

    # --------------------------------------------------- context and company

    def _course_context_note(self, data: AdvisorInput) -> AdvisorNote | None:
        if not data.university_context:
            return None
        # Terms whose only evidence is course context show up as "context"
        # skill matches — exactly the "coursework may cover this, but the
        # resume doesn't show it applied" situation.
        for course in data.university_context.detected_courses:
            covered = sorted(
                m.term for m in data.skill_matches
                if m.status == "context"
                and m.matched_via
                and course.code in m.matched_via
            )
            if covered:
                return AdvisorNote(
                    category="context_advice",
                    title=f"Your {course.code} coursework may cover a flagged gap",
                    message=(
                        f"The posting asks for {', '.join(covered[:3])}, which "
                        f"{course.code} ({course.name}) typically touches. A course "
                        "name alone is weak evidence — add the specific project, "
                        "tool, or deliverable from that course if you have one."
                    ),
                    related_terms=covered[:3] + [course.code],
                )
        return None

    def _location_note(self, data: AdvisorInput) -> AdvisorNote | None:
        if not data.location_context or not data.location_context.positioning_advice:
            return None
        return AdvisorNote(
            category="context_advice",
            title=f"Positioning for {data.location_context.location_name}",
            message=data.location_context.positioning_advice[0],
            related_terms=[],
        )

    def _company_note(self, data: AdvisorInput) -> AdvisorNote | None:
        card = data.company_card
        if not card:
            return None
        emphasis = INDUSTRY_EMPHASIS.get(card.industry or "")
        if not emphasis:
            return None
        return AdvisorNote(
            category="company_angle",
            title=f"Tailoring for {card.company_name}",
            message=(
                f"{card.company_name} operates in {card.industry}. For employers like "
                f"this, emphasize {emphasis} — pick the one or two bullets that show "
                "this best and make sure they survive any resume trimming."
            ),
            related_terms=[],
        )
