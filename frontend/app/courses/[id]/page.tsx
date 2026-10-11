"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchCourse, fetchCourseStatus, reserveSeat, enrollInCourse, type Course } from "@/lib/api";

interface CourseStatus {
  course: Course;
  enrollment?: { id: string; status: string; payment_id?: string };
  can_enroll: boolean;
  seats_available?: number;
}

const formatPrice = (minor: number, currency: string) => {
  const major = (minor / 100).toFixed(2);
  const symbols: Record<string, string> = { GHS: "₵", USD: "$", EUR: "€" };
  return `${symbols[currency] || currency} ${major}`;
};

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.id as string;

  const [course, setCourse] = useState<Course | null>(null);
  const [status, setStatus] = useState<{ course: Course; enrollment?: any; can_enroll: boolean; seats_available?: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [courseData, statusData] = await Promise.all([
          fetchCourse(courseId),
          fetchCourseStatus(courseId),
        ]);
        setCourse(courseData);
        setStatus(statusData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load course");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [courseId]);

  const handleReserveSeat = async () => {
    if (!course) return;
    setActionLoading("reserve");
    try {
      const response = await reserveSeat(courseId, "seefcash");
      window.location.href = response.authorization_url;
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to reserve seat");
    } finally {
      setActionLoading(null);
    }
  };

  const handleEnroll = async () => {
    if (!course) return;
    setActionLoading("enroll");
    try {
      await enrollInCourse(courseId, "seefcash");
      router.refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to enrol");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "3rem" }}>
        <div style={{ display: "inline-block", width: "2rem", height: "2rem", border: "3px solid #e5e7eb", borderTopColor: "#2563eb", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
        <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <p style={{ marginTop: "1rem", color: "#6b7280" }}>Loading course...</p>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div style={{ textAlign: "center", padding: "3rem", color: "#dc2626" }}>
        <h2>Course not found</h2>
        <p>{error || "The requested course does not exist."}</p>
        <Link href="/courses" style={{ display: "inline-block", marginTop: "1rem", padding: "0.5rem 1rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: "0.375rem", textDecoration: "none" }}>
          Browse Courses
        </Link>
      </div>
    );
  }

  const enrollment = status?.enrollment;
  const canEnroll = status?.can_enroll && !enrollment;
  const isEnrolled = enrollment && enrollment.status === "active";
  const hasSeatReserved = enrollment && enrollment.status === "seat_reserved";
  const seatsAvailable = status?.seats_available;

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto" }}>
      <Link href="/courses" style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", color: "#6b7280", textDecoration: "none", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5"/><polyline points="12 19 5 12 12 5"/></svg>
        Back to Courses
      </Link>

      <article>
        <header style={{ marginBottom: "2rem" }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
            <span style={{ background: "#dcfce7", color: "#166534", fontSize: "0.75rem", fontWeight: 600, padding: "0.25rem 0.625rem", borderRadius: "9999px" }}>Active</span>
            {course.capacity && (
              <span style={{ background: "#fef3c7", color: "#92400e", fontSize: "0.75rem", fontWeight: 600, padding: "0.25rem 0.625rem", borderRadius: "9999px" }}>
                Max {course.capacity} students
              </span>
            )}
          </div>
          <h1 style={{ fontSize: "2.5rem", fontWeight: 800, color: "#111827", lineHeight: 1.2, marginBottom: "0.5rem" }}>{course.name}</h1>
          <p style={{ color: "#6b7280", fontSize: "1.125rem", maxWidth: "700px" }}>{course.description || "No description available."}</p>
        </header>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "2rem" }}>
          <section style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem", marginBottom: "2rem", padding: "1.5rem", background: "#f9fafb", borderRadius: "0.75rem" }}>
              {course.start_date && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <div style={{ width: "40px", height: "40px", background: "#dbeafe", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", color: "#2563eb" }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Start Date</div>
                    <div style={{ fontWeight: 600, color: "#111827" }}>{new Date(course.start_date!).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</div>
                  </div>
                </div>
              )}
              {course.class_time && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <div style={{ width: "40px", height: "40px", background: "#fef3c7", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", color: "#f59e0b" }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Class Time</div>
                    <div style={{ fontWeight: 600, color: "#111827" }}>{course.class_time} {course.timezone || "GMT"}</div>
                  </div>
                </div>
              )}
              {course.expected_study_hours && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <div style={{ width: "40px", height: "40px", background: "#f3e8ff", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", color: "#a855f7" }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Study Time</div>
                    <div style={{ fontWeight: 600, color: "#111827" }}>{course.expected_study_hours} hours total</div>
                  </div>
                </div>
              )}
              {course.capacity && (
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <div style={{ width: "40px", height: "40px", background: "#fce7f3", borderRadius: "0.5rem", display: "flex", alignItems: "center", justifyContent: "center", color: "#ec4899" }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                  </div>
                  <div>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Capacity</div>
                    <div style={{ fontWeight: 600, color: "#111827" }}>{course.capacity} students max</div>
                  </div>
                </div>
              )}
            </div>

            {course.learning_outcomes.length > 0 && (
              <section style={{ marginBottom: "2rem" }}>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#111827", marginBottom: "1rem" }}>What You'll Learn</h2>
                <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "0.75rem" }}>
                  {course.learning_outcomes.map((outcome, i) => (
                    <li key={i} style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem", padding: "1rem", background: "#f9fafb", borderRadius: "0.5rem", border: "1px solid #e5e7eb" }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2.5" style={{ flexShrink: 0, marginTop: "0.125rem" }}><polyline points="20 6 9 17 4 12"/></svg>
                      <span style={{ color: "#374151", lineHeight: 1.6 }}>{outcome}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {course.prerequisites.length > 0 && (
              <section style={{ marginBottom: "2rem" }}>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#111827", marginBottom: "1rem" }}>Prerequisites</h2>
                <ul style={{ listStyle: "none", padding: 0, display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {course.prerequisites.map((prereq, i) => (
                    <li key={i} style={{ background: "#fef3c7", color: "#92400e", padding: "0.5rem 1rem", borderRadius: "9999px", fontSize: "0.875rem", fontWeight: 500 }}>{prereq}</li>
                  ))}
                </ul>
              </section>
            )}

            {course.support_email && (
              <section style={{ marginBottom: "2rem" }}>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#111827", marginBottom: "1rem" }}>Support</h2>
                <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "0.5rem", padding: "1rem" }}>
                  <p style={{ margin: 0, color: "#166534" }}><strong>Email:</strong> {course.support_email}</p>
                  {course.support_phone && <p style={{ margin: "0.5rem 0 0", color: "#166534" }}><strong>Phone:</strong> {course.support_phone}</p>}
                </div>
              </section>
            )}
          </section>

          <aside>
            <div style={{ position: "sticky", top: "100px", background: "#fff", border: "1px solid #e5e7eb", borderRadius: "0.75rem", padding: "1.5rem" }}>
              <div style={{ marginBottom: "1.5rem", paddingBottom: "1.5rem", borderBottom: "1px solid #e5e7eb" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.5rem" }}>
                  <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Tuition</div>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#111827" }}>{formatPrice(course.price_minor, course.currency)}</div>
                </div>
                <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>One-time payment, lifetime access</div>
              </div>

              <div style={{ marginBottom: "1.5rem", paddingBottom: "1.5rem", borderBottom: "1px solid #e5e7eb" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "0.5rem" }}>
                  <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em" }}>Seat Reservation</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>{formatPrice(course.seat_reservation_minor, course.currency)}</div>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#2563eb" }}>Counts toward tuition • Refundable if not admitted</div>
              </div>

              {isEnrolled && (
                <div style={{ background: "#dcfce7", border: "1px solid #bbf7d0", borderRadius: "0.5rem", padding: "1rem", marginBottom: "1.5rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#166534", fontWeight: 600 }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
                    <span>You're enrolled!</span>
                  </div>
                  <p style={{ margin: "0.5rem 0 0", fontSize: "0.875rem", color: "#166534" }}>Access your course from the <Link href="/dashboard" style={{ color: "#166534", textDecoration: "underline" }}>Dashboard</Link>.</p>
                </div>
              )}

              {hasSeatReserved && (
                <div style={{ background: "#fef3c7", border: "1px solid #fde68a", borderRadius: "0.5rem", padding: "1rem", marginBottom: "1.5rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#92400e", fontWeight: 600 }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                    <span>Seat Reserved</span>
                  </div>
                  <p style={{ margin: "0.5rem 0 0", fontSize: "0.875rem", color: "#92400e" }}>Complete tuition payment to confirm enrolment.</p>
                </div>
              )}

              {!isEnrolled && !hasSeatReserved && canEnroll && (
                <>
                  <button
                    onClick={handleReserveSeat}
                    disabled={actionLoading === "reserve"}
                    style={{ width: "100%", padding: "0.875rem 1.5rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: "0.5rem", fontSize: "1rem", fontWeight: 600, cursor: actionLoading === "reserve" ? "not-allowed" : "pointer", transition: "background 0.2s" }}
                  >
                    {actionLoading === "reserve" ? (
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: "spin 1s linear infinite" }}><circle cx="12" cy="12" r="10" strokeOpacity="0.25"/><path d="M12 2v4"/><style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style></svg>
                        Redirecting to SeefCash...
                      </span>
                    ) : (
                      "Reserve Seat — " + formatPrice(course.seat_reservation_minor, course.currency)
                    )}
                  </button>
                  <p style={{ marginTop: "0.75rem", fontSize: "0.75rem", color: "#6b7280", textAlign: "center" }}>
                    Secure payment via SeefCash (Mobile Money). Redirects to payment page.
                  </p>
                </>
              )}

              {!isEnrolled && !hasSeatReserved && !canEnroll && (
                <div style={{ textAlign: "center", padding: "1rem", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "0.5rem", color: "#dc2626" }}>
                  {seatsAvailable === 0 ? "This course is full" : "Enrolment not available"}
                </div>
              )}
            </div>
          </aside>
        </div>
      </article>
    </div>
  );
}