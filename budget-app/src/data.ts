import { Transaction } from './types'

export const SAMPLE_TRANSACTIONS: Transaction[] = [
  // Апрель 2026
  { id: 'tx-001', type: 'income',  amount: 120000, category: 'Зарплата',      description: 'Оклад апрель',         date: '2026-04-05' },
  { id: 'tx-002', type: 'income',  amount: 45000,  category: 'Фриланс',       description: 'Проект маркетплейс',   date: '2026-04-08' },
  { id: 'tx-003', type: 'expense', amount: 35000,  category: 'Жилье',         description: 'Аренда квартиры',      date: '2026-04-01' },
  { id: 'tx-004', type: 'expense', amount: 12400,  category: 'Еда',           description: 'Продукты и доставка',  date: '2026-04-10' },
  { id: 'tx-005', type: 'expense', amount: 4200,   category: 'Транспорт',     description: 'Метро и каршеринг',    date: '2026-04-09' },
  { id: 'tx-006', type: 'expense', amount: 8900,   category: 'Развлечения',   description: 'Кино, кафе, стриминг', date: '2026-04-11' },

  // Март 2026
  { id: 'tx-007', type: 'income',  amount: 120000, category: 'Зарплата',      description: 'Оклад март',           date: '2026-03-05' },
  { id: 'tx-008', type: 'income',  amount: 12000,  category: 'Инвестиции',    description: 'Дивиденды',            date: '2026-03-15' },
  { id: 'tx-009', type: 'expense', amount: 35000,  category: 'Жилье',         description: 'Аренда квартиры',      date: '2026-03-01' },
  { id: 'tx-010', type: 'expense', amount: 28500,  category: 'Еда',           description: 'Супермаркеты',         date: '2026-03-20' },
  { id: 'tx-011', type: 'expense', amount: 15000,  category: 'Шоппинг',       description: 'Весенний гардероб',    date: '2026-03-12' },
  { id: 'tx-012', type: 'expense', amount: 6800,   category: 'Здоровье',      description: 'Врач и анализы',       date: '2026-03-18' },
  { id: 'tx-013', type: 'expense', amount: 4500,   category: 'Транспорт',     description: 'Такси',                date: '2026-03-22' },

  // Февраль 2026
  { id: 'tx-014', type: 'income',  amount: 120000, category: 'Зарплата',      description: 'Оклад февраль',        date: '2026-02-05' },
  { id: 'tx-015', type: 'income',  amount: 60000,  category: 'Фриланс',       description: 'Редизайн сайта',       date: '2026-02-20' },
  { id: 'tx-016', type: 'expense', amount: 35000,  category: 'Жилье',         description: 'Аренда квартиры',      date: '2026-02-01' },
  { id: 'tx-017', type: 'expense', amount: 95000,  category: 'Путешествия',   description: 'Поездка в Дубай',      date: '2026-02-14' },
  { id: 'tx-018', type: 'expense', amount: 18000,  category: 'Еда',           description: 'Продукты февраль',     date: '2026-02-15' },
  { id: 'tx-019', type: 'expense', amount: 3200,   category: 'Транспорт',     description: 'Транспорт',            date: '2026-02-18' },

  // Январь 2026
  { id: 'tx-020', type: 'income',  amount: 120000, category: 'Зарплата',      description: 'Оклад январь',         date: '2026-01-10' },
  { id: 'tx-021', type: 'income',  amount: 8500,   category: 'Инвестиции',    description: 'Дивиденды',            date: '2026-01-20' },
  { id: 'tx-022', type: 'expense', amount: 35000,  category: 'Жилье',         description: 'Аренда квартиры',      date: '2026-01-01' },
  { id: 'tx-023', type: 'expense', amount: 22000,  category: 'Еда',           description: 'Продукты и рестораны', date: '2026-01-15' },
  { id: 'tx-024', type: 'expense', amount: 31000,  category: 'Шоппинг',       description: 'Техника и одежда',     date: '2026-01-08' },
  { id: 'tx-025', type: 'expense', amount: 12000,  category: 'Развлечения',   description: 'Новогодние праздники', date: '2026-01-05' },
  { id: 'tx-026', type: 'expense', amount: 5500,   category: 'Транспорт',     description: 'Такси и метро',        date: '2026-01-22' },

  // Декабрь 2025
  { id: 'tx-027', type: 'income',  amount: 150000, category: 'Зарплата',      description: 'Оклад + премия',       date: '2025-12-05' },
  { id: 'tx-028', type: 'income',  amount: 35000,  category: 'Фриланс',       description: 'Рекламная кампания',   date: '2025-12-18' },
  { id: 'tx-029', type: 'expense', amount: 35000,  category: 'Жилье',         description: 'Аренда квартиры',      date: '2025-12-01' },
  { id: 'tx-030', type: 'expense', amount: 45000,  category: 'Шоппинг',       description: 'Подарки на НГ',        date: '2025-12-20' },
  { id: 'tx-031', type: 'expense', amount: 26000,  category: 'Еда',           description: 'Продукты декабрь',     date: '2025-12-15' },
  { id: 'tx-032', type: 'expense', amount: 18000,  category: 'Развлечения',   description: 'Корпоратив и встречи', date: '2025-12-25' },
  { id: 'tx-033', type: 'expense', amount: 6000,   category: 'Транспорт',     description: 'Транспорт',            date: '2025-12-10' },

  // Ноябрь 2025
  { id: 'tx-034', type: 'income',  amount: 120000, category: 'Зарплата',      description: 'Оклад ноябрь',         date: '2025-11-05' },
  { id: 'tx-035', type: 'income',  amount: 15000,  category: 'Инвестиции',    description: 'Прибыль с акций',      date: '2025-11-28' },
  { id: 'tx-036', type: 'expense', amount: 35000,  category: 'Жилье',         description: 'Аренда квартиры',      date: '2025-11-01' },
  { id: 'tx-037', type: 'expense', amount: 24000,  category: 'Еда',           description: 'Продукты ноябрь',      date: '2025-11-15' },
  { id: 'tx-038', type: 'expense', amount: 9500,   category: 'Здоровье',      description: 'Стоматолог',           date: '2025-11-10' },
  { id: 'tx-039', type: 'expense', amount: 4800,   category: 'Транспорт',     description: 'Транспорт',            date: '2025-11-20' },
  { id: 'tx-040', type: 'expense', amount: 7200,   category: 'Развлечения',   description: 'Концерт и кино',       date: '2025-11-22' },
]
