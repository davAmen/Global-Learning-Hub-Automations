"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchCourses } from "@/lib/api";

export const dynamic = "force-dynamic";

interface Course {
  id: string;
  name: string;
  description?: string;
  start_date?: string;
  class_time?: string;
  timezone?: string;
  price_minor: number;
  currency: string;
  capacity?: number;
  seat_reservation_minor: number;
  expected_study_hours?: number;
  learning_outcomes: string[];
  prerequisites: string[];
  support_email?: string;
  support_phone?: string;
  is_active: boolean;
}

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const data = await fetchCourses();
        setCourses(data.courses || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load courses");
      } finally {
        setLoading(false);
      }
    };
    loadCourses();
  }, []);

  const formatPrice = (minor: number, currency: string) => {
    const major = (minor / 100).toFixed(2);
    const symbols: Record<string, string> = { GHS: "₵", USD: "$", EUR: "€" };
    return `${symbols[currency] || currency} ${major}`;
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "3rem" }}>
        <div style={{ display: "inline-block", width: "2rem", height: "2rem", border: "3px solid #e5e7eb", borderTopColor: "#2563eb", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
        <style jsx>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <p style={{ marginTop: "1rem", color: "#6b7280" }}>Loading courses...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: "center", padding: "3rem", color: "#dc2626" }}>
        <h2>Unable to load courses</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()} style={{ marginTop: "1rem", padding: "0.5rem 1rem", background: "#2563eb", color: "#fff", border: "none", borderRadius: "0.375rem", cursor: "pointer" }}>Retry</button>
      </div>
    );
  }

  const activeCourses = courses.filter(c => c.is_active);

  if (activeCourses.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "3rem" }}>
        <h1>No courses available</h1>
        <p style={{ color: "#6b7280" }}>Check back soon for new courses.</p>
      </div>
    );
  }

  return (
    <div>
      <header style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "#111827", marginBottom: "0.5rem" }}>Course Catalogue</h1>
        <p style={{ color: "#6b7280", fontSize: "1.125rem" }}>Browse available courses and start learning today</p>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1.5rem" }}>
        {activeCourses.map((course) => (
          <Link key={course.id} href={`/courses/${course.id}`} style={{ textDecoration: "none", color: "inherit" }}>
            <article style={{ border: "1px solid #e5e7eb", borderRadius: "0.75rem", padding: "1.5rem", background: "#fff", boxShadow: "0 1px 3px rgba(0,0,0,0.05)", transition: "box-shadow 0.2s, transform 0.2s", display: "flex", flexDirection: "column", height: "100%" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#111827", lineHeight: 1.3 }}>{course.name}</h2>
                <span style={{ background: "#dcfce7", color: "#166534", fontSize: "0.75rem", fontWeight: 600, padding: "0.25rem 0.625rem", borderRadius: "9999px", whiteSpace: "nowrap" }}>Active</span>
              </div>

              {course.description && (
                <p style={{ color: "#4b5563", fontSize: "0.9375rem", lineHeight: 1.6, marginBottom: "1rem", flex: 1 }}>{course.description}</p>
              )}

              <div style={{ borderTop: "1px solid #f3f4f6", paddingTop: "1rem", marginBottom: "1rem" }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.75rem" }}>
                  {course.start_date && (
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#4b5563", fontSize: "0.875rem" }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "#9ca3af" }}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                      <span>{new Date(course.start_date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</span>
                    </div>
                  )}
                  {course.class_time && (
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#4b5563", fontSize: "0.875rem" }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "#9ca3af" }}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                      <span>{course.class_time} {course.timezone || "GMT"}</span>
                    </div>
                  )}
                  {course.expected_study_hours && (
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#4b5563", fontSize: "0.875rem" }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "#9ca3af" }}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                      <span>{course.expected_study_hours} hrs</span>
                    </div>
                  )}
                  {course.capacity && (
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#4b5563", fontSize: "0.875rem" }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ color: "#9ca3af" }}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                      <span>Max {course.capacity}</span>
                    </div>
                  )}
                </div>
              </div>

              <div style={{ borderTop: "1px solid #f3f4f6", paddingTop: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ textAlign: "left" }}>
                  <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>Tuition</div>
                  <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#111827" }}>{formatPrice(course.price_minor, course.currency)}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "0.75rem", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>Seat Reservation</div>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#2563eb" }}>{formatPrice(course.seat_reservation_minor, course.currency)}</div>
                </div>
              </div>
            </article>
          </Link>
        ))}
      </div>

      {activeCourses.length === 0 && (
        <p style={{ textAlign: "center", color: "#6b7280", padding: "2rem" }}>No courses available at the moment.</p>
      )}
    </div>
  );
}