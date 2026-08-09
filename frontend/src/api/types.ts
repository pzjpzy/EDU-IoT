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
