"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchProfile, fetchMyEnrollments, logout } from "@/lib/api";

interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone?: string;
  role: string;
  email_verified: boolean;
  created_at: string;
}

interface Enrollment {
  id: string;
  student_id: string;
  course_id: string;
  status: string;
  enrolled_at: string;
  payment_id?: string;
  seat_reserved: boolean;
  seat_reservation_verified_at?: string;
}

export default function DashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);

  const getStatusBadge = (status: string) => {
    const styles: Record<string, { bg: string; text: string; label: string }> = {
      active: { bg: "#dcfce7", text: "#166534", label: "Active" },
      seat_reserved: { bg: "#fef3c7", text: "#92400e", label: "Seat Reserved" },
      pending_seat_payment: { bg: "#fef3c7", text: "#92400e", label: "Pending Payment" },
      completed: { bg: "#dbeafe", text: "#1e40af", label: "Completed" },
      dropped: { bg: "#f3f4f6", text: "#6b7280", label: "Dropped" },
    };
    return styles[status] || { bg: "#f3f4f6", text: "#6b7280", label: status };
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [profile, enrolments] = await Promise.all([
          fetchProfile(),
          fetchMyEnrollments(),
        ]);
        setUser(profile);
        setEnrollments(enrolments);
      } catch {
        window.location.href = "/login";
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleLogout = async () => {
    await logout();
    window.location.href = "/";
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "3rem" }}>
        <div style={{ display: "inline-block", width: "2rem", height: "2rem", border: "3px solid #e5e7eb", borderTopColor: "#2563eb", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
        <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!user) {
    return <script dangerouslySetInnerHTML={{ __html: "window.location.href = '/login';" }} />;
  }

  const activeEnrollments = enrollments.filter(e => e.status === "active");
  const pendingEnrollments = enrollments.filter(e => e.status === "seat_reserved" || e.status === "pending_seat_payment");
  const completedEnrollments = enrollments.filter(e => e.status === "completed");

  return (
    <div>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "2rem", fontWeight: 800, color: "#111827", marginBottom: "0.25rem" }}>Welcome back, {user.name}</h1>
          <p style={{ color: "#6b7280" }}>Manage your courses and track your progress</p>
        </div>
        <button onClick={handleLogout} style={{ background: "none", border: "1px solid #d1d5db", color: "#374151", padding: "0.5rem 1rem", borderRadius: "0.375rem", cursor: "pointer", fontSize: "0.875rem" }}>Logout</button>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div style={{ background: "#dcfce7", border: "1px solid #bbf7d0", borderRadius: "0.75rem", padding: "1.5rem" }}>
          <div style={{ fontSize: "0.75rem", color: "#166534", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Active Courses</div>
          <div style={{ fontSize: "2.5rem", fontWeight: 800, color: "#166534" }}>{activeEnrollments.length}</div>
        </div>
        <div style={{ background: "#fef3c7", border: "1px solid #fde68a", borderRadius: "0.75rem", padding: "1.5rem" }}>
          <div style={{ fontSize: "0.75rem", color: "#92400e", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Pending Payment</div>
          <div style={{ fontSize: "2.5rem", fontWeight: 800, color: "#92400e" }}>{pendingEnrollments.length}</div>
        </div>
        <div style={{ background: "#dbeafe", border: "1px solid #bfdbfe", borderRadius: "0.75rem", padding: "1.5rem" }}>
          <div style={{ fontSize: "0.75rem", color: "#1e40af", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Completed</div>
          <div style={{ fontSize: "2.5rem", fontWeight: 800, color: "#1e40af" }}>{completedEnrollments.length}</div>
        </div>
        <div style={{ background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: "0.75rem", padding: "1.5rem" }}>
          <div style={{ fontSize: "0.75rem", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Email Verified</div>
          <div style={{ fontSize: "2.5rem", fontWeight: 800, color: user.email_verified ? "#166534" : "#92400e" }}>
            {user.email_verified ? "Yes" : "No"}
          </div>
        </div>
      </div>

      <section style={{ marginBottom: "2rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#111827" }}>My Courses</h2>
          <Link href="/courses" style={{ color: "#2563eb", fontWeight: 600, textDecoration: "none", fontSize: "0.875rem" }}>Browse Courses →</Link>
        </div>

        {enrollments.length === 0 ? (
          <div style={{ textAlign: "center", padding: "3rem", background: "#f9fafb", borderRadius: "0.75rem" }}>
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="1.5" style={{ marginBottom: "1rem" }}><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#374151", marginBottom: "0.5rem" }}>No courses yet</h3>
            <p style={{ color: "#6b7280", marginBottom: "1.5rem" }}>Browse our catalogue and start your learning journey</p>
            <Link href="/courses" style={{ display: "inline-block", padding: "0.75rem 1.5rem", background: "#2563eb", color: "#fff", borderRadius: "0.5rem", fontWeight: 600, textDecoration: "none" }}>Browse Courses</Link>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: "1rem" }}>
            {enrollments.map((enrollment) => {
              const badge = getStatusBadge(enrollment.status);
              return (
                <article key={enrollment.id} style={{ border: "1px solid #e5e7eb", borderRadius: "0.75rem", padding: "1.5rem", background: "#fff", display: "flex", flexDirection: "column" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                    <span style={{ background: badge.bg, color: badge.text, fontSize: "0.75rem", fontWeight: 600, padding: "0.25rem 0.625rem", borderRadius: "9999px" }}>{badge.label}</span>
                    <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>{new Date(enrollment.enrolled_at).toLocaleDateString("en-GB")}</span>
                  </div>
                  <h3 style={{ fontSize: "1.125rem", fontWeight: 700, color: "#111827", marginBottom: "0.5rem", flex: 1 }}>Course {enrollment.course_id.slice(0, 8)}</h3>
                  <p style={{ fontSize: "0.875rem", color: "#6b7280", marginBottom: "1rem" }}>Course ID: {enrollment.course_id}</p>
                  <div style={{ display: "flex", gap: "0.5rem", marginTop: "auto" }}>
                    {enrollment.status === "active" && (
                      <Link href={`/courses/${enrollment.course_id}`} style={{ flex: 1, textAlign: "center", padding: "0.625rem 1rem", background: "#2563eb", color: "#fff", borderRadius: "0.5rem", fontWeight: 600, textDecoration: "none" }}>Continue Learning</Link>
                    )}
                    {enrollment.status === "seat_reserved" && (
                      <Link href={`/courses/${enrollment.course_id}`} style={{ flex: 1, textAlign: "center", padding: "0.625rem 1rem", background: "#fef3c7", color: "#92400e", borderRadius: "0.5rem", fontWeight: 600, textDecoration: "none" }}>Complete Payment</Link>
                    )}
                    <Link href={`/courses/${enrollment.course_id}`} style={{ padding: "0.625rem 1rem", background: "#f3f4f6", color: "#374151", border: "1px solid #d1d5db", borderRadius: "0.5rem", fontWeight: 500, textDecoration: "none" }}>Details</Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {!user.email_verified && (
        <div style={{ background: "#fef3c7", border: "1px solid #fde68a", borderRadius: "0.75rem", padding: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ fontWeight: 600, color: "#92400e", marginBottom: "0.25rem" }}>Verify your email</div>
            <p style={{ color: "#92400e", fontSize: "0.875rem", margin: 0 }}>You'll need a verified email to receive course updates and certificates.</p>
          </div>
          <Link href="/auth/verify-email" style={{ background: "#f59e0b", color: "#fff", padding: "0.75rem 1.5rem", borderRadius: "0.5rem", fontWeight: 600, textDecoration: "none" }}>Resend Verification</Link>
        </div>
      )}
    </div>
  );
}