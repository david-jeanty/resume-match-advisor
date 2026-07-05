import type { AnalyzeRequest, AnalyzeResponse } from "@/types/analysis";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  } catch {
    throw new Error(
      "Could not reach the analysis server. If you're running locally, make sure the backend is up on port 8000."
    );
  }
  if (!response.ok) {
    if (response.status === 422) {
      throw new Error(
        "Please paste both your resume and the job description (each under 50,000 characters)."
      );
    }
    throw new Error(`Analysis failed (server responded with ${response.status}). Please try again.`);
  }
  return response.json();
}
