import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { TargetProfile, TaskItem } from '../../api/types'
import TaskCard from '../TaskCard'
import TerminalPanel from '../TerminalPanel'

interface Props {
  sessionId: number
  targetIp: string
  onAllComplete: () => void
}

const HARDENED_LABELS: Record<keyof TargetProfile, string> = {
  http_default_creds_vulnerable: 'HTTP admin default credentials',
  snapshot_unauth_vulnerable: 'Unauthenticated snapshot access',
  telnet_enabled: 'Telnet service (disabled entirely)',
  telnet_default_creds_vulnerable: 'Telnet default credentials',
  rtsp_enabled: 'RTSP service (disabled entirely)',
}

export default function TasksStep({ sessionId, targetIp, onAllComplete }: Props) {
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [profile, setProfile] = useState<TargetProfile | null>(null)
  const [warning, setWarning] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [terminalOpen, setTerminalOpen] = useState(false)

  const reload = useCallback(() => {
    return api.listTasks(sessionId).then((board) => {
      setTasks(board.tasks)
      setProfile(board.profile)
      setWarning(board.warning)
    })
  }, [sessionId])

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [reload])

  const completedCount = tasks.filter((t) => t.completed).length
  const allComplete = completedCount === tasks.length

  const hardenedAgainst = profile
    ? (Object.keys(HARDENED_LABELS) as (keyof TargetProfile)[])
        .filter((key) => !profile[key] && !(key === 'telnet_default_creds_vulnerable' && !profile.telnet_enabled))
        .map((key) => HARDENED_LABELS[key])
    : []

  if (loading) return <p className="text-slate-400">Loading tasks...</p>

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-sky-600/40 bg-sky-500/10 p-4 text-sm text-slate-200">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span>
            Point your own tools at target <span className="font-mono font-semibold">{targetIp}</span> - Nmap, a
            browser, a Telnet client, netcat/ncat. Work through the tasks below in order; each one tells you what
            to try.
          </span>
          <button
            onClick={() => setTerminalOpen((v) => !v)}
            className="whitespace-nowrap rounded-md border border-sky-500 px-3 py-1.5 text-xs font-medium text-sky-300 hover:bg-sky-500/20"
          >
            {terminalOpen ? 'Hide Terminal' : 'Open Terminal'}
          </button>
        </div>
      </div>

      {warning && <p className="text-sm text-amber-400">{warning}</p>}

      {!warning && hardenedAgainst.length > 0 && (
        <div className="rounded-lg border border-emerald-600/40 bg-emerald-500/10 p-3 text-sm text-emerald-200">
          This target has already been hardened against: {hardenedAgainst.join(', ')}. The challenge list below only
          includes weaknesses this specific target actually has.
        </div>
      )}

      {terminalOpen && <TerminalPanel onClose={() => setTerminalOpen(false)} />}

      <div className="flex items-center gap-3">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
          <div
            className="h-full bg-emerald-500 transition-all"
            style={{ width: `${tasks.length ? (completedCount / tasks.length) * 100 : 0}%` }}
          />
        </div>
        <span className="whitespace-nowrap text-sm text-slate-400">
          {completedCount} / {tasks.length} complete
        </span>
      </div>

      <div className="space-y-4">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} sessionId={sessionId} onCompleted={reload} />
        ))}
        {tasks.length === 0 && (
          <p className="text-slate-500">
            No applicable challenges were found for this target - it may be fully hardened, or its profile
            couldn't be read.
          </p>
        )}
      </div>

      <button
        onClick={onAllComplete}
        disabled={!allComplete}
        className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white disabled:opacity-40 hover:bg-sky-500"
      >
        Continue to Report
      </button>
    </div>
  )
}
