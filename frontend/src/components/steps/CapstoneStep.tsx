import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import type { CapstoneBoard, CapstoneObjective } from '../../api/types'
import TerminalPanel from '../TerminalPanel'

interface Props {
  sessionId: number
  preQuiz?: { score: number; total: number } | null
  onComplete: () => void
}

const DEFAULT_CAPSTONE_IP = '192.168.56.52'

/**
 * The capstone challenge replaces the old post-session quiz. The student is
 * handed a SECOND, unseen camera and must recon + exploit it with no
 * step-by-step guidance - objectives show a goal only, no hints or concept
 * panels. The number completed is the learning-effectiveness signal.
 */
export default function CapstoneStep({ sessionId, preQuiz, onComplete }: Props) {
  const [capstoneIp, setCapstoneIp] = useState(DEFAULT_CAPSTONE_IP)
  const [started, setStarted] = useState(false)
  const [board, setBoard] = useState<CapstoneBoard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [terminalOpen, setTerminalOpen] = useState(true)

  const reload = useCallback(() => {
    return api
      .capstoneBoard(sessionId, capstoneIp)
      .then(setBoard)
      .catch((err) => setError(String(err)))
  }, [sessionId, capstoneIp])

  async function handleStart() {
    setError(null)
    try {
      const b = await api.capstoneBoard(sessionId, capstoneIp)
      setBoard(b)
      setStarted(true)
    } catch (err) {
      setError(String(err))
    }
  }

  async function finishWith(status: 'completed' | 'gave_up' | 'skipped') {
    try {
      await api.setCapstoneStatus(sessionId, status)
    } catch {
      // Non-fatal: the summary still renders from whatever was recorded.
    }
    onComplete()
  }

  if (!started) {
    return (
      <div className="space-y-6">
        <div className="rounded-lg border border-amber-600/40 bg-amber-500/10 p-5 space-y-3">
          <h3 className="text-lg font-semibold text-amber-200">Final challenge - on your own</h3>
          <p className="text-sm text-slate-300">
            One last target: a different camera you haven't seen, running its own mix of weaknesses. This time
            there are <span className="font-semibold">no hints, no concept panels, and no set order</span> - just
            objectives. Recon it and exploit what you can, using the same tools and techniques from the guided
            room. How many you complete on your own is the real measure of what you learned.
          </p>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 space-y-3">
          <label className="block text-sm text-slate-300">
            Capstone target IP
            <input
              value={capstoneIp}
              onChange={(e) => setCapstoneIp(e.target.value)}
              className="mt-1 block w-48 rounded-md border border-slate-600 bg-slate-900 px-3 py-1.5 font-mono text-sm text-slate-100"
            />
          </label>
          <p className="text-xs text-slate-500">
            Start the capstone target first (see <span className="font-mono">capstone/docker-compose.yml</span>,
            or its node in your GNS3 lab). It must be inside the configured lab scope.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleStart}
              className="rounded-md bg-amber-600 px-4 py-2 font-medium text-white hover:bg-amber-500"
            >
              Start the challenge
            </button>
            <button
              onClick={() => finishWith('skipped')}
              className="rounded-md border border-slate-600 px-4 py-2 font-medium text-slate-300 hover:bg-slate-800"
            >
              Skip capstone
            </button>
          </div>
        </div>
      </div>
    )
  }

  const objectives = board?.objectives ?? []
  const completed = board?.score ?? objectives.filter((o) => o.completed).length
  const total = board?.total ?? objectives.length
  const allDone = total > 0 && completed === total

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-amber-600/40 bg-amber-500/10 p-4 text-sm text-slate-200">
        Attack target <span className="font-mono font-semibold">{capstoneIp}</span> with your own tools. No hints
        this time - the objectives below just tell you the goal.
      </div>

      {board?.warning && (
        <p className="text-sm text-amber-400">
          {board.warning} (Is the capstone target running at {capstoneIp}?)
        </p>
      )}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="flex items-center justify-between">
        <button
          onClick={() => setTerminalOpen((v) => !v)}
          className="rounded-md border border-sky-500 px-3 py-1.5 text-xs font-medium text-sky-300 hover:bg-sky-500/20"
        >
          {terminalOpen ? 'Hide Terminal' : 'Open Terminal'}
        </button>
        <span className="text-sm text-slate-400">
          {completed} / {total} objectives
        </span>
      </div>

      {terminalOpen && <TerminalPanel onClose={() => setTerminalOpen(false)} />}

      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full bg-amber-500 transition-all"
          style={{ width: `${total ? (completed / total) * 100 : 0}%` }}
        />
      </div>

      <div className="space-y-3">
        {objectives.map((obj) => (
          <CapstoneObjectiveCard
            key={obj.id}
            objective={obj}
            sessionId={sessionId}
            capstoneIp={capstoneIp}
            onCompleted={reload}
          />
        ))}
        {objectives.length === 0 && !board?.warning && (
          <p className="text-slate-500">
            No objectives apply to this capstone target - it may be fully hardened. Pick a target with at least one
            weakness enabled.
          </p>
        )}
      </div>

      {allDone && (
        <div className="rounded-lg border border-emerald-600/40 bg-emerald-500/10 p-4 text-sm text-emerald-200">
          You cleared every objective on a target you'd never seen, unaided - that's the transfer from guided
          learning to hands-on skill.
        </div>
      )}

      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 text-sm text-slate-300">
        <span className="font-semibold text-slate-100">
          Result: {completed} / {total} exploited independently
        </span>
        {preQuiz && (
          <span className="text-slate-400">
            {' '}
            (pre-session knowledge check: {preQuiz.score} / {preQuiz.total})
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        {allDone ? (
          <button
            onClick={() => finishWith('completed')}
            className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500"
          >
            Finish session
          </button>
        ) : (
          <button
            onClick={() => finishWith('gave_up')}
            className="rounded-md border border-amber-600/60 px-4 py-2 font-medium text-amber-300 hover:bg-amber-500/10"
          >
            Give up &amp; see results ({completed}/{total})
          </button>
        )}
      </div>
    </div>
  )
}

function CapstoneObjectiveCard({
  objective,
  sessionId,
  capstoneIp,
  onCompleted,
}: {
  objective: CapstoneObjective
  sessionId: number
  capstoneIp: string
  onCompleted: () => void
}) {
  const [answer, setAnswer] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)

  const runCheck = useCallback(
    async (manual: boolean) => {
      setBusy(true)
      try {
        const res = await api.checkCapstone(sessionId, objective.id, capstoneIp)
        if (res.completed) {
          setMessage(null)
          onCompleted()
        } else if (manual) {
          setMessage(res.error ?? 'Not detected yet - go try it, then check again.')
        }
      } catch (err) {
        if (manual) setMessage(String(err))
      } finally {
        setBusy(false)
      }
    },
    [sessionId, objective.id, capstoneIp, onCompleted],
  )

  useEffect(() => {
    if (objective.type !== 'auto' || objective.completed) return
    pollRef.current = window.setInterval(() => runCheck(false), 4000)
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
  }, [objective.type, objective.completed, runCheck])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setMessage(null)
    try {
      const res = await api.submitCapstone(sessionId, objective.id, capstoneIp, answer)
      if (res.correct) {
        onCompleted()
      } else {
        setMessage(res.error ?? 'Not quite - keep trying.')
      }
    } catch (err) {
      setMessage(String(err))
    } finally {
      setBusy(false)
    }
  }

  const stateClasses = objective.completed
    ? 'border-emerald-600/50 bg-emerald-500/10'
    : 'border-slate-700 bg-slate-800/50'

  return (
    <div className={`rounded-lg border p-4 space-y-3 ${stateClasses}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="font-semibold text-slate-100">{objective.title}</h4>
        <div className="flex items-center gap-2">
          <span className="rounded border border-slate-600 px-2 py-0.5 text-xs text-slate-300">
            OWASP {objective.owasp_id}
          </span>
          {objective.completed && (
            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-300">
              Done
            </span>
          )}
        </div>
      </div>

      {!objective.completed && objective.type === 'auto' && (
        <div className="flex items-center gap-3">
          <button
            onClick={() => runCheck(true)}
            disabled={busy}
            className="rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-40 hover:bg-sky-500"
          >
            {busy ? 'Checking...' : 'Check progress'}
          </button>
          <span className="text-xs text-slate-500">Auto-checking every few seconds...</span>
        </div>
      )}

      {!objective.completed && objective.type === 'submit' && (
        <form onSubmit={handleSubmit} className="flex flex-wrap items-center gap-2">
          <input
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Your answer / flag"
            className="min-w-0 flex-1 rounded-md border border-slate-600 bg-slate-900 px-3 py-1.5 text-sm text-slate-100"
          />
          <button
            type="submit"
            disabled={busy || !answer.trim()}
            className="rounded-md bg-sky-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-40 hover:bg-sky-500"
          >
            Submit
          </button>
        </form>
      )}

      {message && <p className="text-xs text-amber-400">{message}</p>}
    </div>
  )
}
