'use client'

import React, { useEffect, useState } from 'react'

interface ThinkingAnimationProps {
  onComplete?: () => void
  estimatedDuration?: number // 预估时间(ms)，用于进度条
}

const THINKING_MESSAGES = [
  { text: '正在解析您的数据文件...', progress: 10 },
  { text: '正在识别用户购买路径...', progress: 25 },
  { text: '正在计算转化漏斗...', progress: 45 },
  { text: '正在构建用户画像...', progress: 60 },
  { text: '正在分析高价值客户群体...', progress: 75 },
  { text: '正在生成RFM分层模型...', progress: 90 },
  { text: '正在优化分析结果...', progress: 98 },
  { text: '正在准备您的报告...', progress: 100 },
]

export default function ThinkingAnimation({
  onComplete,
  estimatedDuration = 8000,
}: ThinkingAnimationProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [displayedMessages, setDisplayedMessages] = useState<typeof THINKING_MESSAGES>([])
  const [progress, setProgress] = useState(0)
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    // 初始化显示第一条消息
    setDisplayedMessages([THINKING_MESSAGES[0]])

    const messageInterval = setInterval(() => {
      setCurrentIndex(prev => {
        const next = prev + 1
        if (next < THINKING_MESSAGES.length) {
          setDisplayedMessages(msgs => [...msgs.slice(-6), THINKING_MESSAGES[next]])
          return next
        }
        return prev
      })
    }, 900 + Math.random() * 400)

    // 进度条动画
    const startTime = Date.now()
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime
      const newProgress = Math.min((elapsed / estimatedDuration) * 100, 99)
      setProgress(newProgress)
    }, 50)

    // 完成
    setTimeout(() => {
      clearInterval(messageInterval)
      clearInterval(progressInterval)
      setProgress(100)
      setIsComplete(true)
      setTimeout(() => {
        onComplete?.()
      }, 500)
    }, estimatedDuration)

    return () => {
      clearInterval(messageInterval)
      clearInterval(progressInterval)
    }
  }, [estimatedDuration, onComplete])

  return (
    <div className="fixed inset-0 bg-surface/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-surface-elevated border border-border rounded-2xl p-8 w-full max-w-md mx-4 shadow-2xl">
        <div className="text-center mb-6">
          <div className="text-2xl font-medium text-text-primary mb-2">
            {isComplete ? '✓ 分析完成！' : '◉ 深度思考中...'}
          </div>
          <div className="text-sm text-text-secondary">
            {isComplete ? '正在跳转到结果...' : '请稍候'}
          </div>
        </div>

        <div className="space-y-1 mb-6">
          {displayedMessages.map((msg, idx) => {
            const isLast = idx === displayedMessages.length - 1 && !isComplete
            const isDone = displayedMessages.indexOf(msg) < displayedMessages.length - 1

            return (
              <div
                key={idx}
                className={`text-sm flex items-center gap-2 ${
                  isDone ? 'text-text-secondary' : 'text-text-primary'
                }`}
              >
                <span className="w-4">
                  {isDone ? '✓' : isLast ? '▸' : '○'}
                </span>
                <span>{msg.text}</span>
              </div>
            )
          })}
        </div>

        <div className="relative h-2 bg-surface rounded-full overflow-hidden">
          <div
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary to-primary/80 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="text-right text-xs text-text-secondary mt-1">
          {Math.round(progress)}%
        </div>
      </div>
    </div>
  )
}