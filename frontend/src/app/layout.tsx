import './globals.css'

export const metadata = {
  title: '智数 - 电商数据分析助手',
  description: '让没有数据分析能力的电商卖家，轻松读懂自己的生意',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen antialiased">
        {children}
      </body>
    </html>
  )
}
