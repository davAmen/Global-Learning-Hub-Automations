const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    credentials: "include",
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// Health & Reports
export async function fetchHealth() {
  return fetchJson(`${API_URL}/health`);
}

export async function fetchReport() {
  return fetchJson(`${API_URL}/reports/today`);
}

export async function runDailyJob() {
  return fetchJson(`${API_URL}/run-daily-job`, { method: "POST" });
}

// Courses
export async function fetchCourses() {
  return fetchJson(`${API_URL}/courses`);
}

export async function fetchCourse(courseId: string) {
  return fetchJson(`${API_URL}/courses/${courseId}`);
}

// Auth
export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  phone?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    name: string;
    email: string;
    phone?: string;
    role: string;
    email_verified: boolean;
  };
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone?: string;
  role: string;
  email_verified: boolean;
  created_at: string;
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  return fetchJson(`${API_URL}/auth/register`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  return fetchJson(`${API_URL}/auth/login`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logout() {
  return fetchJson(`${API_URL}/auth/logout`, { method: "POST" });
}

export async function refreshToken(): Promise<TokenResponse> {
  return fetchJson(`${API_URL}/auth/refresh`, { method: "POST" });
}

export async function fetchProfile(): Promise<UserProfile> {
  return fetchJson(`${API_URL}/auth/me`);
}

export async function forgotPassword(email: string) {
  return fetchJson(`${API_URL}/auth/forgot-password`, {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token: string, newPassword: string) {
  return fetchJson(`${API_URL}/auth/reset-password`, {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function verifyEmail(token: string) {
  return fetchJson(`${API_URL}/auth/verify-email`, {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

// Enrolments
export interface CourseStatus {
  course: {
    id: string;
    name: string;
    description?: string;
    start_date?: string;
    class_time?: string;
    price_minor: number;
    currency: string;
    seat_reservation_minor: number;
    expected_study_hours?: number;
    learning_outcomes: string[];
    prerequisites: string[];
    capacity?: number;
    seats_available?: number;
  };
  enrollment?: {
    id: string;
    status: string;
    payment_id?: string;
  };
  can_enroll: boolean;
  seats_available?: number;
}

export interface EnrollmentResponse {
  id: string;
  student_id: string;
  course_id: string;
  status: string;
  enrolled_at: string;
  payment_id?: string;
  seat_reserved: boolean;
  seat_reservation_verified_at?: string;
}

export async function fetchCourseStatus(courseId: string): Promise<CourseStatus> {
  return fetchJson(`${API_URL}/enrollments/course/${courseId}/status`);
}

export async function reserveSeat(courseId: string, paymentProvider: string = "seefcash"): Promise<{
  payment_id: string;
  provider_payment_id: string;
  authorization_url: string;
  amount_minor: number;
  currency: string;
  reference: string;
  expires_at: string;
}> {
  return fetchJson(`${API_URL}/enrollments/reserve-seat`, {
    method: "POST",
    body: JSON.stringify({ course_id: courseId, payment_provider: paymentProvider }),
  });
}

export async function confirmSeatReservation(paymentId: string): Promise<EnrollmentResponse> {
  return fetchJson(`${API_URL}/enrollments/confirm-seat-reservation`, {
    method: "POST",
    body: JSON.stringify({ payment_id: paymentId }),
  });
}

export async function enrollInCourse(courseId: string, paymentProvider: string = "seefcash"): Promise<EnrollmentResponse> {
  return fetchJson(`${API_URL}/enrollments/enroll`, {
    method: "POST",
    body: JSON.stringify({ course_id: courseId, payment_provider: paymentProvider }),
  });
}

export async function fetchMyEnrollments(): Promise<EnrollmentResponse[]> {
  return fetchJson(`${API_URL}/enrollments/my-enrollments`);
}