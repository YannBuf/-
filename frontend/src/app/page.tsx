'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import {
  Home,
  FileText,
  MessageCircle,
  User,
  Upload,
  TrendingUp,
  Users,
  ShoppingCart,
  Sparkles,
  Send,
  ChevronRight,
  AlertCircle,
  Database,
  Bell,
  Settings,
  LogOut,
  Plus,
  RefreshCw,
  BarChart3,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
} from 'lucide-react'
import { analyticsApi, conversationApi, reportApi, healthApi, datasourcesApi, authApi } from '@/services/api'
import { getToken } from '@/services/api'
import ThinkingAnimation from '@/components/analytics/ThinkingAnimation'

// ============ Types ============
type Tab = 'home' | 'reports' | 'chat' | 'profile'

type UploadState = 'idle' | 'uploading' | 'thinking' | 'done' | 'error'

interface FieldMapping {
  original: string
  standard: string
}

interface MetricData {
  label: string
  value: string | number
  change?: number
  icon: React.ReactNode
}

interface FunnelStep {
  name: string
  count: number
  rate: number
  dropoff: number
}

interface RFMData {
  segment: string
  count: number
  color: string
}

interface ChatMessageType {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface OverviewData {
  metrics: {
    total_visits: number
    total_orders: number
    conversion_rate: number
    total_customers: number
    avg_order_value: number
  }
  changes: Record<string, number>
}

// ============ API Integration ============
function useApiData<T>(fetchFn: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const fetchRef = useRef(fetchFn)
  fetchRef.current = fetchFn

  const fetch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const result = await fetchRef.current()
      setData(result)
    } catch (err: any) {
      setError(err.message || '获取数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error, refetch: fetch }
}

// ============ Components ============

function BottomTabs({ active, onChange }: { active: Tab; onChange: (tab: Tab) => void }) {
  const tabs = [
    { id: 'home' as Tab, label: '首页', icon: <Home size={22} /> },
    { id: 'reports' as Tab, label: '报告', icon: <FileText size={22} /> },
    { id: 'chat' as Tab, label: '对话', icon: <MessageCircle size={22} /> },
    { id: 'profile' as Tab, label: '我的', icon: <User size={22} /> },
  ]

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50">
      <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />
      <nav className="bg-surface-elevated/95 backdrop-blur-xl border-t border-border">
        <div className="max-w-lg mx-auto flex justify-around py-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`
                flex flex-col items-center gap-1 px-6 py-2 rounded-xl transition-all duration-300
                ${active === tab.id
                  ? 'text-accent bg-accent/10'
                  : 'text-text-muted hover:text-text-secondary'
                }
              `}
            >
              <div className="relative">
                {tab.icon}
                {active === tab.id && (
                  <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-accent animate-pulse" />
                )}
              </div>
              <span className="text-xs font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  )
}

function MetricCardComponent({ metric, index }: { metric: MetricData; index: number }) {
  const isPositive = metric.change && metric.change > 0
  const isNegative = metric.change && metric.change < 0

  return (
    <div
      className="metric-card bg-surface-elevated rounded-2xl p-5 border border-border hover:border-accent/30 transition-all duration-300 group"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 rounded-xl bg-accent/10 text-accent group-hover:bg-accent/20 transition-colors">
          {metric.icon}
        </div>
        {metric.change !== undefined && (
          <div className={`flex items-center gap-1 text-sm font-medium ${isPositive ? 'text-success' : isNegative ? 'text-error' : 'text-text-muted'}`}>
            {isPositive ? <ArrowUpRight size={16} /> : isNegative ? <ArrowDownRight size={16} /> : null}
            {Math.abs(metric.change)}%
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-text-primary mb-1">
        {metric.value}
      </div>
      <div className="text-sm text-text-muted">{metric.label}</div>
    </div>
  )
}

function FunnelChart({ steps }: { steps: FunnelStep[] }) {
  const maxCount = Math.max(...steps.map(s => s.count), 1)

  return (
    <div className="space-y-4">
      {steps.map((step, index) => {
        const widthPercent = (step.count / maxCount) * 100

        return (
          <div key={step.name} className="relative">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-text-primary capitalize">{step.name}</span>
              <div className="flex items-center gap-3">
                <span className="text-sm text-text-secondary">{step.count.toLocaleString()} 人</span>
                <span className="text-sm text-accent font-medium">{step.rate}%</span>
              </div>
            </div>
            <div className="h-10 bg-surface rounded-xl overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-accent/80 to-accent rounded-xl funnel-bar flex items-center justify-end pr-4"
                style={{ width: `${widthPercent}%` }}
              >
                {widthPercent > 15 && (
                  <span className="text-sm font-semibold text-background">
                    {widthPercent.toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
            {step.dropoff > 5 && (
              <div className="absolute -right-8 top-1/2 -translate-y-1/2 text-xs text-error/80 flex items-center gap-1">
                <ArrowDownRight size={12} />
                {step.dropoff}%
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function RFMDistribution({ data }: { data: RFMData[] }) {
  const total = data.reduce((sum, d) => sum + Number(d.count), 0)

  return (
    <div className="space-y-3">
      {data.map((item) => {
        const percent = ((item.count / total) * 100).toFixed(1)
        return (
          <div key={item.segment} className="flex items-center gap-3">
            <div className="w-24 text-sm text-text-secondary capitalize">{item.segment}</div>
            <div className="flex-1 h-8 bg-surface rounded-lg overflow-hidden">
              <div
                className="h-full rounded-lg transition-all duration-700 flex items-center justify-end pr-3"
                style={{
                  width: `${percent}%`,
                  backgroundColor: item.color,
                }}
              >
                {parseFloat(percent) > 8 && (
                  <span className="text-xs font-semibold text-background">{percent}%</span>
                )}
              </div>
            </div>
            <div className="w-16 text-right text-sm text-text-muted">{item.count}</div>
          </div>
        )
      })}
    </div>
  )
}

function AIInsightCard({ insight, loading, onGenerateReport }: { insight: string; loading: boolean; onGenerateReport?: () => void }) {
  return (
    <div className="relative bg-gradient-to-br from-accent/10 via-surface-elevated to-surface-elevated rounded-2xl p-6 border border-accent/20 ai-glow">
      <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-accent/20 to-transparent rounded-tr-2xl rounded-bl-full opacity-50" />
      <div className="flex items-start gap-3 mb-4">
        <div className="p-2 rounded-xl bg-accent/20">
          <Sparkles size={20} className="text-accent" />
        </div>
        <div>
          <div className="text-sm font-semibold text-accent">AI 智能解读</div>
          <div className="text-xs text-text-muted">基于数据分析自动生成</div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-3 text-text-muted">
          <Loader2 size={18} className="animate-spin" />
          <span className="text-sm">AI 思考中...</span>
        </div>
      ) : (
        <p className="text-text-primary leading-relaxed">{insight}</p>
      )}

      <div className="flex gap-2 mt-4">
        <button className="flex-1 py-2 px-4 rounded-xl bg-accent/10 text-accent text-sm font-medium hover:bg-accent/20 transition-colors">
          查看详情
        </button>
        <button
          onClick={onGenerateReport}
          className="flex-1 py-2 px-4 rounded-xl bg-surface hover:bg-surface-hover transition-colors text-sm font-medium"
        >
          生成报告
        </button>
      </div>
    </div>
  )
}

interface ReportGenerateModalProps {
  isOpen: boolean
  onClose: () => void
  onGenerate: (type: string) => void
}

function ReportGenerateModal({ isOpen, onClose, onGenerate }: ReportGenerateModalProps) {
  const [reportType, setReportType] = useState('weekly')

  if (!isOpen) return null

  const reportTypes = [
    { id: 'weekly', label: '周报 - 本周数据汇总', emoji: '📊' },
    { id: 'monthly', label: '月报 - 本月数据汇总', emoji: '📈' },
    { id: 'funnel', label: '漏斗分析 - 转化路径分析', emoji: '🔍' },
    { id: 'rfm', label: '客户分层 - RFM模型分析', emoji: '👥' },
  ]

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-surface-elevated rounded-2xl p-6 w-96 border border-border">
        <h3 className="text-lg font-semibold text-text-primary mb-4">生成报告</h3>
        <div className="space-y-3">
          {reportTypes.map((type) => (
            <button
              key={type.id}
              onClick={() => onGenerate(type.id)}
              className={`w-full p-3 rounded-xl text-left transition-all ${
                reportType === type.id
                  ? 'bg-accent/20 border border-accent'
                  : 'bg-surface border border-border hover:border-accent/50'
              }`}
            >
              <span className="mr-2">{type.emoji}</span>
              {type.label}
            </button>
          ))}
        </div>
        <button
          onClick={onClose}
          className="mt-4 w-full py-2 text-text-muted hover:text-text-primary transition-colors"
        >
          取消
        </button>
      </div>
    </div>
  )
}

interface ReportPreviewModalProps {
  report: { id: string; name: string; type: string; content?: string } | null
  isLoading: boolean
  onClose: () => void
}

function ReportPreviewModal({ report, isLoading, onClose }: ReportPreviewModalProps) {
  if (!report && !isLoading) return null

  const handleDownload = () => {
    if (report) {
      window.open(`/api/reports/download/${report.id}`, '_blank')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface-elevated rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden border border-border">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-text-primary">{report?.name || '加载中...'}</h3>
          <div className="flex gap-2">
            {report && (
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-accent text-background rounded-xl text-sm font-medium hover:bg-accent-bright transition-colors"
              >
                下载报告
              </button>
            )}
            <button
              onClick={onClose}
              className="px-4 py-2 bg-surface rounded-xl text-text-secondary text-sm hover:bg-surface-hover transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={24} className="text-accent animate-spin" />
              <span className="ml-2 text-text-muted">报告内容加载中...</span>
            </div>
          ) : report?.content ? (
            <div dangerouslySetInnerHTML={{ __html: report.content }} />
          ) : (
            <div className="text-center text-text-muted py-12">报告内容加载中...</div>
          )}
        </div>
      </div>
    </div>
  )
}

function FileUploadZone({ onUpload, uploadState }: { onUpload: (file: File) => void; uploadState: UploadState }) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(e.type === 'dragenter')
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && uploadState === 'idle') {
      await onUpload(file)
    }
  }

  const handleUpload = async (file: File) => {
    if (uploadState === 'idle') {
      await onUpload(file)
    }
  }

  const isDisabled = uploadState !== 'idle'

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => !isDisabled && inputRef.current?.click()}
      className={`
        relative overflow-hidden rounded-2xl border-2 border-dashed cursor-pointer transition-all duration-300
        ${isDragging && !isDisabled
          ? 'border-accent bg-accent/10'
          : isDisabled
          ? 'border-border bg-surface-elevated/50 cursor-not-allowed'
          : 'border-border hover:border-accent/50 hover:bg-surface-elevated'
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        className="hidden"
        disabled={isDisabled}
        onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
      />

      <div className="p-12 text-center">
        <div className={`
          w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center transition-colors
          ${isDragging ? 'bg-accent/20' : 'bg-surface'}
        `}>
          {uploadState === 'uploading' ? (
            <Loader2 size={28} className="text-accent animate-spin" />
          ) : uploadState === 'thinking' || uploadState === 'done' ? (
            <Sparkles size={28} className="text-accent" />
          ) : uploadState === 'error' ? (
            <AlertCircle size={28} className="text-error" />
          ) : (
            <Upload size={28} className={isDragging ? 'text-accent' : 'text-text-muted'} />
          )}
        </div>

        <div className="text-lg font-semibold text-text-primary mb-2">
          {uploadState === 'idle' && (isDragging ? '释放以上传' : '拖拽文件到这里')}
          {uploadState === 'uploading' && '上传中...'}
          {uploadState === 'thinking' && '分析中...'}
          {uploadState === 'done' && '上传成功!'}
          {uploadState === 'error' && '上传失败'}
        </div>
        <div className="text-sm text-text-muted mb-4">
          {uploadState === 'idle' && '或点击选择文件'}
          {uploadState === 'uploading' && '请稍候'}
          {uploadState === 'thinking' && '正在进行深度分析...'}
          {uploadState === 'done' && '数据已准备好'}
          {uploadState === 'error' && '请重试'}
        </div>

        {uploadState === 'idle' && (
          <div className="flex justify-center gap-2">
            <span className="px-3 py-1 rounded-full bg-surface text-xs text-text-muted">CSV</span>
            <span className="px-3 py-1 rounded-full bg-surface text-xs text-text-muted">Excel</span>
            <span className="px-3 py-1 rounded-full bg-surface text-xs text-text-muted">JSON</span>
          </div>
        )}
      </div>

      {isDragging && !isDisabled && (
        <div className="absolute inset-0 border-2 border-accent rounded-2xl animate-pulse" />
      )}
    </div>
  )
}

function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      id: '1',
      role: 'assistant',
      content: '你好！我是你的电商数据助手。有什么关于生意的问题可以问我，比如"最近转化率怎么样？"或者"有哪些高价值客户？"',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: ChatMessageType = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    try {
      const response = await conversationApi.chat(input, messages.map(m => ({
        role: m.role,
        content: m.content,
      })))

      const aiMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (err) {
      // Fallback to mock response if API fails
      const responses = [
        '根据你的数据分析，加购到下单的转化率本周下降了15%，这是主要流失环节。',
        '你的高价值客户占总体12%，这些客户最近30天有购买且购买频次高。',
        '对比上月数据，你的整体转化率提升了3%，但客单价下降了8%。',
      ]
      const aiMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, aiMessage])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-accent/10">
            <MessageCircle size={20} className="text-accent" />
          </div>
          <div>
            <div className="font-semibold text-text-primary">智能问答</div>
            <div className="text-xs text-text-muted">基于你的数据分析</div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} chat-message`}
          >
            <div
              className={`
                max-w-[85%] rounded-2xl px-4 py-3
                ${message.role === 'user'
                  ? 'bg-accent text-background'
                  : 'bg-surface-elevated border border-border'
                }
              `}
            >
              {message.role === 'assistant' && (
                <div className="flex items-center gap-2 mb-2 text-xs text-accent">
                  <Sparkles size={12} />
                  AI 助手
                </div>
              )}
              <p className={`text-sm leading-relaxed ${message.role === 'user' ? 'font-medium' : ''}`}>
                {message.content}
              </p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start chat-message">
            <div className="bg-surface-elevated border border-border rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-accent animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-xs text-text-muted">AI 思考中...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 bg-surface-elevated rounded-2xl px-4 py-2 border border-border focus-within:border-accent/50 transition-colors">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="问我任何关于你生意的问题..."
            className="flex-1 bg-transparent text-text-primary placeholder:text-text-muted py-2 outline-none"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="p-2 rounded-xl bg-accent/10 text-accent hover:bg-accent/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
        <div className="text-xs text-text-muted text-center mt-2">
          AI 助手会尝试理解你的问题，但可能会有误差
        </div>
      </div>
    </div>
  )
}

function ReportsList({ onPreviewReport }: { onPreviewReport?: (reportId: string) => void }) {
  const { data, loading } = useApiData(() => reportApi.list().then(r => r.reports))

  const handleReportClick = (reportId: string) => {
    if (onPreviewReport) {
      onPreviewReport(reportId)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary">我的报告</h2>
        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent text-background text-sm font-semibold hover:bg-accent-bright transition-colors">
          <Plus size={16} />
          新建报告
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="text-accent animate-spin" />
        </div>
      ) : (
        <div className="grid gap-3">
          {data?.map((report) => (
            <div
              key={report.id}
              onClick={() => handleReportClick(report.id)}
              className="bg-surface-elevated rounded-xl p-4 border border-border hover:border-accent/30 transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-accent/10">
                    <FileText size={18} className="text-accent" />
                  </div>
                  <div>
                    <div className="font-medium text-text-primary">{report.name}</div>
                    <div className="text-xs text-text-muted">{report.date}</div>
                  </div>
                </div>
                <ChevronRight size={18} className="text-text-muted group-hover:text-accent transition-colors" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ProfilePage() {
  const menuItems = [
    { icon: <Database size={20} />, label: '数据源管理', desc: '管理已连接的数据' },
    { icon: <Bell size={20} />, label: '通知设置', desc: '推送和提醒' },
    { icon: <Settings size={20} />, label: '账号设置', desc: '个人信息' },
    { icon: <LogOut size={20} />, label: '退出登录', desc: '', danger: true },
  ]

  return (
    <div className="p-4 space-y-6">
      <div className="flex items-center gap-4 p-4 bg-surface-elevated rounded-2xl border border-border">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-accent-muted flex items-center justify-center text-2xl font-bold text-background">
          店
        </div>
        <div>
          <div className="text-lg font-semibold text-text-primary">店铺名称</div>
          <div className="text-sm text-text-muted">free @ pro</div>
        </div>
      </div>

      <div className="bg-surface-elevated rounded-2xl p-4 border border-border">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-text-muted">本月 AI 查询</span>
          <span className="text-sm font-medium text-text-primary">23 / 30</span>
        </div>
        <div className="h-2 bg-surface rounded-full overflow-hidden">
          <div className="h-full bg-accent rounded-full" style={{ width: '76%' }} />
        </div>
        <button className="w-full mt-4 py-3 rounded-xl bg-accent/10 text-accent text-sm font-medium hover:bg-accent/20 transition-colors">
          升级到专业版
        </button>
      </div>

      <div className="space-y-2">
        {menuItems.map((item) => (
          <button
            key={item.label}
            className={`w-full flex items-center gap-4 p-4 rounded-xl transition-colors ${
              item.danger
                ? 'hover:bg-error/10 text-error'
                : 'hover:bg-surface-elevated text-text-primary'
            }`}
          >
            <div className={`p-2 rounded-xl ${item.danger ? 'bg-error/10' : 'bg-surface'}`}>
              {item.icon}
            </div>
            <div className="flex-1 text-left">
              <div className="font-medium">{item.label}</div>
              {item.desc && <div className="text-xs text-text-muted">{item.desc}</div>}
            </div>
            <ChevronRight size={18} className="text-text-muted" />
          </button>
        ))}
      </div>
    </div>
  )
}

function DashboardContent() {
  const { data: overview, loading, error, refetch } = useApiData(() => analyticsApi.getOverview())
  const [funnelInsight, setFunnelInsight] = useState('')
  const [insightLoading, setInsightLoading] = useState(false)

  // Upload state management
  const [uploadState, setUploadState] = useState<UploadState>('idle')
  const [datasourceId, setDatasourceId] = useState<number | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Analysis results from polling
  const [analysisFunnelData, setAnalysisFunnelData] = useState<FunnelStep[]>([])
  const [analysisRFMData, setAnalysisRFMData] = useState<RFMData[]>([])
  const [analysisOverviewData, setAnalysisOverviewData] = useState<OverviewData | null>(null)

  // Report modal state
  const [showReportModal, setShowReportModal] = useState(false)
  const [reportPreview, setReportPreview] = useState<{ id: string; name: string; type: string; content?: string } | null>(null)
  const [reportPreviewLoading, setReportPreviewLoading] = useState(false)

  // Funnel data from API
  const { data: funnelData, loading: funnelLoading, error: funnelError, refetch: refetchFunnel } = useApiData(async () => {
    // Use empty events for now - in production, fetch actual events from datasource
    const result = await analyticsApi.analyzeFunnel([])
    // Transform API FunnelStep to component FunnelStep
    return result.funnel.map(step => ({
      name: step.step,
      count: step.user_count,
      rate: step.conversion_rate,
      dropoff: step.dropoff_rate,
    })) as FunnelStep[]
  }, [])

  // RFM data from API
  const { data: rfmData, loading: rfmLoading, error: rfmError, refetch: refetchRFM } = useApiData(async () => {
    // Use empty orders for now - in production, fetch actual orders from datasource
    const result = await analyticsApi.analyzeRFM([])
    // Transform API RFMData to component format
    const colors: Record<string, string> = {
      Champions: '#4ADE80',
      Loyal: '#60A5FA',
      Potential: '#E8B86D',
      'At Risk': '#F87171',
      Lost: '#6B7280',
    }
    return Object.entries(result.segment_distribution).map(([segment, count]) => ({
      segment,
      count,
      color: colors[segment] || '#6B7280',
    })) as RFMData[]
  }, [])

  const defaultInsight = '本月转化率较上月提升 2%，但加购率下降 15%。最大流失发生在"加购→下单"环节，流失率高达 67%。建议优化结算流程或增加限时优惠提升付款转化。'

  useEffect(() => {
    // Fetch AI insight
    const fetchInsight = async () => {
      setInsightLoading(true)
      try {
        const response = await conversationApi.generateInsight('dashboard', {
          metrics: overview?.metrics || {},
          funnel: { funnel: funnelData || [] },
          rfm: { segment_distribution: rfmData ? Object.fromEntries(rfmData.map(d => [d.segment, d.count])) : {} },
        })
        setFunnelInsight(response.insight)
      } catch (err) {
        setFunnelInsight(defaultInsight)
      } finally {
        setInsightLoading(false)
      }
    }

    if (overview) {
      fetchInsight()
    }
  }, [overview, funnelData, rfmData])

  const handleFileUpload = async (file: File) => {
    setUploadState('uploading')
    setUploadError(null)

    try {
      // Step 1: Upload file
      const result = await datasourcesApi.upload(file.name, file)

      // Step 2: Analysis started, show thinking animation
      if (result.datasource_id) {
        setDatasourceId(result.datasource_id)
        setUploadState('thinking')

        // Start polling for results
        const pollResult = async () => {
          let attempts = 0
          const maxAttempts = 60 // 60秒超时

          const poll = async () => {
            if (attempts >= maxAttempts) {
              setUploadState('error')
              setUploadError('分析耗时较长，请稍后刷新页面查看')
              return
            }

            try {
              const res = await analyticsApi.getAnalysisResult(result.datasource_id)
              if (res.status === 'completed') {
                // Transform and set analysis results
                if (res.funnel_result) {
                  const transformedFunnel = res.funnel_result.map((step: any) => ({
                    name: step.step,
                    count: step.user_count,
                    rate: step.conversion_rate,
                    dropoff: step.dropoff_rate,
                  }))
                  setAnalysisFunnelData(transformedFunnel)
                }
                if (res.rfm_result) {
                  const colors: Record<string, string> = {
                    Champions: '#4ADE80',
                    Loyal: '#60A5FA',
                    Potential: '#E8B86D',
                    'At Risk': '#F87171',
                    Lost: '#6B7280',
                  }
                  const transformedRFM = Object.entries(res.rfm_result.segment_distribution).map(
                    ([segment, count]: [string, any]) => ({
                      segment,
                      count,
                      color: colors[segment] || '#6B7280',
                    })
                  )
                  setAnalysisRFMData(transformedRFM)
                }
                if (res.overview) {
                  setAnalysisOverviewData(res.overview)
                }
                setUploadState('done')
              } else if (res.status === 'failed') {
                setUploadState('error')
                setUploadError(res.error || '分析失败')
              } else {
                attempts++
                setTimeout(poll, 1000)
              }
            } catch (err) {
              attempts++
              setTimeout(poll, 1000)
            }
          }

          await poll()
        }

        pollResult()
      }
    } catch (err: any) {
      setUploadError(err.message || '上传失败')
      setUploadState('error')
    }
  }

  const handleRetry = () => {
    setUploadState('idle')
    setUploadError(null)
  }

  const handleGenerateReport = async (reportType: string) => {
    setShowReportModal(false)
    setReportPreviewLoading(true)
    try {
      // Generate the report
      const generated = await reportApi.generate(reportType, {
        metrics: overview?.metrics || {},
        funnel: { funnel: funnelData || [] },
        rfm: { segment_distribution: rfmData ? Object.fromEntries(rfmData.map(d => [d.segment, d.count])) : {} },
      })
      // Fetch report details for preview
      const reportDetails = await reportApi.get(generated.id)
      setReportPreview({
        id: generated.id,
        name: generated.title,
        type: generated.type,
        content: reportDetails.content,
      })
    } catch (err) {
      console.error('Failed to generate report:', err)
    } finally {
      setReportPreviewLoading(false)
    }
  }

  const handleCloseReportPreview = () => {
    setReportPreview(null)
  }

  const metrics: MetricData[] = overview ? [
    { label: '访问量', value: overview.metrics.total_visits.toLocaleString(), change: overview.changes.visits_change, icon: <TrendingUp size={20} /> },
    { label: '订单数', value: overview.metrics.total_orders.toLocaleString(), change: overview.changes.orders_change, icon: <ShoppingCart size={20} /> },
    { label: '转化率', value: `${overview.metrics.conversion_rate}%`, change: overview.changes.conversion_change, icon: <BarChart3 size={20} /> },
    { label: '客户数', value: overview.metrics.total_customers.toLocaleString(), change: overview.changes.customers_change, icon: <Users size={20} /> },
  ] : [
    { label: '访问量', value: '-', icon: <TrendingUp size={20} /> },
    { label: '订单数', value: '-', icon: <ShoppingCart size={20} /> },
    { label: '转化率', value: '-', icon: <BarChart3 size={20} /> },
    { label: '客户数', value: '-', icon: <Users size={20} /> },
  ]

  return (
    <div className="space-y-6 p-4 pb-24">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">数据概览</h1>
          <p className="text-sm text-text-muted">最近30天数据</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={refetch}
            className="p-2 rounded-xl bg-surface-elevated border border-border hover:border-accent/30 transition-colors"
          >
            <RefreshCw size={18} className={`text-text-muted ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button className="p-2 rounded-xl bg-surface-elevated border border-border hover:border-accent/30 transition-colors">
            <Bell size={18} className="text-text-muted" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="text-accent animate-spin" />
        </div>
      ) : error ? (
        <div className="text-center py-12 text-error">
          <AlertCircle size={24} className="mx-auto mb-2" />
          <p className="text-sm">{error}</p>
          <button onClick={refetch} className="mt-2 text-sm text-accent hover:underline">
            重试
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3">
            {metrics.map((metric, index) => (
              <MetricCardComponent key={metric.label} metric={metric} index={index} />
            ))}
          </div>

          <AIInsightCard insight={funnelInsight || defaultInsight} loading={insightLoading} onGenerateReport={() => setShowReportModal(true)} />

          <div className="bg-surface-elevated rounded-2xl p-4 border border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-xl bg-info/10">
                <Upload size={18} className="text-info" />
              </div>
              <div>
                <div className="font-medium text-text-primary">上传新数据</div>
                <div className="text-xs text-text-muted">支持 CSV、Excel 文件</div>
              </div>
            </div>

            {uploadState === 'thinking' ? (
              <ThinkingAnimation
                estimatedDuration={10000}
                onComplete={() => {}}
              />
            ) : uploadState === 'error' ? (
              <div className="text-center py-6">
                <AlertCircle size={24} className="mx-auto mb-2 text-error" />
                <p className="text-sm text-error mb-4">{uploadError || '上传失败'}</p>
                <button
                  onClick={handleRetry}
                  className="px-4 py-2 rounded-xl bg-accent/10 text-accent text-sm font-medium hover:bg-accent/20 transition-colors"
                >
                  重试
                </button>
              </div>
            ) : (
              <FileUploadZone onUpload={handleFileUpload} uploadState={uploadState} />
            )}
          </div>

          <div className="bg-surface-elevated rounded-2xl p-4 border border-border">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-accent/10">
                  <TrendingUp size={18} className="text-accent" />
                </div>
                <div className="font-medium text-text-primary">转化漏斗</div>
              </div>
              <span className="text-xs text-error flex items-center gap-1">
                <AlertCircle size={12} />
                加购→下单流失严重
              </span>
            </div>
            {funnelLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={20} className="text-accent animate-spin" />
              </div>
            ) : funnelError ? (
              <div className="text-center py-6 text-error">
                <p className="text-sm">{funnelError}</p>
                <button onClick={refetchFunnel} className="mt-2 text-sm text-accent hover:underline">
                  重试
                </button>
              </div>
            ) : (analysisFunnelData.length > 0 || (funnelData && funnelData.length > 0)) ? (
              <FunnelChart steps={analysisFunnelData.length > 0 ? analysisFunnelData : funnelData!} />
            ) : (
              <div className="text-center py-8 text-text-muted text-sm">
                暂无漏斗数据，请上传数据后重试
              </div>
            )}
          </div>

          <div className="bg-surface-elevated rounded-2xl p-4 border border-border">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-accent/10">
                  <PieChart size={18} className="text-accent" />
                </div>
                <div className="font-medium text-text-primary">客户分层</div>
              </div>
              <span className="text-xs text-text-muted">RFM 模型</span>
            </div>
            {rfmLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={20} className="text-accent animate-spin" />
              </div>
            ) : rfmError ? (
              <div className="text-center py-6 text-error">
                <p className="text-sm">{rfmError}</p>
                <button onClick={refetchRFM} className="mt-2 text-sm text-accent hover:underline">
                  重试
                </button>
              </div>
            ) : (analysisRFMData.length > 0 || (rfmData && rfmData.length > 0)) ? (
              <RFMDistribution data={analysisRFMData.length > 0 ? analysisRFMData : rfmData!} />
            ) : (
              <div className="text-center py-8 text-text-muted text-sm">
                暂无RFM数据，请上传数据后重试
              </div>
            )}
          </div>

          {/* Report Modals */}
          <ReportGenerateModal
            isOpen={showReportModal}
            onClose={() => setShowReportModal(false)}
            onGenerate={handleGenerateReport}
          />
          <ReportPreviewModal
            report={reportPreview}
            isLoading={reportPreviewLoading}
            onClose={handleCloseReportPreview}
          />
        </>
      )}
    </div>
  )
}

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<Tab>('home')
  const [reportPreview, setReportPreview] = useState<{ id: string; name: string; type: string; content?: string } | null>(null)
  const [reportPreviewLoading, setReportPreviewLoading] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)

  // Check auth status on mount
  useEffect(() => {
    const token = getToken()
    if (!token) {
      window.location.href = '/auth'
    } else {
      setIsAuthenticated(true)
      setAuthChecked(true)
    }
  }, [])

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 size={24} className="text-accent animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  const handlePreviewReport = async (reportId: string) => {
    setReportPreviewLoading(true)
    try {
      const reportDetails = await reportApi.get(reportId)
      // Find the report in the list to get its name
      setReportPreview({
        id: reportId,
        name: reportDetails.name,
        type: reportDetails.type,
        content: reportDetails.content,
      })
    } catch (err) {
      console.error('Failed to load report:', err)
    } finally {
      setReportPreviewLoading(false)
    }
  }

  const handleCloseReportPreview = () => {
    setReportPreview(null)
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="h-12 bg-background" />
      <div className="max-w-lg mx-auto">
        {activeTab === 'home' && <DashboardContent />}
        {activeTab === 'reports' && <ReportsList onPreviewReport={handlePreviewReport} />}
        {activeTab === 'chat' && <div className="h-[calc(100vh-8rem)]"><ChatInterface /></div>}
        {activeTab === 'profile' && <ProfilePage />}
        <ReportPreviewModal
          report={reportPreview}
          isLoading={reportPreviewLoading}
          onClose={handleCloseReportPreview}
        />
      </div>
      <BottomTabs active={activeTab} onChange={setActiveTab} />
    </main>
  )
}
