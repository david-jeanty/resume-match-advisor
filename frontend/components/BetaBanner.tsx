// Replace the placeholder with your Google Form link, or set
// NEXT_PUBLIC_FEEDBACK_URL in Vercel to avoid a code change.
const FEEDBACK_URL =
  process.env.NEXT_PUBLIC_FEEDBACK_URL ?? "https://forms.gle/REPLACE_WITH_YOUR_FORM";

export default function BetaBanner() {
  return (
    <div className="border-b border-amber-200 bg-amber-50">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-2 text-sm text-amber-900">
        <p>
          <span className="font-semibold">🧪 Private beta</span> — a free student project
          under testing. Your resume is analyzed in memory and{" "}
          <span className="font-medium">never stored</span>; no AI service is used.
          Expect rough edges.
        </p>
        <a
          href={FEEDBACK_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 rounded-lg border border-amber-300 bg-white px-3 py-1 font-medium text-amber-900 hover:bg-amber-100"
        >
          Leave feedback
        </a>
      </div>
    </div>
  );
}
