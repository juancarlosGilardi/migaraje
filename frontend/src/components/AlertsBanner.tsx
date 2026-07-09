import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { Alert, AlertStatus } from '../api/types'

const STATUS_COLOR: Record<AlertStatus, string> = {
  overdue: 'var(--color-red)',
  critical: 'var(--color-red)',
  reminder: 'var(--color-amber)',
  warn: 'var(--color-amber)',
  notice: 'var(--color-cyan)',
}

const KIND_ICON: Record<Alert['kind'], string> = {
  plan: '🔧',
  document: '🪪',
  driver: '🪪',
  odometer: '📷',
}

function targetPath(alert: Alert): string {
  if (alert.kind === 'plan') return `/vehicles/${alert.vehicle_id}`
  if (alert.kind === 'odometer') return `/vehicles/${alert.vehicle_id}`
  return '/papeles'
}

export default function AlertsBanner() {
  const navigate = useNavigate()
  const alerts = useQuery({
    queryKey: ['alerts'],
    queryFn: () => api<Alert[]>('/api/alerts'),
  })

  if (!alerts.data || alerts.data.length === 0) return null

  return (
    <div className="mb-4 flex flex-col gap-2">
      {alerts.data.map((a, i) => {
        const color = STATUS_COLOR[a.status]
        return (
          <button
            key={i}
            type="button"
            onClick={() => navigate(targetPath(a))}
            className="flex w-full items-center gap-2.5 rounded-xl border px-3 py-2.5 text-left"
            style={{
              borderColor: `color-mix(in srgb, ${color} 40%, transparent)`,
              background: `color-mix(in srgb, ${color} 8%, transparent)`,
            }}
          >
            <span className="text-base">{KIND_ICON[a.kind]}</span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-xs font-bold" style={{ color }}>
                {a.title}
              </span>
              <span className="block text-[11px] text-muted">{a.message}</span>
            </span>
            <span className="shrink-0 text-muted">›</span>
          </button>
        )
      })}
    </div>
  )
}
