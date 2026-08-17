import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { Finding, StageExplanation } from '../../api/types'
import FindingCard from '../FindingCard'

interface Props {
  sessionId: number
  explanation: StageExplanation
  onComplete: () => void
}

export default function ReportStep({ sessionId, explanation, onComplete }: Props) {
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .getFindings(sessionId)
      .then(setFindings)
      .finally(() => setLoading(false))
  }, [sessionId])

  const severityCounts = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.severity] = (acc[f.severity] ?? 0) + 1
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-5 space-y-3">
        <h3 className="text-lg font-semibold text-slate-100">{explanation.title}</h3>
        <p className="text-sm text-slate-300">{explanation.what_the_tool_does}</p>
      </div>

      {loading && <p className="text-slate-400">Loading findings...</p>}

      {!loading && (
        <>
          <div className="flex gap-3 text-sm">
            {(['High', 'Medium', 'Low'] as const).map((sev) => (
              <span key={sev} className="rounded border border-slate-700 bg-slate-800/50 px-3 py-1 text-slate-300">
                {sev}: {severityCounts[sev] ?? 0}
              </span>
            ))}
          </div>

          <div className="space-y-3">
            {findings.map((f) => (
              <FindingCard key={f.id} finding={f} />
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <a
              href={api.reportUrl(sessionId)}
              download={`eduvapt_report_session_${sessionId}.pdf`}
              className="rounded-md bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-500"
            >
              Download PDF Report
            </a>
            <button
              onClick={onComplete}
              className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500"
            >
              Continue to Capstone Challenge
            </button>
          </div>
        </>
      )}
    </div>
  )
}
