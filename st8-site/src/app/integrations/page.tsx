import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Интеграции",
  description: "Системы, с которыми интегрируется ST8-AI: iiko, R-Keeper, 1С, amoCRM, Telegram.",
};

const integrations = ["iiko", "R-Keeper", "1С", "amoCRM", "Telegram", "Google Sheets"];

export default function IntegrationsPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight">Интеграции</h1>
        <p className="mt-6 text-foreground/70">
          Подключаем AI-автоматизацию к системам, которые уже использует ваш
          бизнес. Страница в разработке — ниже список ключевых интеграций.
        </p>
        <ul className="mt-8 flex flex-wrap gap-3">
          {integrations.map((name) => (
            <li
              key={name}
              className="rounded-full border border-border px-4 py-2 text-sm text-foreground/80"
            >
              {name}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
