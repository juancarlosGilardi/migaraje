import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { Driver, DocStatus, LegalDocument, Vehicle, VehicleDocuments } from '../api/types'

const inputCls =
  'w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-muted focus:border-cyan focus:outline-none'

const STATUS_COLOR: Record<DocStatus, string> = {
  ok: 'var(--color-green)',
  warn: 'var(--color-amber)',
  critical: 'var(--color-red)',
  overdue: 'var(--color-red)',
  unknown: 'var(--color-muted)',
}

function daysLabel(days: number | null): string {
  if (days === null) return ''
  if (days < 0) return `vencido hace ${-days} días`
  if (days === 0) return 'vence hoy'
  return `${days} días`
}

function fmtDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleDateString('es-PE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function DocCard({
  title,
  icon,
  status,
  headline,
  subline,
  onEdit,
}: {
  title: string
  icon: string
  status: DocStatus
  headline: string
  subline: string
  onEdit?: () => void
}) {
  const color = STATUS_COLOR[status]
  return (
    <div className="mb-2.5 rounded-2xl border border-line bg-card p-3.5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-semibold">
            {icon} {title}
          </p>
          <p className="mt-0.5 text-[11.5px] text-muted">{subline}</p>
        </div>
        <span
          className="shrink-0 whitespace-nowrap rounded-full border px-2.5 py-1 text-[11px] font-bold"
          style={{ color, borderColor: `color-mix(in srgb, ${color} 40%, transparent)`, background: `color-mix(in srgb, ${color} 10%, transparent)` }}
        >
          {headline}
        </span>
      </div>
      {onEdit && (
        <button
          type="button"
          onClick={onEdit}
          className="mt-2.5 rounded-full border border-line px-3 py-1.5 text-[11.5px] font-semibold text-muted hover:text-cyan"
        >
          Editar
        </button>
      )}
    </div>
  )
}

function DriverForm({ driver, onDone }: { driver?: Driver; onDone: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    name: driver?.name ?? '',
    license_class: driver?.license_class ?? 'A-I',
    license_expiry: driver?.license_expiry ?? '',
    birth_date: driver?.birth_date ?? '',
  })

  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: form.name,
        license_class: form.license_class,
        license_expiry: form.license_expiry || null,
        birth_date: form.birth_date || null,
      }
      return driver
        ? api(`/api/drivers/${driver.id}`, { method: 'PATCH', body: JSON.stringify(body) })
        : api('/api/drivers', { method: 'POST', body: JSON.stringify(body) })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drivers'] })
      onDone()
    },
  })
  const error = save.error as ApiError | null

  return (
    <form
      className="mb-2.5 flex flex-col gap-2 rounded-2xl border border-line bg-card p-3.5"
      onSubmit={(e) => {
        e.preventDefault()
        save.mutate()
      }}
    >
      <input
        className={inputCls}
        placeholder="Nombre del conductor"
        value={form.name}
        onChange={(e) => setForm({ ...form, name: e.target.value })}
        required
        minLength={2}
      />
      <div className="grid grid-cols-2 gap-2">
        <input
          className={inputCls}
          placeholder="Clase (A-I)"
          value={form.license_class}
          onChange={(e) => setForm({ ...form, license_class: e.target.value })}
        />
        <input
          className={inputCls}
          type="date"
          value={form.birth_date}
          onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
        />
      </div>
      <label className="text-[11px] text-muted">Vencimiento del brevete</label>
      <input
        className={inputCls}
        type="date"
        value={form.license_expiry}
        onChange={(e) => setForm({ ...form, license_expiry: e.target.value })}
      />
      {error && <p className="text-xs font-semibold text-red">{error.message}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={save.isPending}
          className="flex-1 rounded-xl bg-gradient-to-r from-cyan to-indigo px-4 py-2 text-sm font-bold text-[#04101F] disabled:opacity-60"
        >
          Guardar
        </button>
        <button type="button" onClick={onDone} className="rounded-xl border border-line px-4 py-2 text-sm font-semibold text-muted">
          Cancelar
        </button>
      </div>
    </form>
  )
}

function DriverSection() {
  const [adding, setAdding] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const drivers = useQuery({
    queryKey: ['drivers'],
    queryFn: () => api<Driver[]>('/api/drivers'),
  })

  return (
    <div className="mb-6">
      <h2 className="mb-2 text-[11px] font-bold uppercase tracking-widest text-muted">🪪 Conductores</h2>
      {drivers.data?.map((d) =>
        editingId === d.id ? (
          <DriverForm key={d.id} driver={d} onDone={() => setEditingId(null)} />
        ) : (
          <DocCard
            key={d.id}
            title={`${d.name} · licencia ${d.license_class}`}
            icon="🪪"
            status={d.has_data ? d.status : 'unknown'}
            headline={
              d.has_data
                ? daysLabel(d.days_remaining)
                : 'sin fecha registrada'
            }
            subline={
              d.license_expiry
                ? `Vence ${fmtDate(d.license_expiry)}${d.renewal_period_years ? ` · al renovar: vigencia de ${d.renewal_period_years} años` : ''}`
                : 'Agrega la fecha de vencimiento de tu brevete'
            }
            onEdit={() => setEditingId(d.id)}
          />
        ),
      )}
      {adding ? (
        <DriverForm onDone={() => setAdding(false)} />
      ) : (
        <button
          type="button"
          onClick={() => setAdding(true)}
          className="w-full rounded-2xl border-2 border-dashed border-muted/40 p-3 text-xs font-semibold text-muted hover:border-cyan/60 hover:text-cyan"
        >
          ＋ Agregar conductor
        </button>
      )}
    </div>
  )
}

function LegalDocForm({
  vehicleId,
  docType,
  doc,
  onDone,
}: {
  vehicleId: number
  docType: 'soat' | 'citv'
  doc: LegalDocument
  onDone: () => void
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    reference_number: doc.reference_number ?? '',
    expiry_date: doc.expiry_date ?? '',
  })

  const save = useMutation({
    mutationFn: () =>
      api(`/api/vehicles/${vehicleId}/documents/${docType}`, {
        method: 'PUT',
        body: JSON.stringify({
          reference_number: form.reference_number || null,
          expiry_date: form.expiry_date,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', vehicleId] })
      onDone()
    },
  })
  const error = save.error as ApiError | null

  return (
    <form
      className="mb-2.5 flex flex-col gap-2 rounded-2xl border border-line bg-card p-3.5"
      onSubmit={(e) => {
        e.preventDefault()
        save.mutate()
      }}
    >
      <p className="text-xs font-bold">{docType === 'soat' ? 'SOAT' : 'Revisión técnica (CITV)'}</p>
      <input
        className={inputCls}
        placeholder={docType === 'soat' ? 'N.º de póliza (opcional)' : 'N.º de certificado (opcional)'}
        value={form.reference_number}
        onChange={(e) => setForm({ ...form, reference_number: e.target.value })}
      />
      <label className="text-[11px] text-muted">Fecha de vencimiento</label>
      <input
        className={inputCls}
        type="date"
        value={form.expiry_date}
        onChange={(e) => setForm({ ...form, expiry_date: e.target.value })}
        required
      />
      {error && <p className="text-xs font-semibold text-red">{error.message}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={save.isPending}
          className="flex-1 rounded-xl bg-gradient-to-r from-cyan to-indigo px-4 py-2 text-sm font-bold text-[#04101F] disabled:opacity-60"
        >
          Guardar
        </button>
        <button type="button" onClick={onDone} className="rounded-xl border border-line px-4 py-2 text-sm font-semibold text-muted">
          Cancelar
        </button>
      </div>
    </form>
  )
}

function VehicleDocsSection({ vehicle }: { vehicle: Vehicle }) {
  const [editing, setEditing] = useState<'soat' | 'citv' | null>(null)

  const docs = useQuery({
    queryKey: ['documents', vehicle.id],
    queryFn: () => api<VehicleDocuments>(`/api/vehicles/${vehicle.id}/documents`),
  })

  if (docs.isPending) return null
  if (docs.isError) return <p className="text-xs text-red">No se pudo cargar Papeles de este auto.</p>

  const { soat, citv, impuesto_vehicular: impuesto } = docs.data!

  return (
    <div className="mb-6">
      <h2 className="mb-2 text-[11px] font-bold uppercase tracking-widest text-muted">
        🚙 {vehicle.brand} {vehicle.model} · {vehicle.plate}
      </h2>

      {editing === 'soat' ? (
        <LegalDocForm vehicleId={vehicle.id} docType="soat" doc={soat} onDone={() => setEditing(null)} />
      ) : (
        <DocCard
          title="SOAT"
          icon="🛡️"
          status={soat.has_data ? soat.status : 'unknown'}
          headline={soat.has_data ? daysLabel(soat.days_remaining) : 'sin registrar'}
          subline={soat.expiry_date ? `Vence ${fmtDate(soat.expiry_date)}` : 'Registra su fecha de vencimiento'}
          onEdit={() => setEditing('soat')}
        />
      )}

      {editing === 'citv' ? (
        <LegalDocForm vehicleId={vehicle.id} docType="citv" doc={citv} onDone={() => setEditing(null)} />
      ) : (
        <DocCard
          title="Revisión técnica (CITV)"
          icon="🔧"
          status={citv.status}
          headline={
            citv.has_data ? daysLabel(citv.days_remaining) : citv.first_due_year ? `desde ${citv.first_due_year}` : '—'
          }
          subline={citv.has_data ? `Vence ${fmtDate(citv.expiry_date)}` : (citv.message ?? '')}
          onEdit={() => setEditing('citv')}
        />
      )}

      <DocCard
        title="Impuesto vehicular"
        icon="🏛️"
        status={impuesto.applicable ? impuesto.status : 'unknown'}
        headline={
          impuesto.applicable
            ? impuesto.next_due_date
              ? daysLabel(impuesto.days_remaining)
              : `año ${impuesto.year_index} de 3`
            : impuesto.reason === 'expired'
              ? 'ya no aplica ✓'
              : 'aún no aplica'
        }
        subline={
          impuesto.message ??
          (vehicle.first_registration_year
            ? `Calculado desde tu año de 1.ª inscripción (${vehicle.first_registration_year})`
            : 'Agrega el año de 1.ª inscripción en el auto para calcularlo')
        }
      />
    </div>
  )
}

export default function Papeles() {
  const navigate = useNavigate()

  const vehicles = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => api<Vehicle[]>('/api/vehicles'),
  })

  return (
    <div className="mx-auto w-full max-w-md px-5 pb-16 pt-8">
      <button type="button" onClick={() => navigate('/')} className="text-xs text-muted">
        ‹ Garaje
      </button>
      <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">Papeles y vencimientos</h1>
      <p className="mt-1 text-xs text-muted">Del auto y del conductor · SOAT, revisión técnica, impuesto y brevete</p>

      <div className="mt-5">
        <DriverSection />
        {vehicles.isPending && <p className="text-sm text-muted">Cargando…</p>}
        {vehicles.data?.map((v) => <VehicleDocsSection key={v.id} vehicle={v} />)}
      </div>
    </div>
  )
}
