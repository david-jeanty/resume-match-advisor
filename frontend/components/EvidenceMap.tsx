import type { EvidenceItem, MatchStrength, RequirementType } from "@/types/analysis";

const STRENGTH_STYLES: Record<MatchStrength, string> = {
  strong: "bg-emerald-100 text-emerald-800",
  moderate: "bg-amber-100 text-amber-800",
  weak: "bg-orange-100 text-orange-800",
  missing: "bg-rose-100 text-rose-800",
};

const STRENGTH_LABELS: Record<MatchStrength, string> = {
  strong: "Strong",
  moderate: "Moderate",
  weak: "Weak",
  missing: "Missing",
};

const GROUPS: { type: RequirementType; title: string }[] = [
  { type: "required", title: "Required qualifications" },
  { type: "preferred", title: "Preferred qualifications" },
  { type: "responsibility", title: "Day-to-day responsibilities" },
];

function EvidenceCard({ item }: { item: EvidenceItem }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium text-slate-800">{item.requirement}</p>
        <span
          className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${STRENGTH_STYLES[item.match_strength]}`}
        >
          {STRENGTH_LABELS[item.match_strength]}
        </span>
      </div>
      {item.resume_evidence && (
        <blockquote className="mt-2 border-l-2 border-slate-300 pl-3 text-sm italic text-slate-600">
          “{item.resume_evidence}”
        </blockquote>
      )}
      <p className="mt-2 text-xs text-slate-600">{item.explanation}</p>
    </div>
  );
}

export default function EvidenceMap({ items }: { items: EvidenceItem[] }) {
  if (items.length === 0) return null;
  return (
    <section>
      <h2 className="mb-1 text-lg font-semibold text-slate-900">Evidence map</h2>
      <p className="mb-3 text-sm text-slate-600">
        Each item the posting asks for, matched against what your resume actually shows.
      </p>
      <div className="space-y-6">
        {GROUPS.map(({ type, title }) => {
          const group = items.filter((i) => i.requirement_type === type);
          if (group.length === 0) return null;
          return (
            <div key={type}>
              <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                {title}
              </h3>
              <div className="space-y-3">
                {group.map((item, idx) => (
                  <EvidenceCard key={`${type}-${idx}`} item={item} />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
