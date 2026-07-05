import type { AnalyzeResponse } from "@/types/analysis";

const STRENGTH_LABEL: Record<string, string> = {
  strong: "Strong",
  moderate: "Moderate",
  weak: "Weak",
  missing: "Missing",
};

/** Renders the report as plain markdown for the copy/export button. */
export function reportToMarkdown(report: AnalyzeResponse): string {
  const lines: string[] = [];
  lines.push(`# Resume Match Report`);
  lines.push("");
  lines.push(`**Overall match: ${report.overall_score}/100**`);
  lines.push(report.score_interpretation);
  lines.push("");

  lines.push(`## Score breakdown`);
  for (const item of report.score_breakdown) {
    lines.push(`- **${item.label}: ${item.score}/${item.max_score}** — ${item.explanation}`);
  }
  lines.push("");

  if (report.detected_disciplines.length > 0) {
    lines.push(`## Discipline fit`);
    for (const d of report.detected_disciplines) {
      lines.push(`- ${d.discipline} (${d.confidence} confidence)`);
    }
    lines.push("");
  }

  lines.push(`## Evidence map`);
  for (const item of report.evidence_map) {
    lines.push(`### [${STRENGTH_LABEL[item.match_strength]}] ${item.requirement}`);
    if (item.resume_evidence) lines.push(`> ${item.resume_evidence}`);
    lines.push(item.explanation);
    lines.push("");
  }

  const missing = report.missing_skills;
  if (
    missing.required_missing.length ||
    missing.preferred_missing.length ||
    missing.tools_missing.length
  ) {
    lines.push(`## Missing skills & tools`);
    if (missing.required_missing.length)
      lines.push(`- Required skills not found: ${missing.required_missing.join(", ")}`);
    if (missing.preferred_missing.length)
      lines.push(`- Preferred skills not found: ${missing.preferred_missing.join(", ")}`);
    if (missing.tools_missing.length)
      lines.push(`- Tools not found: ${missing.tools_missing.join(", ")}`);
    lines.push("");
  }

  if (report.weak_areas.length) {
    lines.push(`## Weak areas`);
    for (const area of report.weak_areas) lines.push(`- ${area}`);
    lines.push("");
  }

  lines.push(`## Improvement suggestions`);
  for (const s of report.improvement_suggestions) {
    lines.push(`- **[${s.priority}] ${s.title}** — ${s.suggestion}`);
  }
  lines.push("");

  if (report.company_card) {
    const c = report.company_card;
    lines.push(`## Company: ${c.company_name}`);
    if (c.industry) lines.push(`- Industry: ${c.industry}`);
    if (c.ownership) lines.push(`- Ownership: ${c.ownership}`);
    if (c.business_model) lines.push(`- About: ${c.business_model}`);
    lines.push(`- Application angle: ${c.student_angle}`);
    lines.push(`- Resume angle: ${c.resume_angle}`);
    lines.push("");
  }

  lines.push(`---`);
  lines.push(report.privacy_note);
  return lines.join("\n");
}
