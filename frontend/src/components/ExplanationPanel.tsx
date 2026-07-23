import type { StageExplanation } from '../api/types'

export default function ExplanationPanel({ explanation }: { explanation: StageExplanation }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-5 space-y-3">
      <h3 className="text-lg font-semibold text-slate-100">{explanation.title}</h3>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-sky-400">What</p>
        <p className="text-sm text-slate-300">{explanation.what}</p>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-sky-400">Why it matters</p>
        <p className="text-sm text-slate-300">{explanation.why}</p>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-sky-400">What this tool does</p>
        <p className="text-sm text-slate-300">{explanation.what_the_tool_does}</p>
      </div>
    </div>
  )
}
