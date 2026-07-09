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

// --- Historial de servicios / facturas ---
export type InvoiceItem = {
  description: string
  amount: number
}

export type OilMatch = {
  matches: boolean | null
  message: string | null
}

export type InvoicePreview = {
  upload_token: string
  filename: string
  is_xml: boolean
  invoice_number: string | null
  issue_date: string | null
  currency: string | null
  supplier_name: string | null
  supplier_ruc: string | null
  items: InvoiceItem[]
  total: number | null
  suggested_service_type: string | null
  oil_match: OilMatch
  parse_error: string | null
}

export type ServiceFile = {
  id: number
  filename: string
  content_type: string
  is_xml: boolean
}

export type ServiceRecord = {
  id: number
  service_date: string
  km: number | null
  service_type: string
  cost: number | null
  workshop: string | null
  ruc: string | null
  notes: string | null
  has_pdf: boolean
  has_xml: boolean
  files: ServiceFile[]
}

// --- Papeles: conductores y documentos legales ---
export type DocStatus = 'ok' | 'warn' | 'critical' | 'overdue' | 'unknown'

export type Driver = {
  id: number
  name: string
  license_class: string
  license_expiry: string | null
  birth_date: string | null
  has_data: boolean
  days_remaining: number | null
  status: DocStatus
  age: number | null
  renewal_period_years: number | null
}

export type LegalDocument = {
  doc_type: string
  reference_number: string | null
  expiry_date: string | null
  has_data: boolean
  has_history: boolean | null
  days_remaining: number | null
  status: DocStatus
  message: string | null
  first_due_year: number | null
}

export type ImpuestoVehicular = {
  applicable: boolean | null
  reason: string | null
  year_index: number | null
  quota_number: number | null
  next_due_date: string | null
  days_remaining: number | null
  status: DocStatus
  message: string | null
}

export type VehicleDocuments = {
  soat: LegalDocument
  citv: LegalDocument
  impuesto_vehicular: ImpuestoVehicular
}
