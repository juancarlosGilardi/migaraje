import { useNavigate, useParams, Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError, API_URL } from '../api/client'
import type { ServiceRecord, Vehicle } from '../api/types'

function formatDate(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('es-PE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function ServiceCard({ vehicleId, record }: { vehicleId: number; record: ServiceRecord }) {
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: () => api(`/api/vehicles/${vehicleId}/services/${record.id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['services', vehicleId] }),
  })

  return (
    <div className="mb-2.5 rounded-2xl border border-line bg-card p-3.5">
      <div className="text-[11.5px] text-muted">
        {formatDate(record.service_date)}
        {record.km !== null ? ` · ${record.km.toLocaleString('es-PE')} km` : ''}
      </div>
      <div className="mt-0.5 flex items-baseline justify-between gap-2">
        <span className="text-sm font-semibold">{record.service_type}</span>
        {record.cost !== null && (
          <span className="whitespace-nowrap text-sm font-bold text-cyan">
            S/ {record.cost.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
          </span>
        )}
      </div>
      {record.workshop && <p className="mt-0.5 text-[11.5px] text-muted">{record.workshop}</p>}

      <div className="mt-2 flex items-center justify-between">
        <div className="flex gap-1.5">
          {record.has_pdf && (
            <a
              href={`${API_URL}/api/vehicles/${vehicleId}/services/${record.id}/file`}
              target="_blank"
              rel="noreferrer"
              className="rounded-md border border-line bg-bg/50 px-2 py-1 text-[10.5px] font-bold text-muted"
            >
              ⎙ PDF
            </a>
          )}
          {record.has_xml && (
            <a
              href={`${API_URL}/api/vehicles/${vehicleId}/services/${record.id}/file`}
              target="_blank"
              rel="noreferrer"
              className="rounded-md border border-line bg-bg/50 px-2 py-1 text-[10.5px] font-bold text-muted"
            >
              ⟨/⟩ XML
            </a>
          )}
        </div>
        <button
          type="button"
          onClick={() => {
            if (confirm('¿Eliminar este servicio del historial?')) remove.mutate()
          }}
          className="text-[11px] font-semibold text-muted hover:text-red"
        >
          Eliminar
        </button>
      </div>
    </div>
  )
}

export default function History() {
  const { id } = useParams()
  const navigate = useNavigate()
  const vehicleId = Number(id)

  const vehicle = useQuery({
    queryKey: ['vehicle', vehicleId],
    queryFn: () => api<Vehicle>(`/api/vehicles/${vehicleId}`),
  })
  const services = useQuery({
    queryKey: ['services', vehicleId],
    queryFn: () => api<ServiceRecord[]>(`/api/vehicles/${vehicleId}/services`),
  })

  const totalCost = services.data?.reduce((sum, r) => sum + (r.cost ?? 0), 0) ?? 0

  return (
    <div className="mx-auto w-full max-w-md px-5 pb-24 pt-8">
      <button type="button" onClick={() => navigate(`/vehicles/${vehicleId}`)} className="text-xs text-muted">
        ‹ {vehicle.data ? `${vehicle.data.brand} ${vehicle.data.model}` : 'Vehículo'}
      </button>
      <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">Historial</h1>

      {services.isSuccess && (
        <p className="mt-1 text-xs text-muted">
          <b className="text-ink">{services.data.length}</b> servicio{services.data.length === 1 ? '' : 's'} ·{' '}
          <b className="text-ink">S/ {totalCost.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</b>
        </p>
      )}

      <Link
        to={`/vehicles/${vehicleId}/upload`}
        className="mt-4 block rounded-2xl border-2 border-dashed border-cyan/40 p-4 text-center text-sm font-bold text-cyan"
      >
        ＋ Nueva factura
      </Link>

      <div className="mt-4">
        {services.isPending && <p className="text-sm text-muted">Cargando historial…</p>}
        {services.isError && (
          <p className="text-sm font-semibold text-red">
            {(services.error as ApiError).message ?? 'No se pudo cargar el historial.'}
          </p>
        )}
        {services.isSuccess && services.data.length === 0 && (
          <div className="rounded-2xl border border-line bg-card p-6 text-center text-sm text-muted">
            Aún no registraste ningún servicio. Sube tu primera factura.
          </div>
        )}
        {services.data?.map((r) => <ServiceCard key={r.id} vehicleId={vehicleId} record={r} />)}
      </div>
    </div>
  )
}
