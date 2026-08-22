import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import type { FeedbackItem } from '../api/types'

const TOKEN_KEY = 'eduvapt_admin_token'

/** /admin - password login, then a table of all submitted feedback. */
export default function AdminPage() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [password, setPassword] = useState('')
  const [feedback, setFeedback] = useState<FeedbackItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    api
      .getAdminFeedback(token)
      .then(setFeedback)
      .catch((err) => {
        // An expired/invalid token (e.g. after a server restart) forces re-login.
        if (err instanceof ApiError && err.status === 401) {
          localStorage.removeItem(TOKEN_KEY)
          setToken(null)
        } else {
          setError(String(err))
        }
      })
      .finally(() => setLoading(false))
  }, [token])

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const { token: t } = await api.adminLogin(password)
      localStorage.setItem(TOKEN_KEY, t)
      setToken(t)
      setPassword('')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err))
    }
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setFeedback([])
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-sm px-6 py-16">
        <h1 className="mb-1 text-2xl font-bold text-slate-100">Admin login</h1>
        <p className="mb-6 text-sm text-slate-400">Enter the admin password to view feedback.</p>
        <form onSubmit={handleLogin} className="space-y-4 rounded-lg border border-slate-700 bg-slate-800/50 p-5">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Admin password"
            autoFocus
            className="w-full rounded-md border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button type="submit" className="w-full rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500">
            Log in
          </button>
        </form>
        <Link to="/dashboard" className="mt-4 inline-block text-sm text-slate-500 hover:text-slate-300">
          &larr; Back to dashboard
        </Link>
      </div>
    )
  }

  const avg =
    feedback.length > 0 ? (feedback.reduce((a, f) => a + f.rating, 0) / feedback.length).toFixed(1) : '-'

  return (
    <div className="mx-auto max-w-4xl px-6 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Feedback</h1>
          <p className="text-sm text-slate-400">
            {feedback.length} submission(s) · average rating {avg} / 5
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="rounded-md border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
        >
          Log out
        </button>
      </div>

      {loading && <p className="text-slate-400">Loading feedback...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      {!loading && feedback.length === 0 && <p className="text-slate-500">No feedback submitted yet.</p>}

      <div className="space-y-3">
        {feedback.map((f) => (
          <div key={f.id} className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <div className="flex items-center justify-between">
              <span className="text-amber-400" aria-label={`${f.rating} out of 5 stars`}>
                {'★'.repeat(f.rating)}
                <span className="text-slate-600">{'★'.repeat(5 - f.rating)}</span>
              </span>
              <span className="text-xs text-slate-500">
                {f.session_id != null ? `Session ${f.session_id}` : 'Session deleted'} ·{' '}
                {new Date(f.created_at).toLocaleString()}
              </span>
            </div>
            {f.suggestion && <p className="mt-2 text-sm text-slate-300">{f.suggestion}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}
