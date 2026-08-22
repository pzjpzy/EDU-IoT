import { useState } from 'react'
import { api } from '../api/client'

interface Props {
  sessionId: number
  onClose: () => void
}

/** Star-rating + suggestion popup shown when the student leaves the capstone
 * for the summary. Rating is required to submit; the whole thing can be
 * skipped. */
export default function FeedbackModal({ sessionId, onClose }: Props) {
  const [rating, setRating] = useState(0)
  const [hover, setHover] = useState(0)
  const [suggestion, setSuggestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit() {
    if (rating < 1) {
      setError('Please pick a star rating first.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await api.submitFeedback(sessionId, rating, suggestion)
      onClose()
    } catch (err) {
      setError(String(err))
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-6 space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-100">How was this session?</h3>
          <p className="text-sm text-slate-400">Your feedback helps improve the lab.</p>
        </div>

        <div className="flex justify-center gap-2" onMouseLeave={() => setHover(0)}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              onMouseEnter={() => setHover(n)}
              onClick={() => {
                setRating(n)
                setError(null)
              }}
              aria-label={`${n} star${n > 1 ? 's' : ''}`}
              className={
                'text-4xl leading-none transition-colors ' +
                ((hover || rating) >= n ? 'text-amber-400' : 'text-slate-600 hover:text-amber-300')
              }
            >
              {(hover || rating) >= n ? '★' : '☆'}
            </button>
          ))}
        </div>

        <textarea
          value={suggestion}
          onChange={(e) => setSuggestion(e.target.value)}
          rows={4}
          placeholder="Any suggestions? (optional)"
          className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100"
        />

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={busy}
            className="rounded-md border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
          >
            Skip
          </button>
          <button
            onClick={handleSubmit}
            disabled={busy}
            className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40 hover:bg-sky-500"
          >
            {busy ? 'Submitting...' : 'Submit feedback'}
          </button>
        </div>
      </div>
    </div>
  )
}
