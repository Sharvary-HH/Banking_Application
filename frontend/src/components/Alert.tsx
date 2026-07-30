import type { ReactNode } from 'react'

interface AlertProps {
  variant: 'error' | 'success'
  children: ReactNode
}

export default function Alert({ variant, children }: AlertProps) {
  const className = variant === 'error' ? 'alert-error' : 'alert-success'
  return (
    <div className={className} role={variant === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}
