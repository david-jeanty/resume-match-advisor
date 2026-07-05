import type { MissingSkills } from "@/types/analysis";

function SkillPills({ label, skills, tone }: { label: string; skills: string[]; tone: string }) {
  if (skills.length === 0) return null;
  return (
    <div>
      <h3 className="text-sm font-medium text-slate-700">{label}</h3>
      <div className="mt-1.5 flex flex-wrap gap-2">
        {skills.map((s) => (
          <span key={s} className={`rounded-full px-3 py-1 text-sm ${tone}`}>
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function GapsSection({
  missing,
  weakAreas,
}: {
  missing: MissingSkills;
  weakAreas: string[];
}) {
  const hasMissing =
    missing.required_missing.length > 0 ||
    missing.preferred_missing.length > 0 ||
    missing.tools_missing.length > 0;
  if (!hasMissing && weakAreas.length === 0) return null;

  return (
    <section className="grid gap-4 md:grid-cols-2">
      {hasMissing && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="text-lg font-semibold text-slate-900">Missing from your resume</h2>
          <p className="mt-1 text-xs text-slate-500">
            “Missing” means not found on the page — if you actually have it, that&apos;s an easy fix.
          </p>
          <div className="mt-3 space-y-3">
            <SkillPills
              label="Required skills not found"
              skills={missing.required_missing}
              tone="bg-rose-100 text-rose-800"
            />
            <SkillPills
              label="Preferred skills not found"
              skills={missing.preferred_missing}
              tone="bg-orange-100 text-orange-800"
            />
            <SkillPills
              label="Tools not found"
              skills={missing.tools_missing}
              tone="bg-amber-100 text-amber-800"
            />
          </div>
        </div>
      )}
      {weakAreas.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h2 className="text-lg font-semibold text-slate-900">Weakly supported areas</h2>
          <ul className="mt-3 space-y-2">
            {weakAreas.map((area, idx) => (
              <li key={idx} className="flex gap-2 text-sm text-slate-600">
                <span className="mt-0.5 text-amber-500">▸</span>
                <span>{area}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
