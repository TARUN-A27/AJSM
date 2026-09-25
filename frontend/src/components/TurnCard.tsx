import { CaretDown, WarningCircle } from '@phosphor-icons/react'
import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'
import type { Turn } from '../types'
import { ResultView } from './ResultView'

export function TurnCard({ turn }: { turn: Turn }) {
  const [showSql, setShowSql] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="flex flex-col gap-2.5"
    >
      <div className="flex flex-col items-end gap-1">
        <span className="font-mono-label text-[9.5px] text-[var(--text-muted)]">query</span>
        <div className="max-w-[85%] rounded-lg border border-[var(--border)] bg-[var(--card-bg)] px-3.5 py-2 text-sm text-[var(--text-h)]">
          {turn.question}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {turn.status === 'loading' && <ScannerBar />}

        {turn.status === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-2 rounded-lg border px-3.5 py-2.5 text-sm"
            style={{
              borderColor: 'var(--danger-border)',
              background: 'var(--danger-bg)',
              color: 'var(--danger)',
            }}
          >
            <WarningCircle size={15} weight="fill" className="mt-0.5 shrink-0" />
            {turn.error}
          </motion.div>
        )}

        {turn.status === 'done' && turn.response && (
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-between px-0.5">
              <span className="font-mono-label text-[9.5px] text-[var(--text-muted)]">result</span>
              <button
                onClick={() => setShowSql((v) => !v)}
                className="flex items-center gap-1 text-[10px] text-[var(--text-muted)] transition-colors hover:text-[var(--text-h)]"
              >
                <span className="font-mono-label">sql</span>
                <motion.span animate={{ rotate: showSql ? 180 : 0 }} transition={{ duration: 0.2 }}>
                  <CaretDown size={10} weight="bold" />
                </motion.span>
              </button>
            </div>

            <motion.p
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              className="px-0.5 text-sm text-[var(--text-h)]"
            >
              {turn.response.summary}
            </motion.p>

            {turn.response.row_count > 0 && <ResultView response={turn.response} />}

            <AnimatePresence>
              {showSql && (
                <motion.pre
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--bg-subtle)]
                             p-3 text-xs whitespace-pre-wrap text-[var(--text)]"
                >
                  {turn.response.sql}
                </motion.pre>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </motion.div>
  )
}

function ScannerBar() {
  return (
    <div className="flex flex-col gap-2 rounded-lg border border-[var(--border)] bg-[var(--card-bg)] px-3.5 py-3">
      <span className="font-mono-label text-[10px] text-[var(--text-muted)]">querying database…</span>
      <div className="relative h-px w-full overflow-hidden bg-[var(--border)]">
        <motion.div
          className="absolute inset-y-0 w-1/3 bg-[var(--text-h)]"
          animate={{ left: ['-33%', '100%'] }}
          transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
    </div>
  )
}
