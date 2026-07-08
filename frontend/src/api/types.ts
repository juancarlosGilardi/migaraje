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

export type Vehicle = {
  id: number
  brand: string
  model: string
  year: number
  plate: string
  fuel: string
  first_registration_year: number | null
  current_km: number
}
