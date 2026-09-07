import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Check, Send } from "lucide-react";
import Link from "next/link";
import { Hero } from "@/components/hero";
import { getSolution, solutions } from "@/lib/data/solutions";
import { TELEGRAM_URL } from "@/lib/constants";

export function generateStaticParams() {
  return solutions.map((s) => ({ slug: s.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const solution = getSolution(slug);
  if (!solution) return {};

  return {
    title: `${solution.name} — AI-автоматизация`,
    description: solution.description,
    openGraph: {
      title: `${solution.name} — AI-автоматизация | ST8-AI`,
      description: solution.description,
    },
  };
}

export default async function SolutionPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const solution = getSolution(slug);
  if (!solution) notFound();

  return (
    <>
      <Hero
        eyebrow={solution.name}
        title={solution.tagline}
        description={solution.description}
      />

      <section className="px-6 py-16">
        <div className="mx-auto max-w-3xl">
          <h2 className="text-xl font-semibold">Что входит в решение</h2>
          <ul className="mt-6 space-y-4">
            {solution.features.map((f) => (
              <li key={f.title} className="flex items-start gap-3">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-gold" />
                <div>
                  <span className="font-medium text-foreground">{f.title}</span>
                  <span className="text-foreground/60"> — {f.description}</span>
                </div>
              </li>
            ))}
          </ul>

          <h2 className="mt-12 text-xl font-semibold">Как это работает</h2>
          <p className="mt-4 text-foreground/70">{solution.howItWorks}</p>
        </div>
      </section>

      <section className="px-6 py-16">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-6 text-center text-xl font-semibold">
            Результаты клиентов
          </h2>
          <div className="grid grid-cols-3 gap-6">
            {solution.stats.map((s) => (
              <div
                key={s.label}
                className="rounded-2xl border border-border bg-card p-6 text-center"
              >
                <div className="text-3xl font-semibold text-gold">{s.value}</div>
                <div className="mt-2 text-sm text-foreground/60">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 pb-24">
        <div className="mx-auto flex max-w-3xl justify-center">
          <Link
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener"
            className="inline-flex items-center gap-2 rounded-full bg-gold px-6 py-3 text-sm font-semibold text-[#0a0a0a] transition-colors hover:bg-gold/90"
          >
            <Send className="h-4 w-4" />
            Написать в Telegram
          </Link>
        </div>
      </section>
    </>
  );
}
