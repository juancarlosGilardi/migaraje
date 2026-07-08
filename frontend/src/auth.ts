import type { TokenOut, User } from './api/types'

export function saveSession(data: TokenOut) {
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))
}

export function clearSession() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function hasSession(): boolean {
  return Boolean(localStorage.getItem('token'))
}

export function sessionUser(): User | null {
  const raw = localStorage.getItem('user')
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}
