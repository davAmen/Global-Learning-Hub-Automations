"use client";

import { useEffect, useState } from "react";
import StudentTable from "@/components/StudentTable";

export default function StudentsPage() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/reports/today`)
      .then((r) => r.json())
      .then((data) => setStudents(data.students || []))
      .catch(() => setStudents([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;
  return <StudentTable students={students} />;
}
