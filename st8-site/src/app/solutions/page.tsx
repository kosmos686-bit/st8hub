import type { Metadata } from "next";
import { SolutionCard } from "@/components/solution-card";
import { solutions } from "@/lib/data/solutions";

export const metadata: Metadata = {
  title: "Решения",
  description: "AI-автоматизация ST8-AI по отраслям: HoReCa, производство, ритейл, логистика, офис.",
};

export default function SolutionsPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <h1 className="text-3xl font-semibold tracking-tight">Решения по отраслям</h1>
        <p className="mt-3 max-w-2xl text-foreground/70">
          Выберите отрасль — покажем, какие процессы автоматизируем и что это даёт
          в цифрах.
        </p>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {solutions.map((s) => (
            <SolutionCard key={s.slug} solution={s} />
          ))}
        </div>
      </div>
    </section>
  );
}
