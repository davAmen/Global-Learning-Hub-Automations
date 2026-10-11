"use client";

import { useEffect, useState } from "react";
import { fetchStudents } from "@/lib/api";
import StudentTable from "@/components/StudentTable";

export default function StudentsPage() {
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadStudents = async () => {
      try {
        const data = await fetchStudents();
        setStudents(data.students || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load students");
        setStudents([]);
      } finally {
        setLoading(false);
      }
    };
    loadStudents();
  }, []);

  if (loading) return <p>Loading...</p>;
  if (error) return <p style={{ color: "#dc2626" }}>{error}</p>;
  return <StudentTable students={students} />;
}