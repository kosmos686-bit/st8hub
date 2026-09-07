import type { Metadata } from "next";
import { CaseCard } from "@/components/case-card";
import { cases } from "@/lib/data/cases";

export const metadata: Metadata = {
  title: "Кейсы",
  description: "Реализованные проекты AI-автоматизации ST8-AI.",
};

export default function CasesPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <h1 className="text-3xl font-semibold tracking-tight">Кейсы</h1>
        <p className="mt-3 max-w-2xl text-foreground/70">
          Несколько проектов, где ST8-AI внедрял AI-автоматизацию под конкретную
          задачу бизнеса.
        </p>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {cases.map((c) => (
            <CaseCard key={c.slug} caseStudy={c} />
          ))}
        </div>
      </div>
    </section>
  );
}
