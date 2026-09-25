export type ResultView = 'table' | 'chart' | 'summary'

export interface AskResponse {
  question: string
  sql: string
  view: ResultView
  columns: string[]
  rows: (string | number | null)[][]
  row_count: number
  summary: string
}

export interface Turn {
  id: string
  question: string
  status: 'loading' | 'done' | 'error'
  response?: AskResponse
  error?: string
}
