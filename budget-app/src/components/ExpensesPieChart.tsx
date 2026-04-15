import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Transaction, CATEGORY_COLORS, formatCurrency } from '../types'

interface Props {
  transactions: Transaction[]
}

interface ChartEntry {
  name: string
  value: number
  color: string
}

function buildData(transactions: Transaction[]): ChartEntry[] {
  const map: Record<string, number> = {}
  transactions
    .filter(t => t.type === 'expense')
    .forEach(t => { map[t.category] = (map[t.category] ?? 0) + t.amount })

  return Object.entries(map)
    .map(([name, value]) => ({
      name,
      value,
      color: CATEGORY_COLORS[name as keyof typeof CATEGORY_COLORS] ?? '#6b7280',
    }))
    .sort((a, b) => b.value - a.value)
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: { name: string; value: number }[] }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 shadow-xl">
      <p className="text-white text-sm font-medium">{payload[0].name}</p>
      <p className="text-violet-400 text-base font-bold mt-0.5">{formatCurrency(payload[0].value)}</p>
    </div>
  )
}

const CustomLegend = ({ payload }: { payload?: { value: string; color: string }[] }) => {
  if (!payload?.length) return null
  return (
    <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-2">
      {payload.map(entry => (
        <div key={entry.value} className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: entry.color }} />
          <span className="text-xs text-gray-400">{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

export default function ExpensesPieChart({ transactions }: Props) {
  const data = buildData(transactions)
  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Расходы по категориям</h2>
          <p className="text-sm text-gray-500 mt-0.5">Итого: {formatCurrency(total)}</p>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-600">
          <span className="text-4xl mb-3">📊</span>
          <p className="text-sm">Нет данных о расходах</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="45%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} opacity={0.9} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
          </PieChart>
        </ResponsiveContainer>
      )}

      {/* Category breakdown */}
      {data.length > 0 && (
        <div className="mt-2 space-y-2">
          {data.slice(0, 4).map(item => (
            <div key={item.name} className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
              <span className="text-xs text-gray-400 flex-1 truncate">{item.name}</span>
              <span className="text-xs text-gray-300 font-medium">{formatCurrency(item.value)}</span>
              <div className="w-20 bg-gray-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{ width: `${(item.value / total) * 100}%`, backgroundColor: item.color }}
                />
              </div>
              <span className="text-xs text-gray-600 w-8 text-right">
                {Math.round((item.value / total) * 100)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
