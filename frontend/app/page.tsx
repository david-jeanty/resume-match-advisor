import Link from "next/link";

const steps = [
  {
    title: "Paste your resume and the job posting",
    body: "No file uploads needed, no account, nothing saved. Optionally add the company name and target discipline.",
  },
  {
    title: "Get an honest, explainable match score",
    body: "Every point is traceable: required qualifications, skills and tools, experience evidence, discipline fit, keywords, and resume clarity.",
  },
  {
    title: "See your evidence — and your gaps",
    body: "A requirement-by-requirement evidence map shows what your resume already proves, what's transferable, and what's genuinely missing.",
  },
];

const audiences = [
  "Marketing", "Finance", "Accounting", "Business Analytics", "BTM / MIS",
  "Consulting", "Operations & Supply Chain", "HR", "Sales & RevOps",
];

export default function LandingPage() {
  return (
    <div className="mx-auto max-w-5xl px-4">
      <section className="py-16 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          How well does your resume match that job posting?
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-600">
          A free match advisor built for commerce and business students. It compares your
          resume to a job description and shows the evidence you already have, the gaps
          you can fix, and how your clubs, case competitions, class projects, and
          part-time jobs translate into business experience.
        </p>
        <div className="mt-8">
          <Link
            href="/scan"
            className="inline-block rounded-xl bg-slate-900 px-8 py-3 text-lg font-medium text-white hover:bg-slate-700"
          >
            Check my match — free
          </Link>
        </div>
        <p className="mt-4 text-sm text-slate-500">
          No sign-up. Your resume is analyzed in memory and never stored.
        </p>
      </section>

      <section className="grid gap-6 pb-12 sm:grid-cols-3">
        {steps.map((step, i) => (
          <div key={step.title} className="rounded-xl border border-slate-200 bg-white p-6">
            <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
              {i + 1}
            </div>
            <h2 className="font-semibold text-slate-900">{step.title}</h2>
            <p className="mt-2 text-sm text-slate-600">{step.body}</p>
          </div>
        ))}
      </section>

      <section className="pb-12">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="font-semibold text-slate-900">Built for business student experience</h2>
          <p className="mt-2 text-sm text-slate-600">
            Generic scanners undervalue student experience. This one understands that club
            leadership can be project coordination, that a case competition is real analysis
            work, and that a part-time retail job is genuine operations and customer
            evidence — and it tells you how to make that explicit.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {audiences.map((a) => (
              <span
                key={a}
                className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700"
              >
                {a}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="pb-16">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          <h2 className="font-semibold">What this tool is (and isn&apos;t)</h2>
          <p className="mt-2">
            This is an educational advisor, not an “ATS beater.” No tool can guarantee that
            software or a recruiter will pass your resume. What this one does is honest:
            it shows how clearly your resume demonstrates what a specific posting asks
            for, and gives you specific, student-relevant ways to improve it.
          </p>
        </div>
      </section>
    </div>
  );
}
