interface StatCardProps {
  label: string;
  value: string;
  detail: string;
}

export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <div className="panel stat-card">
      <span className="eyebrow">{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </div>
  );
}
