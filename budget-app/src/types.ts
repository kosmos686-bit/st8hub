export type TransactionType = 'income' | 'expense'

export type IncomeCategory = 'Зарплата' | 'Фриланс' | 'Инвестиции'
export type ExpenseCategory =
  | 'Еда'
  | 'Транспорт'
  | 'Жилье'
  | 'Развлечения'
  | 'Шоппинг'
  | 'Здоровье'
  | 'Путешествия'

export type Category = IncomeCategory | ExpenseCategory

export interface Transaction {
  id: string
  type: TransactionType
  amount: number
  category: Category
  description: string
  date: string // YYYY-MM-DD
}

export const INCOME_CATEGORIES: IncomeCategory[] = ['Зарплата', 'Фриланс', 'Инвестиции']

export const EXPENSE_CATEGORIES: ExpenseCategory[] = [
  'Еда',
  'Транспорт',
  'Жилье',
  'Развлечения',
  'Шоппинг',
  'Здоровье',
  'Путешествия',
]

export const CATEGORY_COLORS: Record<Category, string> = {
  Зарплата: '#10b981',
  Фриланс: '#06b6d4',
  Инвестиции: '#8b5cf6',
  Еда: '#f59e0b',
  Транспорт: '#3b82f6',
  Жилье: '#ef4444',
  Развлечения: '#ec4899',
  Шоппинг: '#f97316',
  Здоровье: '#14b8a6',
  Путешествия: '#a78bfa',
}

export const CATEGORY_ICONS: Record<Category, string> = {
  Зарплата: '💰',
  Фриланс: '💻',
  Инвестиции: '📈',
  Еда: '🍽️',
  Транспорт: '🚗',
  Жилье: '🏠',
  Развлечения: '🎮',
  Шоппинг: '🛍️',
  Здоровье: '🏥',
  Путешествия: '✈️',
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}
