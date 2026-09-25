const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type DailyReport = {
  date: string;
  courses_today: number;
  total_enrolled: number;
  engagement: { active: number; low_engagement: number; needs_followup: number };
  reminders: { sent: number; failed: number };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...init, cache: "no-store" });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  report: () => request<DailyReport>("/reports/today")
};
