import { useEffect, useRef, useState } from 'react'

type ComboboxProps = {
  value: string
  onChange: (value: string) => void
  options: string[]
  placeholder: string
  disabled?: boolean
  loading?: boolean
  emptyHint?: string
  required?: boolean
}

const inputCls =
  'w-full rounded-xl border border-line bg-surface px-3 py-2.5 text-sm text-ink placeholder:text-muted focus:border-cyan focus:outline-none disabled:opacity-50'

/** Selector con búsqueda: filtra las opciones al escribir, pero también acepta texto libre
 *  (por si la marca/modelo no está en el catálogo). */
export default function Combobox({
  value,
  onChange,
  options,
  placeholder,
  disabled,
  loading,
  emptyHint,
  required,
}: ComboboxProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState(value)
  const boxRef = useRef<HTMLDivElement>(null)

  useEffect(() => setQuery(value), [value])

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  const filtered =
    query.trim() === ''
      ? options
      : options.filter((o) => o.toLowerCase().includes(query.trim().toLowerCase()))

  function select(option: string) {
    onChange(option)
    setQuery(option)
    setOpen(false)
  }

  return (
    <div className="relative" ref={boxRef}>
      <input
        className={inputCls}
        placeholder={loading ? 'Cargando…' : placeholder}
        value={query}
        required={required}
        disabled={disabled || loading}
        onChange={(e) => {
          setQuery(e.target.value)
          onChange(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
      />
      {open && !loading && (
        <div className="absolute z-30 mt-1 max-h-48 w-full overflow-y-auto rounded-xl border border-line bg-surface shadow-xl">
          {filtered.length === 0 ? (
            <p className="px-3 py-2.5 text-xs text-muted">
              {emptyHint ?? 'Sin coincidencias · se usará el texto escrito'}
            </p>
          ) : (
            filtered.slice(0, 60).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => select(option)}
                className="block w-full truncate px-3 py-2 text-left text-sm hover:bg-cyan/10 hover:text-cyan"
              >
                {option}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
