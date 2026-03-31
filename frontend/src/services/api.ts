const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const TOKEN_KEY = 'token'
const REFRESH_TOKEN_KEY = 'refresh_token'

// Token storage functions
function getToken(): string | null {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem(TOKEN_KEY)
    console.log('[Token] getToken:', token ? `token found (${token.length} chars)` : 'null')
    return token
  }
  return null
}

function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token)
  }
}

function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY)
  }
}

function getRefreshToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }
  return null
}

function setRefreshToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  }
}

function removeRefreshToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

// Auto-refresh function
async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false

  try {
    const response = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) return false

    const data = await response.json()
    if (data.access_token) {
      setToken(data.access_token)
      return true
    }
    return false
  } catch {
    return false
  }
}

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body?: any
  headers?: Record<string, string>
}

async function apiCall<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options
  const token = getToken()

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  }

  if (body) {
    config.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config)

  if (!response.ok) {
    let errorMessage = `API Error: ${response.status}`
    try {
      const errorData = await response.json()
      errorMessage = errorData.message || errorMessage
    } catch {
      // Use default message
    }
    throw new Error(errorMessage)
  }

  return response.json()
}

// Auth API
export const authApi = {
  register: (email: string, password: string) =>
    apiCall<{ id: number; email: string; role: string }>('/api/auth/register', {
      method: 'POST',
      body: { email, password },
    }),

  login: (email: string, password: string) =>
    apiCall<{ access_token: string; refresh_token?: string; token_type: string }>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    }).then((res) => {
      // Store tokens on successful login
      console.log('[Login] Response:', res)
      if (res.access_token) {
        console.log('[Login] Storing access_token:', res.access_token.substring(0, 20) + '...')
        setToken(res.access_token)
      }
      if (res.refresh_token) {
        setRefreshToken(res.refresh_token)
      }
      return res
    }),

  logout: () => {
    removeToken()
    removeRefreshToken()
  },

  me: () =>
    apiCall<{ id: number; email: string; role: string }>('/api/auth/me'),
}

// Analytics API
export interface MetricData {
  total_visits: number
  total_orders: number
  conversion_rate: number
  total_customers: number
  avg_order_value: number
}

export interface FunnelStep {
  step: string
  user_count: number
  conversion_rate: number
  dropoff_rate: number
}

export interface RFMSegment {
  user_id: string
  recency: number
  frequency: number
  monetary: number
  rfm_score: [number, number, number]
  segment: string
}

export interface RFMData {
  segment_distribution: Record<string, number>
  customers: RFMSegment[]
  summary: {
    total_customers: number
    avg_recency: number
    avg_frequency: number
    avg_monetary: number
    high_value_count: number
  }
}

export const analyticsApi = {
  getOverview: () =>
    apiCall<{
      metrics: MetricData
      changes: Record<string, number>
    }>('/api/analytics/overview'),

  analyzeFunnel: (events: any[], steps?: string[]) =>
    apiCall<{
      funnel: FunnelStep[]
      total_users: number
      biggest_dropoff: { step: string; dropoff_rate: number } | null
    }>('/api/analytics/funnel', {
      method: 'POST',
      body: { events, steps },
    }),

  analyzeRFM: (orders: any[]) =>
    apiCall<RFMData>('/api/analytics/rfm', {
      method: 'POST',
      body: { orders },
    }),

  parseColumns: (columns: string[], sample_data: any[]) =>
    apiCall<{
      mappings: Record<string, string>
      suggested_mappings: Record<string, string>
      unmapped_columns: string[]
    }>('/api/analytics/parse-columns', {
      method: 'POST',
      body: { columns, sample_data },
    }),

  getAnalysisResult: (datasourceId: number) => {
    const token = getToken()
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return fetch(`${API_BASE}/api/analytics/result?datasource_id=${datasourceId}`, {
      method: 'GET',
      headers,
    }).then(async (response) => {
      if (!response.ok) {
        throw new Error(`获取分析结果失败: ${response.status}`)
      }
      return response.json()
    })
  },
}

// Conversation API
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export const conversationApi = {
  chat: (
    message: string,
    history: ChatMessage[] = [],
    context?: any
  ) =>
    apiCall<{
      response: string
      parsed_intent?: {
        query_type: string
        parameters: Record<string, any>
      }
    }>('/api/conversation/chat', {
      method: 'POST',
      body: { message, history, context },
    }),

  generateInsight: (
    insightType: 'funnel' | 'rfm' | 'dashboard',
    data: any
  ) =>
    apiCall<{ insight: string }>('/api/conversation/insight', {
      method: 'POST',
      body: { insight_type: insightType, data },
    }),
}

// Report API
export interface Report {
  id: string
  name: string
  type: string
  date: string
  status: 'ready' | 'generating' | 'failed'
}

export const reportApi = {
  generate: (
    reportType: string,
    data: any,
    title?: string
  ) =>
    apiCall<{
      id: string
      title: string
      type: string
      format: string
      download_url: string
      created_at: string
    }>('/api/reports/generate', {
      method: 'POST',
      body: { report_type: reportType, data, title },
    }),

  list: () =>
    apiCall<{ reports: Report[] }>('/api/reports/list'),

  get: (reportId: string) =>
    apiCall<{ id: string; name: string; type: string; content: string }>(
      `/api/reports/${reportId}`
    ),
}

// Health check
export const healthApi = {
  check: () => apiCall<{ status: string; app: string }>('/api/health'),
}

// Datasources API - uses FormData for file uploads
export const datasourcesApi = {
  upload: (name: string, file: File) => {
    const token = getToken()
    console.log('[Upload] Token:', token ? `present (${token.length} chars)` : 'MISSING')
    console.log('[Upload] Token value:', token)
    const formData = new FormData()
    formData.append('file', file)

    const headers: Record<string, string> = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
      console.log('[Upload] Authorization header set')
    }

    return fetch(`${API_BASE}/api/datasources/?name=${encodeURIComponent(name)}`, {
      method: 'POST',
      headers,
      body: formData,
    }).then(async (response) => {
      console.log('[Upload] Response status:', response.status)
      if (!response.ok) {
        const text = await response.text()
        console.log('[Upload] Error response:', text)
        throw new Error(`上传失败: ${response.status} - ${text}`)
      }
      return response.json()
    })
  },

  confirmMappings: (datasourceId: number, mappings: Record<string, string>) => {
    const token = getToken()
    return fetch(`${API_BASE}/api/datasources/confirm-mappings?datasource_id=${datasourceId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(mappings),
    }).then(async (response) => {
      if (!response.ok) {
        throw new Error(`确认映射失败: ${response.status}`)
      }
      return response.json()
    })
  },
}

// Export token utilities for external use
export { refreshAccessToken, getToken, getRefreshToken, setRefreshToken, removeRefreshToken }
