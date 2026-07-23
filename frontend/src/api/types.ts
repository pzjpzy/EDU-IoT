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
  prompt: string
  hint: string | null
  owasp_id: string
  completed: boolean
  locked: boolean
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
