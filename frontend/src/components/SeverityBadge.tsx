const COLORS: Record<string, string> = {
  High: 'bg-red-500/20 text-red-300 border-red-500/40',
  Medium: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
  Low: 'bg-lime-500/20 text-lime-300 border-lime-500/40',
}

export default function SeverityBadge({ severity }: { severity: string }) {
  const cls = COLORS[severity] ?? 'bg-slate-500/20 text-slate-300 border-slate-500/40'
  return <span className={`inline-block rounded border px-2 py-0.5 text-xs font-semibold ${cls}`}>{severity}</span>
}
