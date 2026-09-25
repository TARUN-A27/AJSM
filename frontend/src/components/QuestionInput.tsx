import { ArrowUp } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { useState } from 'react'
import type { FormEvent } from 'react'

export function QuestionInput({
  onSubmit,
  disabled,
}: {
  onSubmit: (question: string) => void
  disabled: boolean
}) {
  const [value, setValue] = useState('')
  const [focused, setFocused] = useState(false)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-center gap-2.5 rounded-lg border bg-[var(--card-bg)] px-3.5 py-2.5 transition-shadow"
      style={{
        borderColor: focused ? 'var(--border-strong)' : 'var(--border)',
        boxShadow: focused ? 'var(--ring-glow)' : 'none',
      }}
    >
      <span className="font-mono select-none text-sm text-[var(--text-muted)]">&gt;</span>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder="ask about purchases, mrs, stock, suppliers…"
        disabled={disabled}
        className="flex-1 bg-transparent py-0.5 text-sm text-[var(--text-h)] outline-none placeholder:text-[var(--text-muted)]"
      />
      <motion.button
        type="submit"
        disabled={disabled || !value.trim()}
        whileTap={{ scale: 0.92 }}
        aria-label="Ask"
        className="grid h-7 w-7 shrink-0 place-items-center rounded-md border border-[var(--border-strong)]
                   bg-[var(--accent-bg)] text-[var(--text-h)] transition-colors
                   enabled:hover:bg-[var(--accent)] enabled:hover:text-[var(--accent-fg)] disabled:opacity-30"
      >
        <ArrowUp size={14} weight="bold" />
      </motion.button>
    </form>
  )
}
