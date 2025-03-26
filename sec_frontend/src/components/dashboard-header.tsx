import type React from "react"
import clsx from "clsx"

interface DashboardHeaderProps {
  heading: string
  text?: string
  children?: React.ReactNode
  className?: string // Allow additional class names for customization
}

export function DashboardHeader({ heading, text, children, className }: DashboardHeaderProps) {
  return (
    <header className={clsx("flex items-center justify-between px-2", className)}>
      <div className="grid gap-1">
        <h1 className="font-heading text-3xl md:text-4xl">{heading}</h1>
        {text && <p className="text-lg text-muted-foreground">{text}</p>}
      </div>
      {children && <div className="flex items-center">{children}</div>}
    </header>
  )
}

