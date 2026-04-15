import { useState } from 'react'
import { Transaction, TransactionType, CATEGORY_COLORS, CATEGORY_ICONS, formatCurrency, formatDate } from '../types'

interface Props {
  transactions: Transaction[]
  onDelete: (id: string) => void
}

type Filter = 'all' | TransactionType

export default function TransactionList({ transactions, onDelete }: Props) {
  const [filter, setFilter] = useState<Filter>('all')
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const filtered = transactions
    .filter(t => filter === 'all' || t.type === filter)
    .sort((a, b) => b.date.localeCompare(a.date))

  const handleDelete = (id: string) => {
    if (confirmDelete === id) {
      onDelete(id)
      setConfirmDelete(null)
    } else {
      setConfirmDelete(id)
      setTimeout(() => setConfirmDelete(null), 3000)
    }
  }

  const filterBtns: { key: Filter; label: string; count: number }[] = [
    { key: 'all',     label: 'Все',     count: transactions.length },
    { key: 'income',  label: 'Доходы',  count: transactions.filter(t => t.type === 'income').length },
    { key: 'expense', label: 'Расходы', count: transactions.filter(t => t.type === 'expense').length },
  ]

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col h-full">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold text-white">История операций</h2>
        <span className="text-xs text-gray-600">{filtered.length} записей</span>
      </div>

      {/* Filter tabs */}
      <div className="flex bg-gray-800 rounded-xl p-1 mb-5 gap-1">
        {filterBtns.map(({ key, label, count }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`flex-1 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
              filter === key
                ? 'bg-gray-700 text-white'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            {label}
            <span
              className={`text-xs px-1.5 py-0.5 rounded-full ${
                filter === key ? 'bg-gray-600 text-gray-300' : 'bg-gray-700/50 text-gray-600'
              }`}
            >
              {count}
            </span>
          </button>
        ))}
      </div>

      {/* Transaction list */}
      <div className="flex-1 overflow-y-auto space-y-2 max-h-96 pr-1">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-600">
            <span className="text-4xl mb-3">📭</span>
            <p className="text-sm">Операций нет</p>
          </div>
        ) : (
          filtered.map(t => (
            <div
              key={t.id}
              className="group flex items-center gap-3 p-3 rounded-xl bg-gray-800/40 hover:bg-gray-800/70 border border-transparent hover:border-gray-700/50 transition-all"
            >
              {/* Category icon */}
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center text-lg flex-shrink-0"
                style={{ backgroundColor: CATEGORY_COLORS[t.category] + '22' }}
              >
                {CATEGORY_ICONS[t.category]}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white truncate">
                    {t.description || t.category}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span
                    className="text-xs px-1.5 py-0.5 rounded-md font-medium"
                    style={{
                      backgroundColor: CATEGORY_COLORS[t.category] + '22',
                      color: CATEGORY_COLORS[t.category],
                    }}
                  >
                    {t.category}
                  </span>
                  <span className="text-xs text-gray-600">{formatDate(t.date)}</span>
                </div>
              </div>

              {/* Amount */}
              <div className="text-right flex-shrink-0">
                <p
                  className={`text-sm font-semibold ${
                    t.type === 'income' ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {t.type === 'income' ? '+' : '−'}
                  {formatCurrency(t.amount)}
                </p>
              </div>

              {/* Delete */}
              <button
                onClick={() => handleDelete(t.id)}
                title={confirmDelete === t.id ? 'Нажмите ещё раз для удаления' : 'Удалить'}
                className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs transition-all opacity-0 group-hover:opacity-100 ${
                  confirmDelete === t.id
                    ? 'bg-rose-500/30 text-rose-400 opacity-100'
                    : 'hover:bg-gray-700 text-gray-600 hover:text-gray-400'
                }`}
              >
                {confirmDelete === t.id ? '✓' : '×'}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
