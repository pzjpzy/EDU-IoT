import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import type { QuizQuestion, QuizResult } from '../../api/types'

interface Props {
  sessionId: number
  phase: 'pre' | 'post'
  priorResult?: QuizResult | null
  onComplete: (result: QuizResult) => void
}

export default function QuizStep({ sessionId, phase, priorResult, onComplete }: Props) {
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [result, setResult] = useState<QuizResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getQuizQuestions()
      .then(setQuestions)
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false))
  }, [])

  const allAnswered = questions.length > 0 && questions.every((q) => answers[q.id] !== undefined)

  async function handleSubmit() {
    setError(null)
    try {
      const payload = Object.entries(answers).map(([question_id, selected_index]) => ({
        question_id,
        selected_index,
      }))
      const res = await api.submitQuiz(sessionId, phase, payload)
      setResult(res)
    } catch (err) {
      setError(String(err))
    }
  }

  if (loading) return <p className="text-slate-400">Loading quiz questions...</p>

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-slate-100">
          {phase === 'pre' ? 'Before you start: quick knowledge check' : 'After the session: same quick check'}
        </h3>
        <p className="text-sm text-slate-400">
          {phase === 'pre'
            ? "This short quiz measures what you know before the guided session. You'll take it again afterwards so we can measure what you learned."
            : 'Same questions as before - this measures how much your understanding improved during the session.'}
        </p>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {!result &&
        questions.map((q, idx) => (
          <div key={q.id} className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <p className="mb-3 font-medium text-slate-200">
              {idx + 1}. {q.question}
            </p>
            <div className="space-y-2">
              {q.options.map((opt, optIdx) => (
                <label key={optIdx} className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="radio"
                    name={q.id}
                    checked={answers[q.id] === optIdx}
                    onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: optIdx }))}
                  />
                  {opt}
                </label>
              ))}
            </div>
          </div>
        ))}

      {!result && (
        <button
          disabled={!allAnswered}
          onClick={handleSubmit}
          className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white disabled:opacity-40 hover:bg-sky-500"
        >
          Submit answers
        </button>
      )}

      {result && (
        <div className="rounded-lg border border-emerald-600/40 bg-emerald-500/10 p-5 space-y-3">
          <p className="text-lg font-semibold text-emerald-300">
            Score: {result.score} / {result.total}
          </p>
          {phase === 'post' && priorResult && (
            <p className="text-sm text-slate-300">
              Pre-session score was {priorResult.score} / {priorResult.total}.{' '}
              {result.score > priorResult.score
                ? `Improvement of ${result.score - priorResult.score} question(s) - nice work.`
                : result.score === priorResult.score
                  ? 'Same score as before.'
                  : 'Lower than before - consider revisiting the explanation panels.'}
            </p>
          )}
          <button
            onClick={() => onComplete(result)}
            className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500"
          >
            Continue
          </button>
        </div>
      )}
    </div>
  )
}
