export type User = {
  id: number
  email: string
  name: string
}

export type TokenOut = {
  access_token: string
  token_type: string
  user: User
}

export type VehicleSpec = {
  oil?: { viscosity: string | null; api_norm: string | null; capacity_liters: number | null; note?: string }
  tires?: { size: string | null; psi: number | null }
  battery?: { ah: number | null }
  fuel?: { type: string | null; octane: string | null }
}

export type Vehicle = {
  id: number
  brand: string
  model: string
  year: number
  plate: string
  fuel: string
  first_registration_year: number | null
  current_km: number
  spec: VehicleSpec | null
}

export type PlanItemStatus = 'ok' | 'warn' | 'overdue'

export type PlanItem = {
  id: number
  name: string
  interval_km: number | null
  interval_months: number | null
  last_service_km: number | null
  last_service_date: string | null
  notes: string | null
  due_km: number | null
  km_remaining: number | null
  due_date: string | null
  days_remaining: number | null
  percent: number
  status: PlanItemStatus
}
