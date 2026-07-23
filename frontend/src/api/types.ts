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

export interface PortInfo {
  port: number
  protocol: string
  state: string
  service: string
  product: string
  version: string
  banner: string
}

export interface ReconResult {
  stage: 'recon'
  explanation: StageExplanation
  hosts_discovered: string[]
  discovery_method: string
  warning: string | null
  ports: PortInfo[]
}

export interface Finding {
  id: number
  owasp_id: string
  title: string
  severity: 'High' | 'Medium' | 'Low'
  evidence: string
  mitigation: string
}

export interface VulnResult {
  stage: 'vuln'
  explanation: StageExplanation
  findings: Finding[]
}

export interface ExploitAttempt {
  id: number
  service: string
  username: string | null
  password: string | null
  success: boolean
  note: string | null
}

export interface ExploitResult {
  stage: 'exploit'
  explanation: StageExplanation
  attempts: ExploitAttempt[]
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
