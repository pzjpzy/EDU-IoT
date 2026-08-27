import { useEffect, useState } from 'react'
import { api, ApiError } from '../../api/client'
import type { ScanResult, ScanService, StageExplanation } from '../../api/types'

interface Props {
  sessionId: number
  targetIp: string
  explanation: StageExplanation
  onComplete: () => void
}

const SEVERITY_CLASSES: Record<string, string> = {
  High: 'border-red-600/50 bg-red-500/10 text-red-300',
  Medium: 'border-amber-600/50 bg-amber-500/10 text-amber-300',
  Low: 'border-lime-600/50 bg-lime-500/10 text-lime-300',
}

function ServiceCard({ svc }: { svc: ScanService }) {
  const sev = SEVERITY_CLASSES[svc.severity_hint] ?? 'border-slate-600 bg-slate-800/50 text-slate-300'
  const banner = svc.version || svc.banner
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="font-semibold text-slate-100">
          <span className="font-mono text-sky-300">{svc.port}</span>/tcp &middot;{' '}
          <span className="uppercase tracking-wide">{svc.protocol}</span>
        </h4>
        <div className="flex items-center gap-2 text-xs">
          <span className="rounded border border-slate-600 px-2 py-0.5 text-slate-300">OWASP {svc.owasp_id}</span>
          <span className={`rounded border px-2 py-0.5 font-medium ${sev}`}>{svc.severity_hint} (hint)</span>
        </div>
      </div>
      <p className="text-sm text-slate-200">{svc.observation}</p>
      <p className="text-sm text-slate-400">
        <span className="font-medium text-slate-300">Why it matters: </span>
        {svc.why_it_matters}
      </p>
      {banner && (
        <p className="text-xs text-slate-500">
          <span className="font-medium">Banner / version: </span>
          <span className="font-mono">{banner}</span>
        </p>
      )}
      <p className="text-xs text-sky-400">
        <span className="font-medium">Reproduce it yourself: </span>
        {svc.reproduce}
      </p>
    </div>
  )
}

export default function ReconStep({ sessionId, targetIp, explanation, onComplete }: Props) {
  const [scan, setScan] = useState<ScanResult | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // If a scan was already run for this session (e.g. the student came back to
  // this step), show the stored result rather than forcing a re-scan.
  useEffect(() => {
    api
      .getScan(sessionId)
      .then(setScan)
      .catch((err) => {
        // 404 just means "no scan yet" - not an error worth showing.
        if (!(err instanceof ApiError && err.status === 404)) setError(String(err))
      })
  }, [sessionId])

  async function handleScan() {
    setRunning(true)
    setError(null)
    try {
      setScan(await api.runScan(sessionId))
    } catch (err) {
      setError(String(err))
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-5 space-y-3">
        <h3 className="text-lg font-semibold text-slate-100">{explanation.title}</h3>
        <p className="text-sm text-slate-300">{explanation.what}</p>
        <p className="text-sm text-slate-400">{explanation.why}</p>
        <p className="text-sm text-slate-300">{explanation.what_the_tool_does}</p>
      </div>

      <div className="rounded-lg border border-sky-600/40 bg-sky-500/10 p-4 text-sm text-slate-200">
        The tool will run an automated recon sweep against{' '}
        <span className="font-mono font-semibold">{targetIp}</span> - a scoped TCP port scan plus protocol
        banner grabbing of the services an IP camera typically exposes. It only observes; you'll confirm the
        exploitable weaknesses yourself in the next step.
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {!scan && (
        <button
          onClick={handleScan}
          disabled={running}
          className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white disabled:opacity-40 hover:bg-sky-500"
        >
          {running ? 'Scanning...' : 'Run automated recon scan'}
        </button>
      )}

      {scan && (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-300">{scan.summary}</p>
            <button
              onClick={handleScan}
              disabled={running}
              className="whitespace-nowrap rounded-md border border-slate-600 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40 hover:bg-slate-800"
            >
              {running ? 'Re-scanning...' : 'Re-run scan'}
            </button>
          </div>

          <div className="space-y-3">
            {scan.services.map((svc) => (
              <ServiceCard key={`${svc.port}-${svc.protocol}`} svc={svc} />
            ))}
          </div>

          <details className="text-xs text-slate-500">
            <summary className="cursor-pointer hover:text-slate-300">
              Scan engine details ({scan.ports_scanned} ports scanned in {scan.duration_seconds}s)
            </summary>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {scan.engine_notes.map((note, i) => (
                <li key={i} className="font-mono">
                  {note}
                </li>
              ))}
            </ul>
          </details>

          {scan.open_ports.length === 0 && (
            <p className="text-sm text-amber-400">
              No open services were found, so there's nothing to assess yet. Check the target is running and
              reachable, then re-run the scan before continuing.
            </p>
          )}

          <button
            onClick={onComplete}
            disabled={scan.open_ports.length === 0}
            className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-sky-500"
          >
            Continue to Challenges
          </button>
        </>
      )}
    </div>
  )
}
