import { useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { InvoicePreview, Vehicle } from '../api/types'

const inputCls =
  'w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-muted focus:border-cyan focus:outline-none'

export default function UploadInvoice() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const vehicleId = Number(id)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [preview, setPreview] = useState<InvoicePreview | null>(null)
  const [form, setForm] = useState({
    service_date: new Date().toISOString().slice(0, 10),
    km: '',
    service_type: '',
    cost: '',
    workshop: '',
    ruc: '',
  })

  const vehicle = useQuery({
    queryKey: ['vehicle', vehicleId],
    queryFn: () => api<Vehicle>(`/api/vehicles/${vehicleId}`),
  })

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData()
      body.append('file', file)
      return api<InvoicePreview>(`/api/vehicles/${vehicleId}/services/upload`, {
        method: 'POST',
        body,
      })
    },
    onSuccess: (data) => {
      setPreview(data)
      setForm({
        service_date: data.issue_date ?? new Date().toISOString().slice(0, 10),
        km: '',
        service_type: data.suggested_service_type ?? '',
        cost: data.total !== null ? String(data.total) : '',
        workshop: data.supplier_name ?? '',
        ruc: data.supplier_ruc ?? '',
      })
    },
  })
  const uploadError = upload.error as ApiError | null

  const confirm = useMutation({
    mutationFn: () =>
      api(`/api/vehicles/${vehicleId}/services`, {
        method: 'POST',
        body: JSON.stringify({
          upload_token: preview?.upload_token ?? null,
          service_date: form.service_date,
          km: form.km ? Number(form.km) : null,
          service_type: form.service_type,
          cost: form.cost ? Number(form.cost) : null,
          workshop: form.workshop || null,
          ruc: form.ruc || null,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['services', vehicleId] })
      navigate(`/vehicles/${vehicleId}/history`)
    },
  })
  const confirmError = confirm.error as ApiError | null

  const handleFile = (file: File | null | undefined) => {
    if (!file) return
    setPreview(null)
    upload.mutate(file)
  }

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [field]: e.target.value })

  return (
    <div className="mx-auto w-full max-w-md px-5 pb-24 pt-8">
      <button type="button" onClick={() => navigate(`/vehicles/${vehicleId}/history`)} className="text-xs text-muted">
        ‹ Historial
      </button>
      <h1 className="mt-1 font-display text-3xl font-bold tracking-tight">Nueva factura</h1>
      <p className="mt-0.5 text-xs text-muted">Sube el comprobante de tu último servicio</p>

      {!preview && (
        <div
          onClick={() => fileInputRef.current?.click()}
          className="mt-5 cursor-pointer rounded-2xl border-2 border-dashed border-line p-8 text-center hover:border-cyan/50"
        >
          <div className="text-4xl">🧾</div>
          <p className="mt-2 text-sm font-bold">Arrastra tu PDF o XML aquí</p>
          <p className="mt-1 text-[11.5px] text-muted">
            Sirve para mantenimientos, SOAT o revisión técnica.
            <br />
            Si es XML (SUNAT), MiGaraje lee y registra todo por ti.
            <br />
            <b className="text-cyan">▶ Haz clic para elegir el archivo</b>
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.xml,application/pdf,text/xml,application/xml"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>
      )}

      {upload.isPending && (
        <div className="mt-5 rounded-2xl border border-line bg-card p-8 text-center">
          <div className="mx-auto size-8 animate-spin rounded-full border-2 border-cyan/30 border-t-cyan" />
          <p className="mt-3 text-sm font-bold">Leyendo factura electrónica…</p>
          <p className="mt-1 text-[11.5px] text-muted">
            Formato UBL 2.1 · SUNAT · extrayendo emisor, fecha, ítems y total
          </p>
        </div>
      )}

      {uploadError && <p className="mt-3 text-sm font-semibold text-red">{uploadError.message}</p>}

      {preview && (
        <div className="mt-5">
          {preview.is_xml && preview.parse_error && (
            <p className="rounded-xl border border-amber/30 bg-amber/10 p-3 text-[11.5px] font-semibold text-amber">
              No se pudo leer el XML automáticamente ({preview.parse_error}). Completa los datos a mano.
            </p>
          )}

          {preview.is_xml && !preview.parse_error && (
            <>
              <p className="text-[11.5px] font-bold text-green">✓ Factura electrónica detectada (UBL 2.1 · SUNAT)</p>
              <div className="mt-2 rounded-2xl border border-line bg-card p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-bold">{preview.supplier_name}</p>
                    <p className="text-[11px] text-muted">
                      RUC {preview.supplier_ruc} {preview.invoice_number ? `· ${preview.invoice_number}` : ''}
                    </p>
                  </div>
                  {preview.total !== null && (
                    <p className="whitespace-nowrap text-lg font-extrabold text-cyan">
                      S/ {preview.total.toLocaleString('es-PE', { minimumFractionDigits: 2 })}
                    </p>
                  )}
                </div>
                <div className="mt-3 space-y-1 border-t border-line pt-3 text-[11.5px]">
                  {preview.issue_date && (
                    <div className="flex justify-between">
                      <span className="text-muted">Fecha de emisión</span>
                      <span>{preview.issue_date}</span>
                    </div>
                  )}
                  {preview.currency && (
                    <div className="flex justify-between">
                      <span className="text-muted">Moneda</span>
                      <span>{preview.currency}</span>
                    </div>
                  )}
                  {preview.items.map((item, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="text-muted">{item.description}</span>
                      <span>S/ {item.amount.toLocaleString('es-PE', { minimumFractionDigits: 2 })}</span>
                    </div>
                  ))}
                </div>
              </div>

              {preview.suggested_service_type && (
                <div className="mt-3 rounded-2xl border border-cyan/25 bg-cyan/5 p-3.5">
                  <p className="text-[11px] font-bold text-cyan">✦ Sugerencia automática</p>
                  <p className="mt-1 text-[11.5px]">
                    Registrar como <b>"{preview.suggested_service_type}"</b>
                    {vehicle.data ? ` · ${vehicle.data.brand} ${vehicle.data.model}` : ''}
                  </p>
                  {preview.oil_match.message && (
                    <p
                      className="mt-1 text-[11px] font-semibold"
                      style={{ color: preview.oil_match.matches ? 'var(--color-green)' : 'var(--color-amber)' }}
                    >
                      {preview.oil_match.matches ? '✓ ' : '⚠ '}
                      {preview.oil_match.message}
                    </p>
                  )}
                </div>
              )}
            </>
          )}

          {!preview.is_xml && (
            <p className="rounded-xl border border-line bg-card p-3 text-[11.5px] text-muted">
              Los PDF no se leen automáticamente todavía (próximamente OCR). Completa los datos del servicio a mano.
            </p>
          )}

          <form
            className="mt-4 flex flex-col gap-2.5"
            onSubmit={(e) => {
              e.preventDefault()
              confirm.mutate()
            }}
          >
            <input
              className={inputCls}
              type="date"
              value={form.service_date}
              onChange={set('service_date')}
              required
            />
            <input
              className={inputCls}
              placeholder="Tipo de servicio"
              value={form.service_type}
              onChange={set('service_type')}
              required
              minLength={2}
            />
            <div className="grid grid-cols-2 gap-2">
              <input className={inputCls} type="number" placeholder="Kilometraje" value={form.km} onChange={set('km')} min={0} />
              <input className={inputCls} type="number" placeholder="Costo (S/)" value={form.cost} onChange={set('cost')} min={0} step="0.01" />
            </div>
            <input className={inputCls} placeholder="Taller / proveedor" value={form.workshop} onChange={set('workshop')} />
            <input className={inputCls} placeholder="RUC (opcional)" value={form.ruc} onChange={set('ruc')} />

            {confirmError && <p className="text-xs font-semibold text-red">{confirmError.message}</p>}

            <button
              type="submit"
              disabled={confirm.isPending}
              className="mt-1 rounded-xl bg-gradient-to-r from-cyan to-indigo px-4 py-2.5 text-sm font-bold text-[#04101F] disabled:opacity-60"
            >
              Confirmar y guardar en el historial
            </button>
            <button
              type="button"
              onClick={() => {
                setPreview(null)
                if (fileInputRef.current) fileInputRef.current.value = ''
              }}
              className="text-center text-xs font-semibold text-muted"
            >
              ↺ subir otro archivo
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
