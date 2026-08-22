import type { VulnBucket } from '../api/types'

const SEVERITIES = [
  { key: 'High', cls: 'bg-red-500' },
  { key: 'Medium', cls: 'bg-amber-500' },
  { key: 'Low', cls: 'bg-lime-500' },
] as const

const BAR_AREA_PX = 150

/** Stacked bar chart of vulnerabilities per time bucket, coloured by severity.
 * Plain flex/divs (no charting dependency), matching the app's Tailwind style. */
export default function VulnBarChart({ data }: { data: VulnBucket[] }) {
  const max = Math.max(1, ...data.map((d) => d.High + d.Medium + d.Low))

  return (
    <div className="flex items-end gap-2" style={{ height: BAR_AREA_PX + 22 }}>
      {data.map((d, i) => {
        const total = d.High + d.Medium + d.Low
        return (
          <div key={i} className="flex flex-1 flex-col items-center gap-1">
            <span className="text-[11px] tabular-nums text-slate-500">{total || ''}</span>
            <div
              className="flex w-3/5 flex-col justify-end gap-0.5"
              style={{ height: BAR_AREA_PX }}
              title={`${d.bucket}: ${d.High} High, ${d.Medium} Medium, ${d.Low} Low`}
            >
              {SEVERITIES.map((s) => {
                const value = d[s.key]
                if (!value) return null
                return (
                  <div
                    key={s.key}
                    className={`${s.cls} rounded-sm`}
                    style={{ height: (value / max) * BAR_AREA_PX }}
                  />
                )
              })}
            </div>
            <span className="text-[11px] text-slate-500">{d.bucket}</span>
          </div>
        )
      })}
      {data.length === 0 && <p className="text-sm text-slate-500">No vulnerabilities recorded yet.</p>}
    </div>
  )
}
