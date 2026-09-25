import { SmileySad } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis } from 'recharts'
import type { AskResponse } from '../types'

// Grayscale intensity ramp — brightest (most prominent) to dimmest, mapped by rank
// after sorting descending. No hue: category is read from the axis label + the
// direct value label on each bar, not from color (chart-domain guidance: never
// encode category by color alone — doubly true with zero hues available).
const MONO_RAMP = [
  'var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)',
  'var(--chart-4)', 'var(--chart-5)', 'var(--chart-6)',
]

export function ResultView({ response }: { response: AskResponse }) {
  if (response.row_count === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-[var(--border)] px-4 py-8 text-center">
        <SmileySad size={20} weight="light" style={{ color: 'var(--text-muted)' }} />
        <span className="font-mono-label text-[10px] text-[var(--text-muted)]">no rows matched</span>
      </div>
    )
  }

  switch (response.view) {
    case 'summary':
      return <SummaryView response={response} />
    case 'chart':
      return <ChartView response={response} />
    default:
      return <TableView response={response} />
  }
}

function SummaryView({ response }: { response: AskResponse }) {
  const row = response.rows[0]
  return (
    <div className="flex flex-wrap gap-6 rounded-lg border border-[var(--border)] bg-[var(--card-bg)] px-5 py-4">
      {response.columns.map((col, i) => (
        <motion.div
          key={col}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06, duration: 0.3, ease: 'easeOut' }}
        >
          <div className="font-mono-label text-[9.5px] text-[var(--text-muted)]">{col}</div>
          <div className="mt-1 font-mono text-[28px] leading-none font-medium text-[var(--text-h)]">
            {formatCell(row[i])}
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function TableView({ response }: { response: AskResponse }) {
  return (
    <div className="overflow-hidden rounded-lg border border-[var(--border)]">
      <div className="max-h-80 overflow-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-[var(--bg-subtle)]">
            <tr>
              {response.columns.map((col) => (
                <th
                  key={col}
                  className="font-mono-label border-b border-[var(--border)] px-3 py-2 text-[10px] text-[var(--text-muted)] whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {response.rows.map((row, i) => (
              <tr key={i} className="transition-colors hover:bg-[var(--bg-subtle)]">
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className="border-b border-[var(--border)] px-3 py-2 font-mono text-[13px] whitespace-nowrap text-[var(--text)]"
                  >
                    {formatCell(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="font-mono-label border-t border-[var(--border)] bg-[var(--bg-subtle)] px-3 py-1.5 text-[9.5px] text-[var(--text-muted)]">
        {response.row_count} row{response.row_count === 1 ? '' : 's'}
      </div>
    </div>
  )
}

function ChartView({ response }: { response: AskResponse }) {
  const numericIdx = response.columns.findIndex(
    (_, i) => typeof response.rows[0]?.[i] === 'number',
  )
  const labelIdx = numericIdx === 0 ? 1 : 0
  const valueKey = response.columns[numericIdx] ?? response.columns[response.columns.length - 1]
  const labelKey = response.columns[labelIdx] ?? response.columns[0]

  const data = response.rows
    .map((row) => {
      const entry: Record<string, string | number> = {}
      response.columns.forEach((col, i) => {
        entry[col] = row[i] ?? ''
      })
      return entry
    })
    .sort((a, b) => (Number(b[valueKey]) || 0) - (Number(a[valueKey]) || 0))

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--card-bg)] p-4 pt-6">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 20, right: 8, left: 8, bottom: 8 }}>
          <XAxis
            dataKey={labelKey}
            tick={{ fontSize: 10.5, fill: 'var(--text-muted)', fontFamily: 'var(--mono)' }}
            axisLine={{ stroke: 'var(--border)' }}
            tickLine={false}
          />
          <Bar dataKey={valueKey} radius={[3, 3, 0, 0]} maxBarSize={52}>
            {data.map((_, i) => (
              <Cell key={i} fill={MONO_RAMP[i % MONO_RAMP.length]} />
            ))}
            <LabelList
              dataKey={valueKey}
              position="top"
              formatter={(v: unknown) => (typeof v === 'number' ? v.toLocaleString() : String(v ?? ''))}
              style={{ fontFamily: 'var(--mono)', fontSize: 11, fill: 'var(--text-h)' }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function formatCell(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') return value.toLocaleString()
  return String(value)
}
