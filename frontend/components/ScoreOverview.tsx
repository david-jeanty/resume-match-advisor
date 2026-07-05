import type { AnalyzeResponse } from "@/types/analysis";

const CONFIDENCE_LABEL = { high: "high confidence", medium: "medium confidence", low: "low confidence" };

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-700";
  if (score >= 65) return "text-teal-700";
  if (score >= 50) return "text-amber-700";
  return "text-rose-700";
}

export default function ScoreOverview({ report }: { report: AnalyzeResponse }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex items-baseline gap-1">
          <span className={`text-6xl font-bold ${scoreColor(report.overall_score)}`}>
            {report.overall_score}
          </span>
          <span className="text-xl text-slate-400">/100</span>
        </div>
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-slate-900">Overall match</h2>
          <p className="mt-1 text-sm text-slate-600">{report.score_interpretation}</p>
          <p className="mt-2 text-xs text-slate-400">
            This score reflects how clearly your resume demonstrates what this posting asks
            for — not your actual ability, and not a prediction of any screening system.
          </p>
        </div>
      </div>
      {report.detected_disciplines.length > 0 && (
        <div className="mt-4 border-t border-slate-100 pt-4">
          <span className="text-sm font-medium text-slate-700">Detected discipline fit: </span>
          <span className="mt-2 inline-flex flex-wrap gap-2 align-middle">
            {report.detected_disciplines.map((d) => (
              <span
                key={d.discipline_id}
                title={d.matched_signals.join(", ")}
                className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700"
              >
                {d.discipline}
                <span className="ml-1 text-xs text-slate-400">
                  ({CONFIDENCE_LABEL[d.confidence]})
                </span>
              </span>
            ))}
          </span>
        </div>
      )}
    </div>
  );
}
