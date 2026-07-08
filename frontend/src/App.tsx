import { useQuery } from '@tanstack/react-query'
import { api } from './api/client'

type Health = { status: string; app: string; version: string }

function App() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: () => api<Health>('/api/health'),
    retry: 1,
  })

  return (
    <div className="mx-auto flex min-h-svh max-w-md flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="font-display text-4xl font-extrabold tracking-tight">
        Mi<span className="bg-gradient-to-r from-cyan to-indigo bg-clip-text text-transparent">Garaje</span>
        <span className="text-cyan">.</span>
      </h1>
      <p className="text-muted">La bitácora inteligente de tu auto</p>

      <div className="w-full rounded-2xl border border-line bg-card p-5 text-sm">
        {health.isPending && <span className="text-muted">Conectando con la API…</span>}
        {health.isError && (
          <span className="font-semibold text-red">
            ✗ API sin conexión — ¿está corriendo uvicorn en el puerto 8000?
          </span>
        )}
        {health.isSuccess && (
          <span className="font-semibold text-green">
            ✓ Conectado a {health.data.app} v{health.data.version}
          </span>
        )}
      </div>

      <p className="text-xs text-muted">Fase 0 · fundaciones — las pantallas llegan en la Fase 1</p>
    </div>
  )
}

export default App
