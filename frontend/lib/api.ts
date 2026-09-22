const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_URL}/health`);
  return res.json();
}

export async function fetchReport() {
  const res = await fetch(`${API_URL}/reports/today`);
  return res.json();
}

export async function runDailyJob() {
  const res = await fetch(`${API_URL}/run-daily-job`, { method: "POST" });
  return res.json();
}

export async function fetchStudents() {
  const res = await fetch(`${API_URL}/reports/today`);
  return res.json();
}
