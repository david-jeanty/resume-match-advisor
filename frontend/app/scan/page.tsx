"use client";

import { useState } from "react";
import { analyze } from "@/lib/api";
import type { AnalyzeResponse } from "@/types/analysis";
import { DISCIPLINES } from "@/types/analysis";
import ResultsView from "@/components/ResultsView";

export default function ScanPage() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [discipline, setDiscipline] = useState("");
  const [university, setUniversity] = useState("");
  const [program, setProgram] = useState("");
  const [location, setLocation] = useState("");
  const [courses, setCourses] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AnalyzeResponse | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!resumeText.trim() || !jdText.trim()) {
      setError("Please paste both your resume and the job description.");
      return;
    }
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await analyze({
        resume_text: resumeText,
        job_description_text: jdText,
        company_name: companyName.trim() || null,
        target_discipline: discipline || null,
        university: university.trim() || null,
        program: program.trim() || null,
        location: location.trim() || null,
        completed_courses: courses.trim() || null,
      });
      setReport(result);
      // Bring the results into view once they render.
      setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
      }, 50);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">Check your match</h1>
      <p className="mt-2 text-sm text-slate-600">
        Paste your resume and the job description below. Everything is analyzed in memory —{" "}
        <span className="font-medium text-slate-800">your resume is not stored</span>.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5">
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label htmlFor="resume" className="mb-1 block text-sm font-medium text-slate-700">
              Your resume (paste as text)
            </label>
            <textarea
              id="resume"
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={16}
              maxLength={50000}
              placeholder="Paste your full resume text here…"
              className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="jd" className="mb-1 block text-sm font-medium text-slate-700">
              Job description
            </label>
            <textarea
              id="jd"
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={16}
              maxLength={50000}
              placeholder="Paste the full job posting here…"
              className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label htmlFor="company" className="mb-1 block text-sm font-medium text-slate-700">
              Company name <span className="text-slate-400">(optional)</span>
            </label>
            <input
              id="company"
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              maxLength={200}
              placeholder="e.g. RBC, Deloitte, Shopify"
              className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="discipline" className="mb-1 block text-sm font-medium text-slate-700">
              Target discipline <span className="text-slate-400">(optional — auto-detected if blank)</span>
            </label>
            <select
              id="discipline"
              value={discipline}
              onChange={(e) => setDiscipline(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
            >
              <option value="">Auto-detect from the job description</option>
              {DISCIPLINES.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <details className="rounded-xl border border-slate-200 bg-white">
          <summary className="cursor-pointer select-none p-4 text-sm font-medium text-slate-700">
            Optional context{" "}
            <span className="font-normal text-slate-400">
              — university, program, location, courses
            </span>
          </summary>
          <div className="space-y-4 border-t border-slate-100 p-4">
            <p className="text-xs text-slate-500">
              Optional context helps the tool translate courses, clubs, and local student
              experiences into resume evidence. It is not stored.
            </p>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="university" className="mb-1 block text-sm font-medium text-slate-700">
                  University
                </label>
                <input
                  id="university"
                  type="text"
                  value={university}
                  onChange={(e) => setUniversity(e.target.value)}
                  maxLength={200}
                  placeholder="e.g. University of Ottawa"
                  className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="program" className="mb-1 block text-sm font-medium text-slate-700">
                  Program
                </label>
                <input
                  id="program"
                  type="text"
                  value={program}
                  onChange={(e) => setProgram(e.target.value)}
                  maxLength={200}
                  placeholder="e.g. BCom, BTM, Marketing, Finance"
                  className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="location" className="mb-1 block text-sm font-medium text-slate-700">
                  Location
                </label>
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  maxLength={200}
                  placeholder="e.g. Ottawa / Kanata"
                  className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="courses" className="mb-1 block text-sm font-medium text-slate-700">
                  Completed or relevant courses
                </label>
                <input
                  id="courses"
                  type="text"
                  value={courses}
                  onChange={(e) => setCourses(e.target.value)}
                  maxLength={500}
                  placeholder="e.g. ADM 1370, ADM 2372, ADM 2302, ADM 2320"
                  className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:border-slate-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </details>

        {error && (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-slate-900 px-8 py-3 font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze my match"}
        </button>
      </form>

      {loading && (
        <div className="mt-8 animate-pulse rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">
          Comparing your resume to the posting — extracting requirements, mapping evidence,
          and scoring each category…
        </div>
      )}

      {report && (
        <div id="results" className="mt-10">
          <ResultsView report={report} />
        </div>
      )}
    </div>
  );
}
