"use client";

import RunJobButton from "@/components/RunJobButton";

export default function RunPage() {
  return (
    <div>
      <h1>Run Daily Job</h1>
      <p>Click the button below to manually trigger today's reminder job.</p>
      <RunJobButton />
    </div>
  );
}
