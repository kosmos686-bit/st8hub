import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Transaction, formatCurrency } from '../types'

interface Props {
  transactions: Transaction[]
}

interface MonthData {
  label: string
  income: number
  expense: number
  profit: number
}

function buildMonthlyData(transactions: Transaction[]): MonthData[] {
  const now = new Date()
  const months: { key: string; label: string }[] = []

  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
    const label = d.toLocaleDateString('ru-RU', { month: 'short' })
    months.push({ key, label })
  }

  return months.map(({ key, label }) => {
    const month = transactions.filter(t => t.date.startsWith(key))
    const income = month.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0)
    const expense = month.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0)
    return { label, income, expense, profit: income - expense }
  })
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
}) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-gray-400 text-xs mb-2 font-medium uppercase tracking-wide">{label}</p>
      {payload.map(entry => (
        <div key={entry.name} className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-gray-400 text-xs">{entry.name}:</span>
          <span className="text-white text-xs font-semibold">{formatCurrency(entry.value)}</span>
        </div>
      ))}
    </div>
  )
}

export default function MonthlyLineChart({ transactions }: Props) {
  const data = buildMonthlyData(transactions)
  const hasData = data.some(d => d.income > 0 || d.expense > 0)

  const maxVal = Math.max(...data.map(d => Math.max(d.income, d.expense)))

  const formatYAxis = (value: number) => {
    if (value >= 1000) return `${(value / 1000).toFixed(0)}k`
    return String(value)
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Динамика по месяцам</h2>
          <p className="text-sm text-gray-500 mt-0.5">Последние 6 месяцев</p>
        </div>
        {hasData && (
          <div className="flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-emerald-500 rounded" />
              Доходы
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 bg-rose-500 rounded" />
              Расходы
            </div>
          </div>
        )}
      </div>

      {!hasData ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-600">
          <span className="text-4xl mb-3">📈</span>
          <p className="text-sm">Нет данных за последние 6 месяцев</p>
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: '#6b7280', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tickFormatter={formatYAxis}
                tick={{ fill: '#6b7280', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                domain={[0, maxVal * 1.1]}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#374151', strokeWidth: 1 }} />
              <Line
                type="monotone"
                dataKey="income"
                name="Доходы"
                stroke="#10b981"
                strokeWidth={2.5}
                dot={{ fill: '#10b981', r: 4, strokeWidth: 0 }}
                activeDot={{ r: 6, strokeWidth: 0 }}
              />
              <Line
                type="monotone"
                dataKey="expense"
                name="Расходы"
                stroke="#ef4444"
                strokeWidth={2.5}
                dot={{ fill: '#ef4444', r: 4, strokeWidth: 0 }}
                activeDot={{ r: 6, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>

          {/* Monthly profit row */}
          <div className="grid grid-cols-6 gap-1 mt-2">
            {data.map(m => (
              <div key={m.label} className="text-center">
                <p className="text-xs text-gray-600 mb-0.5">{m.label}</p>
                <p
                  className={`text-xs font-semibold ${
                    m.profit > 0 ? 'text-emerald-500' : m.profit < 0 ? 'text-rose-500' : 'text-gray-600'
                  }`}
                >
                  {m.profit > 0 ? '+' : ''}{m.profit === 0 ? '—' : `${Math.round(m.profit / 1000)}k`}
                </p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
