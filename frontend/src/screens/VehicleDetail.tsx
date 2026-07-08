import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { PlanItem, Vehicle } from '../api/types'

const inputCls =
  'w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-muted focus:border-cyan focus:outline-none'

const STATUS_COLOR: Record<string, string> = {
  ok: 'var(--color-green)',
  warn: 'var(--color-amber)',
  overdue: 'var(--color-red)',
}

function formatDue(item: PlanItem): string {
  if (item.km_remaining === null) {
    if (item.days_remaining === null) return ''
    return item.days_remaining >= 0 ? `en ${item.days_remaining} días` : `vencido hace ${-item.days_remaining} días`
  }
  return item.km_remaining >= 0
    ? `en ${item.km_remaining.toLocaleString('es-PE')} km`
    : `vencido hace ${(-item.km_remaining).toLocaleString('es-PE')} km`
}

function ruleText(item: PlanItem): string {
  const parts: string[] = []
  if (item.interval_km) parts.push(`Cada ${item.interval_km.toLocaleString('es-PE')} km`)
  if (item.interval_months) parts.push(`${item.interval_km ? 'o ' : 'cada '}${item.interval_months} meses`)
  if (item.last_service_km !== null) parts.push(`último: ${item.last_service_km.toLocaleString('es-PE')} km`)
  return parts.join(' · ')
}

function PlanItemCard({ vehicleId, item }: { vehicleId: number; item: PlanItem }) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [intervalKm, setIntervalKm] = useState(String(item.interval_km ?? ''))
  const [intervalMonths, setIntervalMonths] = useState(String(item.interval_months ?? ''))

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['plan', vehicleId] })

  const markDone = useMutation({
    mutationFn: () => api(`/api/vehicles/${vehicleId}/plan/${item.id}/mark-done`, { method: 'POST' }),
    onSuccess: invalidate,
  })

  const saveEdit = useMutation({
    mutationFn: () =>
      api(`/api/vehicles/${vehicleId}/plan/${item.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          interval_km: intervalKm ? Number(intervalKm) : null,
          interval_months: intervalMonths ? Number(intervalMonths) : null,
        }),
      }),
    onSuccess: () => {
      invalidate()
      setEditing(false)
    },
  })

  const color = STATUS_COLOR[item.status] ?? STATUS_COLOR.ok
  const barWidth = Math.min(100, Math.max(4, item.percent))

  return (
    <div className="mb-2.5 rounded-2xl border border-line bg-card p-3.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-semibold">{item.name}</span>
        <span className="whitespace-nowrap text-xs font-bold" style={{ color }}>
          {formatDue(item)}
        </span>
      </div>
      <p className="mt-0.5 text-[11.5px] text-muted">{ruleText(item)}</p>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted/15">
        <div className="h-full rounded-full" style={{ width: `${barWidth}%`, background: color }} />
      </div>
      {item.notes && <p className="mt-2 text-[11px] text-cyan">🛢 {item.notes}</p>}

      <div className="mt-2.5 flex gap-2">
        <button
          type="button"
          onClick={() => markDone.mutate()}
          disabled={markDone.isPending}
          className="rounded-full border border-cyan/40 bg-cyan/10 px-3 py-1.5 text-[11.5px] font-bold text-cyan disabled:opacity-60"
        >
          ✓ Marcar hecho hoy
        </button>
        <button
          type="button"
          onClick={() => setEditing(!editing)}
          className="rounded-full border border-line px-3 py-1.5 text-[11.5px] font-semibold text-muted"
        >
          Editar intervalo
        </button>
      </div>

      {editing && (
        <form
          className="mt-2.5 flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            saveEdit.mutate()
          }}
        >
          <input
            className={`${inputCls} w-32`}
            type="number"
            placeholder="Cada km"
            value={intervalKm}
            onChange={(e) => setIntervalKm(e.target.value)}
            min={1}
          />
          <input
            className={`${inputCls} w-32`}
            type="number"
            placeholder="Cada meses"
            value={intervalMonths}
            onChange={(e) => setIntervalMonths(e.target.value)}
            min={1}
          />
          <button
            type="submit"
            disabled={saveEdit.isPending}
            className="rounded-xl bg-gradient-to-r from-cyan to-indigo px-3 py-2 text-xs font-bold text-[#04101F]"
          >
            Guardar
          </button>
        </form>
      )}
    </div>
  )
}

export default function VehicleDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const vehicleId = Number(id)
  const [showKmForm, setShowKmForm] = useState(false)
  const [km, setKm] = useState('')

  const vehicle = useQuery({
    queryKey: ['vehicle', vehicleId],
    queryFn: () => api<Vehicle>(`/api/vehicles/${vehicleId}`),
  })
  const plan = useQuery({
    queryKey: ['plan', vehicleId],
    queryFn: () => api<PlanItem[]>(`/api/vehicles/${vehicleId}/plan`),
    enabled: vehicle.isSuccess,
  })

  const updateKm = useMutation({
    mutationFn: () =>
      api<Vehicle>(`/api/vehicles/${vehicleId}/odometer`, {
        method: 'POST',
        body: JSON.stringify({ km: Number(km) }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicle', vehicleId] })
      queryClient.invalidateQueries({ queryKey: ['plan', vehicleId] })
      queryClient.invalidateQueries({ queryKey: ['vehicles'] })
      setShowKmForm(false)
      setKm('')
    },
  })
  const kmError = updateKm.error as ApiError | null

  if (vehicle.isPending) {
    return <p className="p-8 text-center text-sm text-muted">Cargando…</p>
  }
  if (vehicle.isError) {
    return <p className="p-8 text-center text-sm font-semibold text-red">No se pudo cargar el vehículo.</p>
  }

  const v = vehicle.data
  const spec = v.spec

  return (
    <div className="mx-auto w-full max-w-md px-5 pb-16 pt-8">
      <button type="button" onClick={() => navigate('/')} className="text-xs text-muted">
        ‹ Garaje
      </button>
      <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">
        {v.brand} {v.model} {v.year}
      </h1>
      <p className="mt-0.5 flex items-center gap-2 text-xs text-muted">
        <span className="rounded-md border border-line bg-bg/60 px-1.5 py-0.5 font-bold tracking-widest">
          {v.plate}
        </span>
        {v.fuel}
      </p>

      <div className="mt-4 rounded-2xl border border-line bg-gradient-to-br from-card2 to-card p-4.5 text-center">
        <p className="text-[11px] font-bold uppercase tracking-widest text-muted">Kilometraje actual</p>
        <p className="mt-1 font-display text-4xl font-extrabold tracking-tight">
          {v.current_km.toLocaleString('es-PE')} <small className="text-base font-semibold text-muted">km</small>
        </p>
        <button
          type="button"
          onClick={() => setShowKmForm(!showKmForm)}
          className="mt-2.5 rounded-full border border-cyan/40 bg-cyan/10 px-4 py-1.5 text-xs font-bold text-cyan"
        >
          ↻ Actualizar kilometraje
        </button>
        {showKmForm && (
          <form
            className="mt-3 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              updateKm.mutate()
            }}
          >
            <input
              className={inputCls}
              type="number"
              min={v.current_km}
              placeholder={`≥ ${v.current_km.toLocaleString('es-PE')}`}
              value={km}
              onChange={(e) => setKm(e.target.value)}
              required
              autoFocus
            />
            <button
              type="submit"
              disabled={updateKm.isPending}
              className="shrink-0 rounded-xl bg-gradient-to-r from-cyan to-indigo px-4 text-sm font-bold text-[#04101F]"
            >
              Guardar
            </button>
          </form>
        )}
        {kmError && <p className="mt-2 text-xs font-semibold text-red">{kmError.message}</p>}
      </div>

      {spec && (
        <>
          <h2 className="mt-5 mb-2 text-sm font-bold">Ficha de tu auto</h2>
          <div className="flex flex-wrap gap-2">
            {spec.oil?.viscosity && (
              <span className="rounded-md border border-line bg-bg/50 px-2.5 py-1.5 text-[11px] font-semibold text-muted">
                🛢 Aceite: <b className="text-ink">{spec.oil.viscosity}</b>
                {spec.oil.capacity_liters ? ` (${spec.oil.capacity_liters} L)` : ''}
              </span>
            )}
            {spec.tires?.size && (
              <span className="rounded-md border border-line bg-bg/50 px-2.5 py-1.5 text-[11px] font-semibold text-muted">
                🛞 {spec.tires.size}
                {spec.tires.psi ? ` · ${spec.tires.psi} psi` : ''}
              </span>
            )}
            {spec.battery?.ah && (
              <span className="rounded-md border border-line bg-bg/50 px-2.5 py-1.5 text-[11px] font-semibold text-muted">
                🔋 {spec.battery.ah} Ah
              </span>
            )}
            {spec.fuel?.type && (
              <span className="rounded-md border border-line bg-bg/50 px-2.5 py-1.5 text-[11px] font-semibold text-muted">
                ⛽ {spec.fuel.type} {spec.fuel.octane ?? ''}
              </span>
            )}
          </div>
          {spec.oil?.note && <p className="mt-2 text-[11px] text-muted">{spec.oil.note}</p>}
        </>
      )}

      <h2 className="mt-5 mb-2 text-sm font-bold">Plan de mantenimiento</h2>
      {plan.isPending && <p className="text-sm text-muted">Cargando plan…</p>}
      {plan.data?.map((item) => <PlanItemCard key={item.id} vehicleId={vehicleId} item={item} />)}
    </div>
  )
}
