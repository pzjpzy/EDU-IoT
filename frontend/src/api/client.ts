import type {
  CapstoneBoard,
  CapstoneStatus,
  CheckResult,
  FeedbackItem,
  Finding,
  QuizAnswer,
  QuizQuestion,
  QuizResult,
  ScanResult,
  SessionSummary,
  StatsOverview,
  SubmitResult,
  TaskBoard,
  VaptSession,
  VulnBucket,
  VulnGranularity,
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

  getStatsOverview: () => request<StatsOverview>('/api/stats/overview'),
  getVulnStats: (granularity: VulnGranularity) =>
    request<VulnBucket[]>(`/api/stats/vulnerabilities?granularity=${granularity}`),

  getSummary: (id: number) => request<SessionSummary>(`/api/sessions/${id}/summary`),
  setProgress: (id: number, furthestPhase: number) =>
    request<{ furthest_phase: number }>(`/api/sessions/${id}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ furthest_phase: furthestPhase }),
    }),

  runScan: (id: number, useScapy = false) =>
    request<ScanResult>(`/api/sessions/${id}/scan`, {
      method: 'POST',
      body: JSON.stringify({ use_nmap: true, use_scapy: useScapy }),
    }),
  getScan: (id: number) => request<ScanResult>(`/api/sessions/${id}/scan`),

  listTasks: (id: number) => request<TaskBoard>(`/api/sessions/${id}/tasks`),
  checkTask: (id: number, taskId: string) =>
    request<CheckResult>(`/api/sessions/${id}/tasks/${taskId}/check`, { method: 'POST' }),
  submitTask: (id: number, taskId: string, answer: string) =>
    request<SubmitResult>(`/api/sessions/${id}/tasks/${taskId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    }),

  getFindings: (id: number) => request<Finding[]>(`/api/sessions/${id}/findings`),

  capstoneBoard: (id: number, capstoneIp: string) =>
    request<CapstoneBoard>(`/api/sessions/${id}/capstone/board`, {
      method: 'POST',
      body: JSON.stringify({ capstone_target_ip: capstoneIp }),
    }),
  checkCapstone: (id: number, objId: string, capstoneIp: string) =>
    request<CheckResult>(`/api/sessions/${id}/capstone/${objId}/check`, {
      method: 'POST',
      body: JSON.stringify({ capstone_target_ip: capstoneIp }),
    }),
  submitCapstone: (id: number, objId: string, capstoneIp: string, answer: string) =>
    request<SubmitResult>(`/api/sessions/${id}/capstone/${objId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ capstone_target_ip: capstoneIp, answer }),
    }),
  setCapstoneStatus: (id: number, status: CapstoneStatus) =>
    request<{ capstone_status: string }>(`/api/sessions/${id}/capstone/status`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    }),

  getQuizQuestions: () => request<QuizQuestion[]>('/api/quiz/questions'),
  submitQuiz: (id: number, phase: 'pre' | 'post', answers: QuizAnswer[]) =>
    request<QuizResult>(`/api/sessions/${id}/quiz`, { method: 'POST', body: JSON.stringify({ phase, answers }) }),
  getQuizResults: (id: number) => request<QuizResult[]>(`/api/sessions/${id}/quiz`),

  reportUrl: (id: number) => `${BASE_URL}/api/sessions/${id}/report`,

  submitFeedback: (id: number, rating: number, suggestion: string) =>
    request<{ ok: boolean }>(`/api/sessions/${id}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ rating, suggestion }),
    }),

  adminLogin: (password: string) =>
    request<{ token: string }>('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    }),
  getAdminFeedback: (token: string) =>
    request<FeedbackItem[]>('/api/admin/feedback', {
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    }),
}

export function terminalWsUrl(): string {
  return `${BASE_URL.replace(/^http/, 'ws')}/ws/terminal`
}
