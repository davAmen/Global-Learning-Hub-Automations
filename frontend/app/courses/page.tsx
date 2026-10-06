"use client";

import { useEffect, useState } from "react";

export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/courses`)
      .then((r) => r.json())
      .then((data) => setCourses(data.courses || []))
      .catch(() => setCourses([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <h1>Courses</h1>
      {courses.map((c, i) => (
        <div key={i} style={{ border: "1px solid #ccc", padding: "1rem", marginBottom: "1rem" }}>
          <h3>{c.name}</h3>
          <p>Start: {c.start_date} at {c.class_time}</p>
        </div>
      ))}
    </div>
  );
}
