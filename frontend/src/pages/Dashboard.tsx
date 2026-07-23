import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { VaptSession } from '../api/types'

export default function Dashboard() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<VaptSession[]>([])
  const [name, setName] = useState('')
  const [targetIp, setTargetIp] = useState('127.0.0.1')
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  function reload() {
    api.listSessions().then(setSessions).catch(() => {})
  }

  useEffect(reload, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setCreating(true)
    try {
      const session = await api.createSession(name || 'Untitled Session', targetIp)
      navigate(`/sessions/${session.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-10 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">EduVAPT-IoT Dashboard</h1>
        <p className="text-slate-400">Start a new guided VAPT session, or resume an existing one.</p>
      </div>

      <form onSubmit={handleCreate} className="rounded-lg border border-slate-700 bg-slate-800/50 p-5 space-y-4">
        <h2 className="font-semibold text-slate-100">New session</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm text-slate-300">
            Session name
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. CAM-01 Assessment"
              className="mt-1 w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </label>
          <label className="text-sm text-slate-300">
            Target IP (your lab camera / GNS3 node)
            <input
              value={targetIp}
              onChange={(e) => setTargetIp(e.target.value)}
              placeholder="127.0.0.1"
              className="mt-1 w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </label>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={creating}
          className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white disabled:opacity-40 hover:bg-sky-500"
        >
          {creating ? 'Creating...' : 'Start guided session'}
        </button>
      </form>

      <div>
        <h2 className="mb-3 font-semibold text-slate-100">Existing sessions</h2>
        <div className="space-y-2">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => navigate(`/sessions/${s.id}`)}
              className="flex w-full items-center justify-between rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 text-left hover:border-sky-500"
            >
              <div>
                <p className="font-medium text-slate-100">{s.name}</p>
                <p className="text-xs text-slate-500">
                  {s.target_ip} &middot; {new Date(s.created_at).toLocaleString()}
                </p>
              </div>
              <span className="text-slate-500">&rarr;</span>
            </button>
          ))}
          {sessions.length === 0 && <p className="text-slate-500">No sessions yet.</p>}
        </div>
      </div>
    </div>
  )
}
