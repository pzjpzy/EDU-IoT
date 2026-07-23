import type {
  ExploitResult,
  Finding,
  QuizAnswer,
  QuizQuestion,
  QuizResult,
  ReconResult,
  VaptSession,
  VulnResult,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

export { ApiError }

export const api = {
  listSessions: () => request<VaptSession[]>('/api/sessions'),
  createSession: (name: string, target_ip: string) =>
    request<VaptSession>('/api/sessions', { method: 'POST', body: JSON.stringify({ name, target_ip }) }),
  getSession: (id: number) => request<VaptSession>(`/api/sessions/${id}`),
  deleteSession: (id: number) => fetch(`${BASE_URL}/api/sessions/${id}`, { method: 'DELETE' }),

  runRecon: (id: number) => request<ReconResult>(`/api/sessions/${id}/recon`, { method: 'POST' }),
  getRecon: (id: number) => request<ReconResult>(`/api/sessions/${id}/recon`),

  runVuln: (id: number) => request<VulnResult>(`/api/sessions/${id}/vuln`, { method: 'POST' }),
  getFindings: (id: number) => request<Finding[]>(`/api/sessions/${id}/findings`),

  runExploit: (id: number) => request<ExploitResult>(`/api/sessions/${id}/exploit`, { method: 'POST' }),

  getQuizQuestions: () => request<QuizQuestion[]>('/api/quiz/questions'),
  submitQuiz: (id: number, phase: 'pre' | 'post', answers: QuizAnswer[]) =>
    request<QuizResult>(`/api/sessions/${id}/quiz`, { method: 'POST', body: JSON.stringify({ phase, answers }) }),
  getQuizResults: (id: number) => request<QuizResult[]>(`/api/sessions/${id}/quiz`),

  reportUrl: (id: number) => `${BASE_URL}/api/sessions/${id}/report`,
}
