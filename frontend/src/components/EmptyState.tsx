import { ArrowUpRight } from '@phosphor-icons/react'
import { motion } from 'motion/react'

const EXAMPLES = [
  { tag: 'CONSUMPTION', text: 'How much cost was consumed last month?' },
  { tag: 'ISSUE', text: 'Latest issue for yarn in 2024' },
  { tag: 'PURCHASE', text: 'Which purchase orders are pending at JMD?' },
  { tag: 'STOCK', text: 'Total stock of item A12001392' },
]

export function EmptyState({ onPick }: { onPick: (question: string) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="flex flex-1 flex-col items-center justify-center gap-8 text-center"
    >
      <ScanTarget />

      <div>
        <h1 className="text-2xl font-semibold text-[var(--text-h)]">Ask AJSMGPT anything</h1>
        <p className="font-mono-label mt-2 text-[11px] text-[var(--text-muted)]">
          natural language &middot; oracle erp &middot; read-only
        </p>
      </div>

      <div className="grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {EXAMPLES.map(({ tag, text }, i) => (
          <motion.button
            key={text}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + i * 0.06, duration: 0.35, ease: 'easeOut' }}
            whileHover={{ borderColor: 'var(--border-strong)' }}
            onClick={() => onPick(text)}
            className="group flex items-center justify-between gap-3 rounded-lg border border-[var(--border)]
                       bg-[var(--card-bg)] px-3.5 py-3 text-left transition-colors"
          >
            <span className="flex flex-col gap-1">
              <span className="font-mono-label text-[9.5px] text-[var(--text-muted)]">{tag}</span>
              <span className="text-xs text-[var(--text)] group-hover:text-[var(--text-h)]">{text}</span>
            </span>
            <ArrowUpRight
              size={14}
              className="shrink-0 text-[var(--text-muted)] opacity-0 transition-opacity group-hover:opacity-100"
            />
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}

function ScanTarget() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="relative grid h-16 w-16 place-items-center"
    >
      {(['top-0 left-0 border-t border-l', 'top-0 right-0 border-t border-r',
         'bottom-0 left-0 border-b border-l', 'bottom-0 right-0 border-b border-r'] as const
      ).map((pos) => (
        <span
          key={pos}
          className={`absolute h-4 w-4 border-[var(--border-strong)] ${pos}`}
        />
      ))}
      <motion.span
        className="h-1.5 w-1.5 rounded-full bg-[var(--text-h)]"
        animate={{ opacity: [1, 0.3, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      />
    </motion.div>
  )
}
