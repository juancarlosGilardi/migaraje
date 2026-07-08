import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { Vehicle } from '../api/types'
import { clearSession, sessionUser } from '../auth'
import Combobox from '../components/Combobox'

const inputCls =
  'w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-muted focus:border-cyan focus:outline-none'

const FUELS = ['gasolina', 'diésel', 'GLP', 'GNV', 'híbrido', 'eléctrico']

function fuelEmoji(fuel: string) {
  if (fuel === 'eléctrico') return '⚡'
  if (fuel === 'híbrido') return '🍃'
  return '🚙'
}

function VehicleCard({ vehicle }: { vehicle: Vehicle }) {
  const queryClient = useQueryClient()
  const [editingKm, setEditingKm] = useState(false)
  const [km, setKm] = useState('')

  const updateKm = useMutation({
    mutationFn: () =>
      api<Vehicle>(`/api/vehicles/${vehicle.id}/odometer`, {
        method: 'POST',
        body: JSON.stringify({ km: Number(km) }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] })
      setEditingKm(false)
      setKm('')
    },
  })
  const error = updateKm.error as ApiError | null

  return (
    <div className="rounded-2xl border border-line bg-gradient-to-br from-card2 to-card p-4">
      <div className="flex items-center gap-3">
        <Link to={`/vehicles/${vehicle.id}`} className="flex min-w-0 flex-1 items-center gap-3">
          <div className="grid size-12 place-items-center rounded-xl border border-cyan/25 bg-cyan/10 text-2xl">
            {fuelEmoji(vehicle.fuel)}
          </div>
          <div className="min-w-0">
            <p className="truncate font-semibold">
              {vehicle.brand} {vehicle.model} {vehicle.year}
            </p>
            <p className="mt-0.5 flex items-center gap-2 text-xs text-muted">
              <span className="rounded-md border border-line bg-bg/60 px-1.5 py-0.5 font-bold tracking-widest">
                {vehicle.plate}
              </span>
              <span className="font-semibold text-ink">
                {vehicle.current_km.toLocaleString('es-PE')} km
              </span>
            </p>
          </div>
          <span className="shrink-0 text-lg text-muted">›</span>
        </Link>
        <button
          type="button"
          onClick={() => setEditingKm(!editingKm)}
          className="ml-1 shrink-0 rounded-full border border-cyan/40 bg-cyan/10 px-3 py-1.5 text-xs font-bold text-cyan"
        >
          ↻ km
        </button>
      </div>

      {editingKm && (
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
            min={vehicle.current_km}
            placeholder={`Kilometraje actual (≥ ${vehicle.current_km.toLocaleString('es-PE')})`}
            value={km}
            onChange={(e) => setKm(e.target.value)}
            required
            autoFocus
          />
          <button
            type="submit"
            disabled={updateKm.isPending}
            className="shrink-0 rounded-xl bg-gradient-to-r from-cyan to-indigo px-4 text-sm font-bold text-[#04101F] disabled:opacity-60"
          >
            Guardar
          </button>
        </form>
      )}
      {error && <p className="mt-2 text-xs font-semibold text-red">{error.message}</p>}
    </div>
  )
}

function AddVehicleForm({ onDone }: { onDone: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    brand: '',
    model: '',
    year: '',
    plate: '',
    fuel: 'gasolina',
    first_registration_year: '',
    initial_km: '',
  })

  const makes = useQuery({
    queryKey: ['catalog', 'makes'],
    queryFn: () => api<string[]>('/api/catalog/makes'),
    staleTime: 24 * 60 * 60 * 1000,
    retry: 1,
  })
  const models = useQuery({
    queryKey: ['catalog', 'models', form.brand],
    queryFn: () => api<string[]>(`/api/catalog/models?make=${encodeURIComponent(form.brand)}`),
    enabled: form.brand.trim().length > 1,
    staleTime: 24 * 60 * 60 * 1000,
    retry: 1,
  })

  const create = useMutation({
    mutationFn: () =>
      api<Vehicle>('/api/vehicles', {
        method: 'POST',
        body: JSON.stringify({
          brand: form.brand,
          model: form.model,
          year: Number(form.year),
          plate: form.plate,
          fuel: form.fuel,
          first_registration_year: form.first_registration_year
            ? Number(form.first_registration_year)
            : null,
          initial_km: form.initial_km ? Number(form.initial_km) : 0,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] })
      onDone()
    },
  })
  const error = create.error as ApiError | null
  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [field]: e.target.value })

  return (
    <form
      className="flex flex-col gap-3 rounded-2xl border border-line bg-card p-4"
      onSubmit={(e) => {
        e.preventDefault()
        create.mutate()
      }}
    >
      <p className="font-display text-sm font-bold">Nuevo auto</p>
      <div className="grid grid-cols-2 gap-2">
        <Combobox
          value={form.brand}
          onChange={(v) => setForm({ ...form, brand: v, model: '' })}
          options={makes.data ?? []}
          loading={makes.isPending}
          placeholder="Marca (Toyota)"
          required
          emptyHint={
            makes.isError ? 'Catálogo no disponible · escribe la marca' : 'Sin coincidencias · se usará el texto escrito'
          }
        />
        <Combobox
          value={form.model}
          onChange={(v) => setForm({ ...form, model: v })}
          options={models.data ?? []}
          loading={form.brand.trim().length > 1 && models.isPending}
          disabled={form.brand.trim().length <= 1}
          placeholder="Modelo (RAV4)"
          required
        />
        <input className={inputCls} type="number" placeholder="Año (2022)" value={form.year} onChange={set('year')} required min={1950} max={2035} />
        <input className={inputCls} placeholder="Placa (BGR-742)" value={form.plate} onChange={set('plate')} required minLength={6} />
        <select className={inputCls} value={form.fuel} onChange={set('fuel')}>
          {FUELS.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
        <input className={inputCls} type="number" placeholder="Km actual" value={form.initial_km} onChange={set('initial_km')} min={0} />
      </div>
      <input
        className={inputCls}
        type="number"
        placeholder="Año de 1.ª inscripción en Registros Públicos (opcional)"
        value={form.first_registration_year}
        onChange={set('first_registration_year')}
        min={1950}
        max={2035}
      />
      <p className="-mt-1 text-[11px] text-muted">
        La inscripción define hasta cuándo pagas el impuesto vehicular (lo usamos en Papeles).
      </p>
      {error && <p className="text-sm font-semibold text-red">{error.message}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={create.isPending}
          className="flex-1 rounded-xl bg-gradient-to-r from-cyan to-indigo px-4 py-2.5 text-sm font-bold text-[#04101F] disabled:opacity-60"
        >
          Guardar auto
        </button>
        <button
          type="button"
          onClick={onDone}
          className="rounded-xl border border-line px-4 py-2.5 text-sm font-semibold text-muted"
        >
          Cancelar
        </button>
      </div>
    </form>
  )
}

export default function Garage() {
  const navigate = useNavigate()
  const user = sessionUser()
  const [adding, setAdding] = useState(false)

  const vehicles = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => api<Vehicle[]>('/api/vehicles'),
    retry: (count, error) => (error as ApiError).status !== 401 && count < 2,
  })

  if (vehicles.isError && (vehicles.error as ApiError).status === 401) {
    clearSession()
    navigate('/login', { replace: true })
    return null
  }

  return (
    <div className="mx-auto w-full max-w-md px-5 pb-24 pt-8">
      <header className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted">Hola, {user?.name ?? 'conductor'} 👋</p>
          <h1 className="font-display text-3xl font-bold tracking-tight">Tu garaje</h1>
        </div>
        <button
          type="button"
          onClick={() => {
            clearSession()
            navigate('/login', { replace: true })
          }}
          className="rounded-full border border-line px-3 py-1.5 text-xs font-semibold text-muted hover:text-red"
        >
          Salir
        </button>
      </header>

      <div className="mt-5 flex flex-col gap-3">
        {vehicles.isPending && <p className="text-sm text-muted">Cargando tu garaje…</p>}
        {vehicles.isError && (
          <p className="text-sm font-semibold text-red">No se pudo cargar el garaje. ¿API activa?</p>
        )}

        {vehicles.data?.map((v) => <VehicleCard key={v.id} vehicle={v} />)}

        {vehicles.isSuccess && vehicles.data.length === 0 && !adding && (
          <div className="rounded-2xl border border-line bg-card p-6 text-center text-sm text-muted">
            Aún no tienes autos registrados. ¡Agrega el primero!
          </div>
        )}

        {adding ? (
          <AddVehicleForm onDone={() => setAdding(false)} />
        ) : (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="rounded-2xl border-2 border-dashed border-muted/40 p-4 text-sm font-semibold text-muted hover:border-cyan/60 hover:text-cyan"
          >
            ＋ Agregar auto
          </button>
        )}
      </div>
    </div>
  )
}
