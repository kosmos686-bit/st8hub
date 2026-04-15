import { useState, useEffect } from 'react'
import { Transaction } from './types'
import { SAMPLE_TRANSACTIONS } from './data'
import Balance from './components/Balance'
import TransactionForm from './components/TransactionForm'
import TransactionList from './components/TransactionList'
import ExpensesPieChart from './components/ExpensesPieChart'
import MonthlyLineChart from './components/MonthlyLineChart'

export default function App() {
  const [transactions, setTransactions] = useState<Transaction[]>(() => {
    try {
      const saved = localStorage.getItem('budget-transactions')
      return saved ? (JSON.parse(saved) as Transaction[]) : SAMPLE_TRANSACTIONS
    } catch {
      return SAMPLE_TRANSACTIONS
    }
  })

  useEffect(() => {
    localStorage.setItem('budget-transactions', JSON.stringify(transactions))
  }, [transactions])

  const addTransaction = (t: Omit<Transaction, 'id'>) => {
    setTransactions(prev => [{ ...t, id: crypto.randomUUID() }, ...prev])
  }

  const deleteTransaction = (id: string) => {
    setTransactions(prev => prev.filter(t => t.id !== id))
  }

  const totalIncome = transactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0)

  const totalExpense = transactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0)

  const balance = totalIncome - totalExpense

  const today = new Date().toLocaleDateString('ru-RU', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {/* Header */}
        <div className="mb-8 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Домашний бюджет
            </h1>
            <p className="text-gray-500 mt-1 capitalize">{today}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 bg-gray-900 border border-gray-800 rounded-xl px-4 py-2">
              <span className="text-gray-400 text-sm">Операций</span>
              <span className="text-white font-semibold">{transactions.length}</span>
            </div>
            {transactions.length > 0 && (
              <button
                onClick={() => {
                  if (window.confirm('Удалить все транзакции и начать с нуля?')) {
                    setTransactions([])
                  }
                }}
                className="text-xs text-gray-600 hover:text-rose-400 border border-gray-800 hover:border-rose-900 rounded-xl px-3 py-2 transition-colors"
              >
                Очистить всё
              </button>
            )}
          </div>
        </div>

        {/* Balance row */}
        <Balance balance={balance} income={totalIncome} expense={totalExpense} />

        {/* Form + List */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-2">
            <TransactionForm onAdd={addTransaction} />
          </div>
          <div className="lg:col-span-3">
            <TransactionList
              transactions={transactions}
              onDelete={deleteTransaction}
            />
          </div>
        </div>

        {/* Charts */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ExpensesPieChart transactions={transactions} />
          <MonthlyLineChart transactions={transactions} />
        </div>

        <p className="text-center text-gray-700 text-xs mt-8 pb-4">
          Данные хранятся в браузере · ST8-AI Budget Tracker
        </p>
      </div>
    </div>
  )
}
