"""Pydantic models for the Resume Match Advisor API."""

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

MatchStrength = Literal["strong", "moderate", "weak", "missing"]
RequirementType = Literal["required", "preferred", "responsibility"]

PRIVACY_NOTE = (
    "Your resume and job description are processed in memory to generate this "
    "report and are not stored, logged, or used for anything else."
)


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=1, max_length=50_000)
    job_description_text: str = Field(..., min_length=1, max_length=50_000)
    company_name: Optional[str] = Field(None, max_length=200)
    target_discipline: Optional[str] = Field(
        None, max_length=100, description="Knowledge pack id, e.g. 'marketing'"
    )
    # Optional context — improves feedback quality, never required, never stored.
    university: Optional[str] = Field(None, max_length=200)
    program: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    completed_courses: Optional[Union[str, list[str]]] = Field(
        None, description="Course codes/names, as a comma-separated string or list"
    )
    current_year: Optional[str] = Field(None, max_length=50)


class ScoreBreakdownItem(BaseModel):
    category: str
    label: str
    score: int
    max_score: int
    explanation: str


class DisciplineFit(BaseModel):
    discipline_id: str
    discipline: str
    confidence: Literal["high", "medium", "low"]
    matched_signals: list[str]


class JobRequirements(BaseModel):
    role_title: Optional[str] = None
    required_qualifications: list[str]
    preferred_qualifications: list[str]
    responsibilities: list[str]
    skills: list[str]
    tools: list[str]


class ResumeSignals(BaseModel):
    sections_found: list[str]
    skills_found: list[str]
    tools_found: list[str]
    student_signals: list[str]
    bullet_count: int
    quantified_bullet_count: int
    action_verb_bullet_count: int


class EvidenceItem(BaseModel):
    requirement: str
    requirement_type: RequirementType
    resume_evidence: Optional[str] = None
    match_strength: MatchStrength
    explanation: str


class MissingSkills(BaseModel):
    required_missing: list[str]
    preferred_missing: list[str]
    tools_missing: list[str]


class ImprovementSuggestion(BaseModel):
    priority: Literal["high", "medium", "low"]
    title: str
    suggestion: str
    related_requirement: Optional[str] = None


class CompanyCard(BaseModel):
    company_name: str
    industry: Optional[str] = None
    ownership: Optional[str] = None
    business_model: Optional[str] = None
    products_services: list[str] = []
    student_angle: str
    resume_angle: str
    source: Literal["wikipedia", "fallback"]


class DetectedCourse(BaseModel):
    code: str
    name: str
    disciplines: list[str] = []
    related_skills: list[str] = []
    strength: Literal["weak", "moderate", "strong"]
    note: str


class DetectedClub(BaseModel):
    name: str
    matched_text: str
    kind: Literal["club", "association", "competition"]
    disciplines: list[str] = []
    supports: list[str] = []
    strength: Literal["weak", "moderate", "strong"]
    note: str


class UniversityContext(BaseModel):
    university_name: str
    business_school: Optional[str] = None
    detected_from: Literal["provided", "resume"]
    program: Optional[str] = None
    detected_courses: list[DetectedCourse] = []
    detected_clubs: list[DetectedClub] = []
    coop_detected: bool = False
    bilingual_detected: bool = False
    notes: list[str] = []


class LocationContext(BaseModel):
    location_name: str
    detected_from: Literal["provided", "job_description", "resume"]
    industries: list[str] = []
    positioning_advice: list[str] = []


class ContextSection(BaseModel):
    section_id: Literal["university_program", "school_involvement", "location_angle"]
    title: str
    items: list[str]


class AnalyzeResponse(BaseModel):
    overall_score: int
    score_interpretation: str
    score_breakdown: list[ScoreBreakdownItem]
    detected_disciplines: list[DisciplineFit]
    extracted_job_requirements: JobRequirements
    extracted_resume_signals: ResumeSignals
    evidence_map: list[EvidenceItem]
    missing_skills: MissingSkills
    weak_areas: list[str]
    improvement_suggestions: list[ImprovementSuggestion]
    company_card: Optional[CompanyCard] = None
    university_context: Optional[UniversityContext] = None
    location_context: Optional[LocationContext] = None
    contextual_feedback: list[ContextSection] = []
    privacy_note: str = PRIVACY_NOTE
