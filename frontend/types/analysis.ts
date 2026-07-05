// Mirrors the backend Pydantic models in backend/app/models.py.

export type MatchStrength = "strong" | "moderate" | "weak" | "missing";
export type RequirementType = "required" | "preferred" | "responsibility";
export type Priority = "high" | "medium" | "low";
export type Confidence = "high" | "medium" | "low";

export interface AnalyzeRequest {
  resume_text: string;
  job_description_text: string;
  company_name?: string | null;
  target_discipline?: string | null;
}

export interface ScoreBreakdownItem {
  category: string;
  label: string;
  score: number;
  max_score: number;
  explanation: string;
}

export interface DisciplineFit {
  discipline_id: string;
  discipline: string;
  confidence: Confidence;
  matched_signals: string[];
}

export interface JobRequirements {
  role_title: string | null;
  required_qualifications: string[];
  preferred_qualifications: string[];
  responsibilities: string[];
  skills: string[];
  tools: string[];
}

export interface ResumeSignals {
  sections_found: string[];
  skills_found: string[];
  tools_found: string[];
  student_signals: string[];
  bullet_count: number;
  quantified_bullet_count: number;
  action_verb_bullet_count: number;
}

export interface EvidenceItem {
  requirement: string;
  requirement_type: RequirementType;
  resume_evidence: string | null;
  match_strength: MatchStrength;
  explanation: string;
}

export interface MissingSkills {
  required_missing: string[];
  preferred_missing: string[];
  tools_missing: string[];
}

export interface ImprovementSuggestion {
  priority: Priority;
  title: string;
  suggestion: string;
  related_requirement?: string | null;
}

export interface CompanyCard {
  company_name: string;
  industry: string | null;
  ownership: string | null;
  business_model: string | null;
  products_services: string[];
  student_angle: string;
  resume_angle: string;
  source: "wikipedia" | "fallback";
}

export interface AnalyzeResponse {
  overall_score: number;
  score_interpretation: string;
  score_breakdown: ScoreBreakdownItem[];
  detected_disciplines: DisciplineFit[];
  extracted_job_requirements: JobRequirements;
  extracted_resume_signals: ResumeSignals;
  evidence_map: EvidenceItem[];
  missing_skills: MissingSkills;
  weak_areas: string[];
  improvement_suggestions: ImprovementSuggestion[];
  company_card: CompanyCard | null;
  privacy_note: string;
}

export const DISCIPLINES: { id: string; label: string }[] = [
  { id: "marketing", label: "Marketing" },
  { id: "finance", label: "Finance" },
  { id: "accounting", label: "Accounting" },
  { id: "business_analytics", label: "Business Analytics" },
  { id: "btm_mis", label: "Business Technology Management (BTM/MIS)" },
  { id: "consulting", label: "Consulting" },
  { id: "operations", label: "Operations & Supply Chain" },
  { id: "hr", label: "HR / People Operations" },
  { id: "sales_revops", label: "Sales / Revenue Operations" },
];
