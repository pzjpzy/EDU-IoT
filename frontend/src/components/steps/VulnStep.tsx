import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { VulnResult } from '../../api/types'
import ExplanationPanel from '../ExplanationPanel'
import FindingCard from '../FindingCard'

interface Props {
  sessionId: number
  onComplete: (result: VulnResult) => void
}

export default function VulnStep({ sessionId, onComplete }: Props) {
  const [result, setResult] = useState<VulnResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      const res = await api.runVuln(sessionId)
      setResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {result ? <ExplanationPanel explanation={result.explanation} /> : null}

      {!result && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-6 text-center">
          <p className="mb-4 text-slate-300">Ready to analyse your recon data against the OWASP IoT Top 10.</p>
          <button
            onClick={run}
            disabled={loading}
            className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white disabled:opacity-40 hover:bg-sky-500"
          >
            {loading ? 'Analysing...' : 'Identify Vulnerabilities'}
          </button>
        </div>
      )}

      {error && <p className="text-sm text-red-400">{error}</p>}

      {result && (
        <>
          <div className="space-y-3">
            {result.findings.map((f) => (
              <FindingCard key={f.id} finding={f} />
            ))}
            {result.findings.length === 0 && <p className="text-slate-500">No findings derived from recon data.</p>}
          </div>

          <div className="flex gap-3">
            <button
              onClick={run}
              disabled={loading}
              className="rounded-md border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
            >
              Re-analyse
            </button>
            <button
              onClick={() => onComplete(result)}
              className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500"
            >
              Continue to Exploitation
            </button>
          </div>
        </>
      )}
    </div>
  )
}
