import { AnimatePresence, motion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { askQuestion } from './api'
import { EmptyState } from './components/EmptyState'
import { QuestionInput } from './components/QuestionInput'
import { ThemeToggle } from './components/ThemeToggle'
import { TurnCard } from './components/TurnCard'
import type { Turn } from './types'

export default function App() {
  const [turns, setTurns] = useState<Turn[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [turns])

  const isBusy = turns.some((t) => t.status === 'loading')

  async function handleAsk(question: string) {
    const id = crypto.randomUUID()
    setTurns((prev) => [...prev, { id, question, status: 'loading' }])

    try {
      const response = await askQuestion(question)
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, status: 'done', response } : t)))
    } catch (err) {
      setTurns((prev) =>
        prev.map((t) =>
          t.id === id
            ? { ...t, status: 'error', error: err instanceof Error ? err.message : 'Something went wrong.' }
            : t,
        ),
      )
    }
  }

  return (
    <div className="flex h-full flex-col bg-[var(--bg)]">
      <header className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--bg)]/85 px-5 py-3.5 backdrop-blur-md">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-md border border-[var(--border-strong)] text-[var(--text-h)]">
            <span className="font-mono-label text-[10px]">AJ</span>
          </div>
          <span className="font-mono-label flex items-center gap-1.5 text-[13px] text-[var(--text-h)]">
            AJSMGPT
            <motion.span
              className="inline-block h-[13px] w-[7px] bg-[var(--text-h)]"
              animate={{ opacity: [1, 1, 0, 0] }}
              transition={{ duration: 1, repeat: Infinity, times: [0, 0.5, 0.5, 1] }}
            />
          </span>
          <StatusDot />
        </div>
        <ThemeToggle />
      </header>

      <main ref={scrollRef} className="flex flex-1 flex-col overflow-y-auto px-4 py-6">
        <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8">
          {turns.length === 0 ? (
            <EmptyState onPick={handleAsk} />
          ) : (
            <AnimatePresence initial={false}>
              {turns.map((turn) => (
                <TurnCard key={turn.id} turn={turn} />
              ))}
            </AnimatePresence>
          )}
        </div>
      </main>

      <footer className="border-t border-[var(--border)] bg-[var(--bg)]/85 px-4 py-4 backdrop-blur-md">
        <div className="mx-auto w-full max-w-2xl">
          <QuestionInput onSubmit={handleAsk} disabled={isBusy} />
        </div>
      </footer>
    </div>
  )
}

function StatusDot() {
  return (
    <span className="ml-1 flex items-center gap-1.5 text-[var(--text-muted)]">
      <span className="relative flex h-1.5 w-1.5">
        <motion.span
          className="absolute inline-flex h-full w-full rounded-full bg-[var(--text-muted)]"
          animate={{ scale: [1, 2.2], opacity: [0.5, 0] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'easeOut' }}
        />
        <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[var(--text-muted)]" />
      </span>
      <span className="font-mono-label text-[10px]">live</span>
    </span>
  )
}
