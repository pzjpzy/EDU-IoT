import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { TaskItem } from '../api/types'

interface Props {
  task: TaskItem
  sessionId: number
  onCompleted: () => void
}

export default function TaskCard({ task, sessionId, onCompleted }: Props) {
  const [showHint, setShowHint] = useState(false)
  const [showConcept, setShowConcept] = useState(false)
  const [answer, setAnswer] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const pollRef = useRef<number | null>(null)

  const active = !task.locked && !task.completed

  async function runCheck(manual: boolean) {
    setBusy(true)
    try {
      const res = await api.checkTask(sessionId, task.id)
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
  }

  useEffect(() => {
    if (task.type !== 'auto' || !active) return
    pollRef.current = window.setInterval(() => runCheck(false), 4000)
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [task.type, active, task.id])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setMessage(null)
    try {
      const res = await api.submitTask(sessionId, task.id, answer)
      if (res.correct) {
        onCompleted()
      } else {
        setMessage(res.error ?? 'Not quite - check the hint and try again.')
      }
    } catch (err) {
      setMessage(String(err))
    } finally {
      setBusy(false)
    }
  }

  const stateClasses = task.completed
    ? 'border-emerald-600/50 bg-emerald-500/10'
    : task.locked
      ? 'border-slate-800 bg-slate-900/40 opacity-50'
      : 'border-slate-700 bg-slate-800/50'

  return (
    <div className={`rounded-lg border p-5 space-y-3 ${stateClasses}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="font-semibold text-slate-100">{task.title}</h4>
        <div className="flex items-center gap-2">
          <span className="rounded border border-slate-600 px-2 py-0.5 text-xs text-slate-300">
            OWASP {task.owasp_id}
          </span>
          {task.completed && (
            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-300">
              Completed
            </span>
          )}
          {task.locked && <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-400">Locked</span>}
        </div>
      </div>

      {task.locked && <p className="text-sm text-slate-500">Complete the previous task to unlock this one.</p>}

      {!task.locked && (
        <>
          {task.concept && (
            <div className="rounded-md border border-slate-700 bg-slate-900/40 p-3">
              <button
                type="button"
                onClick={() => setShowConcept((v) => !v)}
                className="text-xs font-medium text-sky-400 hover:text-sky-300"
              >
                {showConcept ? 'Hide concept' : 'What is this? (concept)'}
              </button>
              {showConcept && (
                <p className="mt-2 whitespace-pre-line text-xs leading-relaxed text-slate-400">{task.concept}</p>
              )}
            </div>
          )}

          <p className="whitespace-pre-line text-sm text-slate-300">{task.prompt}</p>

          {task.hint && !task.completed && (
            <div>
              <button
                type="button"
                onClick={() => setShowHint((v) => !v)}
                className="text-xs text-sky-400 hover:text-sky-300"
              >
                {showHint ? 'Hide hint' : 'Show hint'}
              </button>
              {showHint && <p className="mt-1 text-xs text-slate-400">{task.hint}</p>}
            </div>
          )}

          {!task.completed && task.type === 'auto' && (
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

          {!task.completed && task.type === 'submit' && (
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
        </>
      )}
    </div>
  )
}
