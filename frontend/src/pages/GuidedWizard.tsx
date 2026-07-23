import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { QuizResult, StageExplanation, VaptSession } from '../api/types'
import StepperNav from '../components/StepperNav'
import QuizStep from '../components/steps/QuizStep'
import TasksStep from '../components/steps/TasksStep'
import ReportStep from '../components/steps/ReportStep'

const REPORT_EXPLANATION: StageExplanation = {
  title: 'Stage 3 - Reporting',
  what: 'A penetration test is only useful if its results are communicated clearly to the people who need to act on them.',
  why: 'Real-world reports translate technical findings into risk and remediation guidance a non-specialist stakeholder can act on.',
  what_the_tool_does:
    'This step compiles every task you completed - findings, OWASP IoT mapping, severity, and mitigation guidance - into a downloadable PDF report.',
}

export default function GuidedWizard() {
  const { id } = useParams()
  const sessionId = Number(id)
  const [session, setSession] = useState<VaptSession | null>(null)
  const [step, setStep] = useState(0)
  const [preQuizResult, setPreQuizResult] = useState<QuizResult | null>(null)

  useEffect(() => {
    api.getSession(sessionId).then(setSession).catch(() => {})
  }, [sessionId])

  return (
    <div className="mx-auto max-w-4xl px-6 py-10 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/dashboard" className="text-sm text-slate-500 hover:text-slate-300">
            &larr; Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-slate-100">{session?.name ?? 'Loading...'}</h1>
          <p className="text-sm text-slate-500">Target: {session?.target_ip}</p>
        </div>
      </div>

      <StepperNav current={step} />

      {step === 0 && (
        <QuizStep
          sessionId={sessionId}
          phase="pre"
          onComplete={(res) => {
            setPreQuizResult(res)
            setStep(1)
          }}
        />
      )}

      {step === 1 && session && (
        <TasksStep sessionId={sessionId} targetIp={session.target_ip} onAllComplete={() => setStep(2)} />
      )}

      {step === 2 && (
        <ReportStep sessionId={sessionId} explanation={REPORT_EXPLANATION} onComplete={() => setStep(3)} />
      )}

      {step === 3 && (
        <QuizStep sessionId={sessionId} phase="post" priorResult={preQuizResult} onComplete={() => setStep(4)} />
      )}

      {step === 4 && (
        <div className="rounded-lg border border-emerald-600/40 bg-emerald-500/10 p-8 text-center space-y-4">
          <h2 className="text-xl font-semibold text-emerald-300">Session complete</h2>
          <p className="text-slate-300">
            You've worked through every task in this room using your own tools, and completed the
            learning-effectiveness quiz. You can revisit the report at any time.
          </p>
          <div className="flex justify-center gap-3">
            <button
              onClick={() => setStep(2)}
              className="rounded-md border border-slate-600 px-4 py-2 text-slate-300 hover:bg-slate-800"
            >
              Back to Report
            </button>
            <Link to="/dashboard" className="rounded-md bg-sky-600 px-4 py-2 font-medium text-white hover:bg-sky-500">
              Back to Dashboard
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
