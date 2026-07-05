import type { ImprovementSuggestion, Priority } from "@/types/analysis";

const PRIORITY_STYLES: Record<Priority, string> = {
  high: "bg-rose-100 text-rose-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-slate-100 text-slate-600",
};

export default function SuggestionsList({ suggestions }: { suggestions: ImprovementSuggestion[] }) {
  if (suggestions.length === 0) return null;
  return (
    <section>
      <h2 className="mb-1 text-lg font-semibold text-slate-900">How to improve this application</h2>
      <p className="mb-3 text-sm text-slate-600">
        Specific changes, in priority order. Only add things that are true for you.
      </p>
      <div className="space-y-3">
        {suggestions.map((s, idx) => (
          <div key={idx} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase ${PRIORITY_STYLES[s.priority]}`}
              >
                {s.priority}
              </span>
              <h3 className="text-sm font-semibold text-slate-800">{s.title}</h3>
            </div>
            <p className="mt-2 text-sm text-slate-600">{s.suggestion}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
