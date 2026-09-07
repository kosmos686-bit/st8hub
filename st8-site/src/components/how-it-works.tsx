const steps = [
  {
    number: "1",
    title: "Аудит",
    description: "Анализируем процессы, данные и инфраструктуру за 1-2 дня",
  },
  {
    number: "2",
    title: "Настройка",
    description: "Обучаем модели на ваших данных, настраиваем интеграции",
  },
  {
    number: "3",
    title: "Запуск",
    description: "Пилот на 1 точке, тестирование, доработка под реальную нагрузку",
  },
  {
    number: "4",
    title: "Масштабирование",
    description:
      "Распространяем на всю сеть, обучаем команду, передаём документацию",
  },
];

export function HowItWorks() {
  return (
    <div className="mx-auto grid max-w-4xl gap-6 sm:grid-cols-2 md:grid-cols-4">
      {steps.map((step) => (
        <div key={step.number} className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-gold/30 text-lg font-semibold text-gold">
            {step.number}
          </div>
          <h3 className="mb-2 text-sm font-semibold">{step.title}</h3>
          <p className="text-xs leading-relaxed text-foreground/50">
            {step.description}
          </p>
        </div>
      ))}
    </div>
  );
}
