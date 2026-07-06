"use client";

import { useState } from "react";
import type { AnalyzeResponse } from "@/types/analysis";
import { reportToMarkdown } from "@/lib/reportText";
import ScoreOverview from "./ScoreOverview";
import ScoreBreakdown from "./ScoreBreakdown";
import EvidenceMap from "./EvidenceMap";
import GapsSection from "./GapsSection";
import SuggestionsList from "./SuggestionsList";
import CompanyCardView from "./CompanyCardView";
import ContextSections from "./ContextSections";
import AdvisorNotes from "./AdvisorNotes";

export default function ResultsView({ report }: { report: AnalyzeResponse }) {
  const [copied, setCopied] = useState(false);

  async function copyReport() {
    try {
      await navigator.clipboard.writeText(reportToMarkdown(report));
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Clipboard unavailable (e.g. insecure context) — quietly ignore.
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Your match report</h1>
        <button
          onClick={copyReport}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          {copied ? "Copied ✓" : "Copy report"}
        </button>
      </div>

      <ScoreOverview report={report} />
      <ScoreBreakdown items={report.score_breakdown} />
      <EvidenceMap items={report.evidence_map} />
      <GapsSection missing={report.missing_skills} weakAreas={report.weak_areas} />
      <SuggestionsList suggestions={report.improvement_suggestions} />
      <AdvisorNotes notes={report.advisor_notes ?? []} />
      <ContextSections sections={report.contextual_feedback ?? []} />
      {report.company_card && <CompanyCardView card={report.company_card} />}

      <p className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500">
        🔒 {report.privacy_note}
      </p>
    </div>
  );
}
