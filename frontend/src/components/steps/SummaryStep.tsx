import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import type { SessionSummary } from '../../api/types'

interface Props {
  sessionId: number
}

const CAPSTONE_LABEL: Record<string, string> = {
  completed: 'Completed',
  gave_up: 'Gave up (partial)',
  skipped: 'Skipped',
  in_progress: 'In progress',
  not_started: 'Not started',
}

const SEVERITY_STYLE: Record<string, string> = {
  High: 'border-red-600/50 bg-red-500/10 text-red-300',
  Medium: 'border-amber-600/50 bg-amber-500/10 text-amber-300',
  Low: 'border-lime-600/50 bg-lime-500/10 text-lime-300',
}

/** End-of-session dashboard: quiz accuracy, vulnerabilities by severity,
 * capstone outcome, and the report download. Reachable again by reopening a
 * finished session (the wizard restores to this phase). */
export default function SummaryStep({ sessionId }: Props) {
  const [summary, setSummary] = useState<SessionSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getSummary(sessionId)
      .then(setSummary)
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) return <p className="text-slate-400">Loading summary...</p>
  if (!summary) return <p className="text-red-400">Could not load the session summary.</p>

  const pre = summary.pre_quiz
  const prePct = pre && pre.total ? Math.round((pre.score / pre.total) * 100) : null
  const cap = summary.capstone
  const capPct = cap.score != null && cap.total ? Math.round((cap.score / cap.total) * 100) : null
  const sev = summary.findings_by_severity

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-emerald-600/40 bg-emerald-500/10 p-5">
        <h2 className="text-xl font-semibold text-emerald-300">Session summary</h2>
        <p className="text-sm text-slate-300">
          Everything you achieved this session, at a glance. Use the phase stepper above to revisit any step.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Quiz accuracy */}
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-5">
          <p className="text-sm text-slate-400">Pre-session quiz accuracy</p>
          {pre ? (
            <p className="mt-1 text-3xl font-bold text-slate-100">
              {prePct}% <span className="text-base font-normal text-slate-500">({pre.score}/{pre.total})</span>
            </p>
          ) : (
            <p className="mt-1 text-slate-500">Not taken</p>
          )}
        </div>

        {/* Capstone score */}
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-5">
          <p className="text-sm text-slate-400">Capstone (unguided) result</p>
          <p className="mt-1 text-3xl font-bold text-slate-100">
            {cap.score != null && cap.total != null ? (
              <>
                {cap.score}/{cap.total}
                {capPct != null && <span className="text-base font-normal text-slate-500"> ({capPct}%)</span>}
              </>
            ) : (
              <span className="text-slate-500">-</span>
            )}
          </p>
          <p className="mt-1 text-xs text-slate-400">Status: {CAPSTONE_LABEL[cap.status] ?? cap.status}</p>
        </div>
      </div>

      {/* Vulnerabilities by severity */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-5 space-y-3">
        <div className="flex items-baseline justify-between">
          <p className="text-sm text-slate-400">Vulnerabilities confirmed</p>
          <p className="text-2xl font-bold text-slate-100">{summary.findings_total}</p>
        </div>
        <div className="flex flex-wrap gap-3">
          {(['High', 'Medium', 'Low'] as const).map((s) => (
            <span
              key={s}
              className={`rounded-md border px-3 py-1.5 text-sm font-medium ${SEVERITY_STYLE[s]}`}
            >
              {s}: {sev[s]}
            </span>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        <a
          href={api.reportUrl(sessionId)}
          download={`eduvapt_report_session_${sessionId}.pdf`}
          className="rounded-md bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-500"
        >
          Download PDF Report
        </a>
        <Link
          to="/dashboard"
          className="rounded-md border border-slate-600 px-4 py-2 font-medium text-slate-300 hover:bg-slate-800"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  )
}
