import type { CompanyCard } from "@/types/analysis";

export default function CompanyCardView({ card }: { card: CompanyCard }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4">
      <h2 className="text-lg font-semibold text-slate-900">
        Applying to {card.company_name}
      </h2>
      {(card.industry || card.ownership) && (
        <div className="mt-2 flex flex-wrap gap-2">
          {card.industry && (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
              {card.industry}
            </span>
          )}
          {card.ownership && (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
              {card.ownership} company
            </span>
          )}
        </div>
      )}
      {card.business_model && (
        <p className="mt-3 text-sm text-slate-600">{card.business_model}</p>
      )}
      <div className="mt-3 space-y-2 text-sm text-slate-600">
        <p>
          <span className="font-medium text-slate-800">Application angle: </span>
          {card.student_angle}
        </p>
        <p>
          <span className="font-medium text-slate-800">Resume angle: </span>
          {card.resume_angle}
        </p>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        {card.source === "wikipedia"
          ? "Company summary from Wikipedia (open data). Verify details on the company's own site."
          : "No public data lookup was available for this name — the advice above is general."}
      </p>
    </section>
  );
}
