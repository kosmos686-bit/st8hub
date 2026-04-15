import { useState, FormEvent } from 'react'
import {
  Transaction,
  TransactionType,
  Category,
  IncomeCategory,
  ExpenseCategory,
  INCOME_CATEGORIES,
  EXPENSE_CATEGORIES,
  CATEGORY_ICONS,
} from '../types'

interface Props {
  onAdd: (t: Omit<Transaction, 'id'>) => void
}

export default function TransactionForm({ onAdd }: Props) {
  const [type, setType] = useState<TransactionType>('expense')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState<Category>('Еда')
  const [description, setDescription] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [error, setError] = useState('')

  const handleTypeChange = (newType: TransactionType) => {
    setType(newType)
    setCategory(newType === 'income' ? 'Зарплата' : 'Еда')
    setError('')
  }

  const categories: Category[] =
    type === 'income'
      ? (INCOME_CATEGORIES as Category[])
      : (EXPENSE_CATEGORIES as Category[])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const amountNum = parseFloat(amount.replace(',', '.'))
    if (!amountNum || amountNum <= 0) {
      setError('Введите корректную сумму')
      return
    }
    onAdd({ type, amount: amountNum, category, description: description.trim(), date })
    setAmount('')
    setDescription('')
    setDate(new Date().toISOString().split('T')[0])
    setError('')
  }

  const inputClass =
    'w-full bg-gray-800/60 border border-gray-700 rounded-xl px-4 py-2.5 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors'

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 h-full">
      <h2 className="text-lg font-semibold text-white mb-5">Добавить операцию</h2>

      {/* Type toggle */}
      <div className="flex bg-gray-800 rounded-xl p-1 mb-5">
        <button
          type="button"
          onClick={() => handleTypeChange('expense')}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
            type === 'expense'
              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
              : 'text-gray-500 hover:text-gray-300'
          }`}
        >
          Расход
        </button>
        <button
          type="button"
          onClick={() => handleTypeChange('income')}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
            type === 'income'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'text-gray-500 hover:text-gray-300'
          }`}
        >
          Доход
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Amount */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Сумма, ₽
          </label>
          <input
            type="number"
            min="1"
            step="1"
            placeholder="0"
            value={amount}
            onChange={e => { setAmount(e.target.value); setError('') }}
            className={`${inputClass} text-lg font-semibold`}
            required
          />
          {error && <p className="text-rose-400 text-xs mt-1">{error}</p>}
        </div>

        {/* Category */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Категория
          </label>
          <select
            value={category}
            onChange={e => setCategory(e.target.value as Category)}
            className={`${inputClass} cursor-pointer`}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {CATEGORY_ICONS[cat]} {cat}
              </option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Описание <span className="text-gray-600">(необязательно)</span>
          </label>
          <input
            type="text"
            placeholder="Например: продукты в Перекрёстке"
            value={description}
            onChange={e => setDescription(e.target.value)}
            maxLength={80}
            className={inputClass}
          />
        </div>

        {/* Date */}
        <div>
          <label className="block text-xs font-medium text-gray-400 mb-1.5">
            Дата
          </label>
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            className={`${inputClass} [color-scheme:dark]`}
            required
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          className={`w-full py-3 rounded-xl font-semibold text-sm transition-all mt-2 ${
            type === 'expense'
              ? 'bg-rose-500 hover:bg-rose-400 text-white'
              : 'bg-emerald-500 hover:bg-emerald-400 text-white'
          }`}
        >
          {type === 'expense' ? '− Добавить расход' : '+ Добавить доход'}
        </button>
      </form>
    </div>
  )
}
