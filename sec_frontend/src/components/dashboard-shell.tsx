import type React from "react"

interface DashboardShellProps {
  children: React.ReactNode
  className?: string // Allow additional class names for customization
}

export function DashboardShell({ children, className }: DashboardShellProps) {
  return (
    <div className={`flex min-h-screen flex-col ${className || ""}`}>
      <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">{children}</main>
    </div>
  )
}

