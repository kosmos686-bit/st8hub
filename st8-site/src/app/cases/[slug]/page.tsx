import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { cases, getCase } from "@/lib/data/cases";

export function generateStaticParams() {
  return cases.map((c) => ({ slug: c.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const caseStudy = getCase(slug);
  if (!caseStudy) return {};

  return {
    title: `${caseStudy.client} — кейс ST8-AI`,
    description: caseStudy.solution,
  };
}

export default async function CasePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const caseStudy = getCase(slug);
  if (!caseStudy) notFound();

  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-2xl">
        <p className="text-sm font-medium uppercase tracking-[0.2em] text-gold">
          {caseStudy.industry}
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight">
          {caseStudy.client}
        </h1>

        <div className="mt-10">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-foreground/40">
            Задача
          </h2>
          <p className="mt-2 text-foreground/80">{caseStudy.challenge}</p>
        </div>

        <div className="mt-6">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-foreground/40">
            Решение
          </h2>
          <p className="mt-2 text-foreground/80">{caseStudy.solution}</p>
        </div>

        <div className="mt-10 grid grid-cols-3 gap-4 border-t border-border pt-8">
          {caseStudy.results.map((r) => (
            <div key={r.label} className="text-center">
              <div className="text-2xl font-semibold text-gold">{r.value}</div>
              <div className="mt-1 text-xs text-foreground/50">{r.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
