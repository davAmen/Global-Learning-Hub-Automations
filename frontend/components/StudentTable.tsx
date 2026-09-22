export default function StudentTable({ students }: { students: any[] }) {
  if (!students.length) return <p>No students found.</p>;
  return (
    <table border={1} cellPadding={8}>
      <thead>
        <tr><th>Name</th><th>Phone</th><th>Email</th></tr>
      </thead>
      <tbody>
        {students.map((s, i) => (
          <tr key={i}><td>{s.name}</td><td>{s.phone}</td><td>{s.email}</td></tr>
        ))}
      </tbody>
    </table>
  );
}
