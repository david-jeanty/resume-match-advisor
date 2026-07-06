"""Advisor engine provider interface.

The advisor engine runs AFTER the deterministic scan (parse -> match ->
score) and produces additional student-friendly notes. It is an
explanation layer only:

  * It never changes the score or the evidence map.
  * The default provider is rule-based and makes no external calls.
  * LLM-backed providers are optional stubs, disabled by default — the
    base product must always work fully without them.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..jd_parser import ParsedJD
from ..matching_engine import SkillMatch
from ..models import (
    AdvisorNote,
    AnalyzeRequest,
    CompanyCard,
    DisciplineFit,
    EvidenceItem,
    LocationContext,
    MissingSkills,
    UniversityContext,
)
from ..resume_parser import ParsedResume


@dataclass
class AdvisorInput:
    """Everything the deterministic pipeline learned, read-only."""

    request: AnalyzeRequest
    resume: ParsedResume
    jd: ParsedJD
    disciplines: list[DisciplineFit]
    evidence_map: list[EvidenceItem]
    skill_matches: list[SkillMatch]
    missing_skills: MissingSkills
    university_context: Optional[UniversityContext]
    university_pack: Optional[dict]
    location_context: Optional[LocationContext]
    company_card: Optional[CompanyCard]
    overall_score: int


class AdvisorProvider(ABC):
    """A provider turns scan results into advisor notes.

    Implementations must be side-effect free with respect to the scan:
    they receive results and return notes, nothing else.
    """

    name: str = "base"

    @abstractmethod
    def advise(self, data: AdvisorInput) -> list[AdvisorNote]:
        """Return advisor notes. Must not mutate anything in `data`."""
