import { formatCurrency } from '../types'

interface Props {
  balance: number
  income: number
  expense: number
}

export default function Balance({ balance, income, expense }: Props) {
  const isPositive = balance >= 0
  const isZero = balance === 0

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {/* Main balance card */}
      <div
        className={`sm:col-span-1 relative overflow-hidden rounded-2xl p-6 border ${
          isZero
            ? 'bg-gray-900 border-gray-800'
            : isPositive
            ? 'bg-gradient-to-br from-emerald-950 to-gray-900 border-emerald-900/50'
            : 'bg-gradient-to-br from-rose-950 to-gray-900 border-rose-900/50'
        }`}
      >
        <div className="relative z-10">
          <p className="text-sm font-medium text-gray-400 mb-1">Текущий баланс</p>
          <p
            className={`text-3xl font-bold tracking-tight ${
              isZero ? 'text-gray-300' : isPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isPositive && !isZero ? '+' : ''}
            {formatCurrency(balance)}
          </p>
          <div className="mt-3 flex items-center gap-1.5">
            <div
              className={`w-2 h-2 rounded-full ${
                isZero ? 'bg-gray-500' : isPositive ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
            <span className="text-xs text-gray-500">
              {isZero ? 'Нулевой баланс' : isPositive ? 'Положительный' : 'Отрицательный'}
            </span>
          </div>
        </div>
        {/* Glow */}
        <div
          className={`absolute -top-8 -right-8 w-32 h-32 rounded-full blur-3xl opacity-20 ${
            isPositive && !isZero ? 'bg-emerald-500' : isZero ? 'bg-gray-600' : 'bg-rose-500'
          }`}
        />
      </div>

      {/* Income card */}
      <div className="rounded-2xl p-6 bg-gray-900 border border-gray-800 relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <p className="text-sm font-medium text-gray-400">Доходы</p>
          </div>
          <p className="text-2xl font-bold text-emerald-400">{formatCurrency(income)}</p>
          <p className="text-xs text-gray-600 mt-2">Всё время</p>
        </div>
        <div className="absolute -bottom-6 -right-6 w-24 h-24 rounded-full blur-2xl opacity-10 bg-emerald-500" />
      </div>

      {/* Expense card */}
      <div className="rounded-2xl p-6 bg-gray-900 border border-gray-800 relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-rose-500" />
            <p className="text-sm font-medium text-gray-400">Расходы</p>
          </div>
          <p className="text-2xl font-bold text-rose-400">{formatCurrency(expense)}</p>
          <p className="text-xs text-gray-600 mt-2">Всё время</p>
        </div>
        <div className="absolute -bottom-6 -right-6 w-24 h-24 rounded-full blur-2xl opacity-10 bg-rose-500" />
      </div>
    </div>
  )
}
