import type { ContextSection } from "@/types/analysis";

const SECTION_ICONS: Record<ContextSection["section_id"], string> = {
  university_program: "🎓",
  school_involvement: "🤝",
  location_angle: "📍",
};

export default function ContextSections({ sections }: { sections: ContextSection[] }) {
  if (sections.length === 0) return null;
  return (
    <section className="space-y-4">
      {sections.map((section) => (
        <div
          key={section.section_id}
          className="rounded-xl border border-sky-200 bg-sky-50 p-4"
        >
          <h2 className="text-base font-semibold text-slate-900">
            {SECTION_ICONS[section.section_id]} {section.title}
          </h2>
          <ul className="mt-3 space-y-2">
            {section.items.map((item, idx) => (
              <li key={idx} className="flex gap-2 text-sm text-slate-700">
                <span className="mt-0.5 shrink-0 text-sky-500">▸</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}
