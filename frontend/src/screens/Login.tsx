import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api, ApiError } from '../api/client'
import type { TokenOut } from '../api/types'
import { saveSession } from '../auth'

const inputCls =
  'w-full rounded-xl border border-line bg-surface px-4 py-3 text-sm text-ink placeholder:text-muted focus:border-cyan focus:outline-none'

export default function Login() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')

  const submit = useMutation({
    mutationFn: () =>
      api<TokenOut>(`/api/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify(mode === 'login' ? { email, password } : { email, name, password }),
      }),
    onSuccess: (data) => {
      saveSession(data)
      navigate('/', { replace: true })
    },
  })

  const error = submit.error as ApiError | null

  return (
    <div className="mx-auto flex min-h-svh w-full max-w-sm flex-col justify-center px-6 py-10">
      <h1 className="text-center font-display text-4xl font-extrabold tracking-tight">
        Mi
        <span className="bg-gradient-to-r from-cyan to-indigo bg-clip-text text-transparent">
          Garaje
        </span>
        <span className="text-cyan">.</span>
      </h1>
      <p className="mt-2 text-center text-sm text-muted">La bitácora inteligente de tu auto</p>

      <form
        className="mt-8 flex flex-col gap-3 rounded-2xl border border-line bg-card p-5"
        onSubmit={(e) => {
          e.preventDefault()
          submit.mutate()
        }}
      >
        {mode === 'register' && (
          <input
            className={inputCls}
            placeholder="Tu nombre"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            minLength={2}
          />
        )}
        <input
          className={inputCls}
          type="email"
          placeholder="Correo electrónico"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className={inputCls}
          type="password"
          placeholder={mode === 'register' ? 'Contraseña (mín. 8 caracteres)' : 'Contraseña'}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
        />

        {error && <p className="text-sm font-semibold text-red">{error.message}</p>}

        <button
          type="submit"
          disabled={submit.isPending}
          className="mt-1 rounded-xl bg-gradient-to-r from-cyan to-indigo px-4 py-3 text-sm font-bold text-[#04101F] disabled:opacity-60"
        >
          {submit.isPending ? 'Un momento…' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
        </button>
      </form>

      <button
        type="button"
        className="mt-5 text-sm text-muted underline-offset-4 hover:text-cyan hover:underline"
        onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
      >
        {mode === 'login' ? '¿No tienes cuenta? Regístrate' : '¿Ya tienes cuenta? Inicia sesión'}
      </button>
    </div>
  )
}
