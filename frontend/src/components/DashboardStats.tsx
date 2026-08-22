import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { StatsOverview, VulnBucket, VulnGranularity } from '../api/types'
import DonutChart from './DonutChart'
import VulnBarChart from './VulnBarChart'

const GRANULARITIES: { key: VulnGranularity; label: string }[] = [
  { key: 'day', label: 'Day' },
  { key: 'week', label: 'Week' },
  { key: 'month', label: 'Month' },
]

const LEGEND = [
  { label: 'High', cls: 'bg-red-500' },
  { label: 'Medium', cls: 'bg-amber-500' },
  { label: 'Low', cls: 'bg-lime-500' },
]

/** The dashboard analytics strip: CCTV scanned this month, overall quiz
 * accuracy (donut), and a severity-coloured vulnerability bar chart with a
 * day/week/month toggle. Everything else on the dashboard is unchanged. */
export default function DashboardStats() {
  const [overview, setOverview] = useState<StatsOverview | null>(null)
  const [granularity, setGranularity] = useState<VulnGranularity>('week')
  const [buckets, setBuckets] = useState<VulnBucket[]>([])

  useEffect(() => {
    api.getStatsOverview().then(setOverview).catch(() => {})
  }, [])

  useEffect(() => {
    api.getVulnStats(granularity).then(setBuckets).catch(() => {})
  }, [granularity])

  const periodTotal = buckets.reduce((acc, b) => acc + b.High + b.Medium + b.Low, 0)

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="flex items-center gap-4 rounded-xl border border-slate-700 bg-slate-800/50 p-5">
          <div className="text-3xl">📷</div>
          <div>
            <p className="text-3xl font-bold text-slate-100">{overview?.cctv_scanned_this_month ?? '-'}</p>
            <p className="text-xs text-slate-400">CCTV scanned this month</p>
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-xl border border-slate-700 bg-slate-800/50 p-5">
          <DonutChart pct={overview?.quiz_accuracy.pct ?? 0} label="Overall quiz accuracy" />
          <div>
            <p className="text-xs text-slate-400">Overall quiz accuracy</p>
            {overview && (
              <p className="text-xs text-slate-500">
                {overview.quiz_accuracy.correct}/{overview.quiz_accuracy.total} correct
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 rounded-xl border border-slate-700 bg-slate-800/50 p-5">
          <div className="text-3xl text-red-400">⚠</div>
          <div>
            <p className="text-3xl font-bold text-slate-100">{overview?.vulns_all_time ?? '-'}</p>
            <p className="text-xs text-slate-400">Vulnerabilities found (all time)</p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-semibold text-slate-100">Vulnerabilities found</h2>
            <p className="text-xs text-slate-400">{periodTotal} in the selected period</p>
          </div>
          <div className="inline-flex overflow-hidden rounded-md border border-slate-600">
            {GRANULARITIES.map((g) => (
              <button
                key={g.key}
                onClick={() => setGranularity(g.key)}
                className={
                  'px-3 py-1.5 text-sm ' +
                  (granularity === g.key
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700')
                }
              >
                {g.label}
              </button>
            ))}
          </div>
        </div>

        <VulnBarChart data={buckets} />

        <div className="mt-4 flex gap-5">
          {LEGEND.map((l) => (
            <span key={l.label} className="flex items-center gap-2 text-xs text-slate-400">
              <span className={`h-3 w-3 rounded-sm ${l.cls}`} />
              {l.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
