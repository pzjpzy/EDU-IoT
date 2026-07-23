import { useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { ReconResult } from '../../api/types'
import ExplanationPanel from '../ExplanationPanel'

interface Props {
  sessionId: number
  onComplete: (result: ReconResult) => void
}

export default function ReconStep({ sessionId, onComplete }: Props) {
  const [result, setResult] = useState<ReconResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      const res = await api.runRecon(sessionId)
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
          <p className="mb-4 text-slate-300">
            Ready to discover live hosts and scan for open ports/services on your target.
          </p>
          <button
            onClick={run}
            disabled={loading}
            className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white disabled:opacity-40 hover:bg-sky-500"
          >
            {loading ? 'Scanning... (this can take up to ~20s)' : 'Run Reconnaissance'}
          </button>
        </div>
      )}

      {error && <p className="text-sm text-red-400">{error}</p>}

      {result && (
        <>
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <p className="text-sm text-slate-300">
              Host discovery method: <span className="font-mono text-slate-100">{result.discovery_method}</span>{' '}
              &mdash; target is{' '}
              <span className={result.hosts_discovered.length ? 'text-emerald-400' : 'text-red-400'}>
                {result.hosts_discovered.length ? 'alive' : 'not responding'}
              </span>
            </p>
            {result.warning && <p className="mt-1 text-xs text-amber-400">{result.warning}</p>}
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800 text-slate-400">
                <tr>
                  <th className="px-3 py-2">Port</th>
                  <th className="px-3 py-2">State</th>
                  <th className="px-3 py-2">Service</th>
                  <th className="px-3 py-2">Banner</th>
                </tr>
              </thead>
              <tbody>
                {result.ports.map((p) => (
                  <tr key={`${p.protocol}-${p.port}`} className="border-t border-slate-700">
                    <td className="px-3 py-2 font-mono">
                      {p.port}/{p.protocol}
                    </td>
                    <td className="px-3 py-2">{p.state}</td>
                    <td className="px-3 py-2">{p.service}</td>
                    <td className="max-w-md truncate px-3 py-2 text-slate-400" title={p.banner}>
                      {p.banner || '-'}
                    </td>
                  </tr>
                ))}
                {result.ports.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-3 py-4 text-center text-slate-500">
                      No open ports found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex gap-3">
            <button
              onClick={run}
              disabled={loading}
              className="rounded-md border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
            >
              Re-scan
            </button>
            <button
              onClick={() => onComplete(result)}
              className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500"
            >
              Continue to Vulnerability ID
            </button>
          </div>
        </>
      )}
    </div>
  )
}
