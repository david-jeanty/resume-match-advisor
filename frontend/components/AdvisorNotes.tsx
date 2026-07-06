import type { AdvisorNote } from "@/types/analysis";

const CATEGORY_LABELS: Record<AdvisorNote["category"], string> = {
  false_gap: "Possible wording gap",
  gap_explanation: "Genuine gap",
  positioning: "Positioning",
  experience_translation: "Translate your experience",
  role_suggestion: "Role-specific",
  context_advice: "Your context",
  company_angle: "Company angle",
};

const CATEGORY_STYLES: Record<AdvisorNote["category"], string> = {
  false_gap: "bg-violet-100 text-violet-800",
  gap_explanation: "bg-rose-100 text-rose-800",
  positioning: "bg-emerald-100 text-emerald-800",
  experience_translation: "bg-amber-100 text-amber-800",
  role_suggestion: "bg-slate-100 text-slate-700",
  context_advice: "bg-sky-100 text-sky-800",
  company_angle: "bg-teal-100 text-teal-800",
};

export default function AdvisorNotes({ notes }: { notes: AdvisorNote[] }) {
  if (!notes || notes.length === 0) return null;
  return (
    <section>
      <h2 className="mb-1 text-lg font-semibold text-slate-900">Advisor insights</h2>
      <p className="mb-3 text-sm text-slate-600">
        Deeper, rule-based reading of your results — including gaps that may just be
        wording problems. Generated locally with no AI service.
      </p>
      <div className="space-y-3">
        {notes.map((note, idx) => (
          <div key={idx} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${CATEGORY_STYLES[note.category]}`}
              >
                {CATEGORY_LABELS[note.category]}
              </span>
              <h3 className="text-sm font-semibold text-slate-800">{note.title}</h3>
            </div>
            <p className="mt-2 text-sm text-slate-600">{note.message}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
