import type { Finding } from '../api/types'
import SeverityBadge from './SeverityBadge'

export default function FindingCard({ finding }: { finding: Finding }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-medium text-slate-100">{finding.title}</h4>
        <div className="flex items-center gap-2 shrink-0">
          <span className="rounded border border-slate-600 px-2 py-0.5 text-xs text-slate-300">
            OWASP {finding.owasp_id}
          </span>
          <SeverityBadge severity={finding.severity} />
        </div>
      </div>
      <p className="text-sm text-slate-400">
        <span className="font-semibold text-slate-300">Evidence: </span>
        {finding.evidence}
      </p>
      <p className="text-sm text-slate-400">
        <span className="font-semibold text-slate-300">Mitigation: </span>
        {finding.mitigation}
      </p>
    </div>
  )
}
