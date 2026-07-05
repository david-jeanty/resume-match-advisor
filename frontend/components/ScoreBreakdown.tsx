import type { ScoreBreakdownItem } from "@/types/analysis";

function barColor(ratio: number): string {
  if (ratio >= 0.8) return "bg-emerald-500";
  if (ratio >= 0.5) return "bg-amber-500";
  return "bg-rose-500";
}

export default function ScoreBreakdown({ items }: { items: ScoreBreakdownItem[] }) {
  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold text-slate-900">Score breakdown</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => {
          const ratio = item.max_score > 0 ? item.score / item.max_score : 0;
          return (
            <div key={item.category} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-800">{item.label}</h3>
                <span className="text-sm font-semibold text-slate-900">
                  {item.score}
                  <span className="font-normal text-slate-400">/{item.max_score}</span>
                </span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full ${barColor(ratio)}`}
                  style={{ width: `${Math.round(ratio * 100)}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-slate-600">{item.explanation}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
