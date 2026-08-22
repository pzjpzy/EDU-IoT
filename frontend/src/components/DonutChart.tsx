interface Props {
  /** 0-100 */
  pct: number
  size?: number
  label?: string
}

/** A hollow (donut) gauge showing a single percentage in its center.
 * Hand-rolled SVG so the dashboard needs no charting dependency. */
export default function DonutChart({ pct, size = 104, label }: Props) {
  const clamped = Math.max(0, Math.min(100, pct))
  const r = 46
  const circumference = 2 * Math.PI * r
  const offset = circumference * (1 - clamped / 100)

  return (
    <svg width={size} height={size} viewBox="0 0 120 120" role="img" aria-label={label ?? `${clamped}%`}>
      <circle cx="60" cy="60" r={r} fill="none" stroke="#334155" strokeWidth="13" />
      <circle
        cx="60"
        cy="60"
        r={r}
        fill="none"
        stroke="#10b981"
        strokeWidth="13"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90 60 60)"
      />
      <text x="60" y="68" textAnchor="middle" fontSize="27" fontWeight="600" fill="#e2e8f0">
        {clamped}%
      </text>
    </svg>
  )
}
