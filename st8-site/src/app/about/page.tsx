import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "О нас",
  description: "ST8-AI — команда, внедряющая AI-автоматизацию для бизнеса.",
};

export default function AboutPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight">О нас</h1>
        <p className="mt-6 text-foreground/70">
          ST8-AI — команда, которая внедряет AI-автоматизацию для бизнеса: от
          чат-ботов и учёта до глубокой интеграции с внутренними системами.
          Страница в разработке.
        </p>
      </div>
    </section>
  );
}
