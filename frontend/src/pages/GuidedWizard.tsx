import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { QuizResult, SessionSummary, StageExplanation, VaptSession } from '../api/types'
import StepperNav from '../components/StepperNav'
import QuizStep from '../components/steps/QuizStep'
import ReconStep from '../components/steps/ReconStep'
import TasksStep from '../components/steps/TasksStep'
import ReportStep from '../components/steps/ReportStep'
import CapstoneStep from '../components/steps/CapstoneStep'
import SummaryStep from '../components/steps/SummaryStep'

const SUMMARY_PHASE = 5

const RECON_EXPLANATION: StageExplanation = {
  title: 'Stage 1 - Automated Recon',
  what: 'Reconnaissance is the first phase of any penetration test: discovering which services a target exposes before assessing them.',
  why: 'A real assessor starts by mapping the attack surface. Seeing the tool do it automatically - and having each service explained - builds the mental model you then apply by hand.',
  what_the_tool_does:
    "This step runs an automated, lab-scoped port scan and protocol banner grab of the target, then explains each discovered service and how it maps to the OWASP IoT Top 5. You'll reproduce the key findings yourself in the challenges that follow.",
}

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
  const [furthest, setFurthest] = useState(0)
  const [preQuizResult, setPreQuizResult] = useState<QuizResult | null>(null)
  const [summary, setSummary] = useState<SessionSummary | null>(null)

  useEffect(() => {
    api.getSession(sessionId).then(setSession).catch(() => {})
    // Restore how far the student got so a page reload doesn't drop them back
    // at Pre-Quiz, and so the stepper knows which phases are revisitable.
    api
      .getSummary(sessionId)
      .then((s) => {
        setSummary(s)
        const resume = Math.min(Math.max(s.furthest_phase, 0), SUMMARY_PHASE)
        setFurthest(resume)
        setStep(resume)
      })
      .catch(() => {})
  }, [sessionId])

  /** Move forward a phase and persist it as the new furthest reached. */
  function advance(next: number) {
    setStep(next)
    setFurthest((f) => Math.max(f, next))
    api.setProgress(sessionId, next).catch(() => {})
  }

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

      <StepperNav current={step} furthest={furthest} onNavigate={setStep} />

      {step === 0 && (
        <QuizStep
          sessionId={sessionId}
          phase="pre"
          onComplete={(res) => {
            setPreQuizResult(res)
            advance(1)
          }}
        />
      )}

      {step === 1 && session && (
        <ReconStep
          sessionId={sessionId}
          targetIp={session.target_ip}
          explanation={RECON_EXPLANATION}
          onComplete={() => advance(2)}
        />
      )}

      {step === 2 && session && (
        <TasksStep sessionId={sessionId} targetIp={session.target_ip} onAllComplete={() => advance(3)} />
      )}

      {step === 3 && (
        <ReportStep sessionId={sessionId} explanation={REPORT_EXPLANATION} onComplete={() => advance(4)} />
      )}

      {step === 4 && (
        <CapstoneStep
          sessionId={sessionId}
          preQuiz={preQuizResult ?? summary?.pre_quiz ?? null}
          onComplete={() => advance(SUMMARY_PHASE)}
        />
      )}

      {step === SUMMARY_PHASE && <SummaryStep sessionId={sessionId} />}
    </div>
  )
}
