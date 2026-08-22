export interface VaptSession {
  id: number
  name: string
  target_ip: string
  created_at: string
}

export interface StageExplanation {
  title: string
  what: string
  why: string
  what_the_tool_does: string
}

export interface Finding {
  id: number
  owasp_id: string
  title: string
  severity: 'High' | 'Medium' | 'Low'
  evidence: string
  mitigation: string
}

export interface TaskItem {
  id: string
  title: string
  type: 'auto' | 'submit'
  concept: string | null
  prompt: string
  hint: string | null
  owasp_id: string
  completed: boolean
  locked: boolean
}

export interface ScanService {
  port: number
  protocol: string
  banner: string | null
  version: string | null
  owasp_id: string
  severity_hint: string
  observation: string
  why_it_matters: string
  reproduce: string
}

export interface ScanResult {
  target_ip: string
  duration_seconds: number
  ports_scanned: number
  open_ports: number[]
  services: ScanService[]
  engine_notes: string[]
  summary: string
}

export interface TargetProfile {
  http_default_creds_vulnerable: boolean
  snapshot_unauth_vulnerable: boolean
  telnet_enabled: boolean
  telnet_default_creds_vulnerable: boolean
  rtsp_enabled: boolean
}

export interface TaskBoard {
  tasks: TaskItem[]
  profile: TargetProfile
  warning: string | null
}

export interface CheckResult {
  completed: boolean
  error?: string
}

export interface SubmitResult {
  correct: boolean
  error?: string
}

export interface QuizQuestion {
  id: string
  question: string
  options: string[]
}

export interface QuizAnswer {
  question_id: string
  selected_index: number
}

export interface QuizResult {
  phase: 'pre' | 'post'
  score: number
  total: number
  breakdown: { question_id: string; correct: boolean; correct_answer_index: number }[]
}

export interface CapstoneObjective {
  id: string
  title: string
  type: 'auto' | 'submit'
  owasp_id: string
  completed: boolean
}

export interface CapstoneBoard {
  objectives: CapstoneObjective[]
  profile: TargetProfile
  warning: string | null
  score: number
  total: number
}

export type CapstoneStatus = 'completed' | 'gave_up' | 'skipped' | 'in_progress' | 'not_started'

export interface SessionSummary {
  furthest_phase: number
  pre_quiz: { score: number; total: number } | null
  recon_done: boolean
  findings_by_severity: { High: number; Medium: number; Low: number }
  findings_total: number
  capstone: { status: CapstoneStatus; score: number | null; total: number | null }
}

export type VulnGranularity = 'day' | 'week' | 'month'

export interface StatsOverview {
  cctv_scanned_this_month: number
  quiz_accuracy: { correct: number; total: number; pct: number }
  vulns_all_time: number
}

export interface VulnBucket {
  bucket: string
  High: number
  Medium: number
  Low: number
}

export interface FeedbackItem {
  id: number
  session_id: number | null
  rating: number
  suggestion: string | null
  created_at: string
}
