import Link from "next/link";
import type { CaseStudy } from "@/lib/data/cases";

export function CaseCard({ caseStudy }: { caseStudy: CaseStudy }) {
  return (
    <Link
      href={`/cases/${caseStudy.slug}`}
      className="group flex flex-col gap-6 rounded-2xl border border-border bg-card p-7 transition-colors hover:border-gold/30"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-wider text-gold/70">
            {caseStudy.industry}
          </span>
          <h3 className="text-xl font-semibold group-hover:text-gold transition-colors">
            {caseStudy.client}
          </h3>
        </div>
        <span className="whitespace-nowrap rounded-full bg-gold/10 px-3 py-1 text-[10px] font-semibold text-gold">
          {caseStudy.tag}
        </span>
      </div>

      <div>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-foreground/35">
          Задача
        </p>
        <p className="text-sm text-foreground/65">{caseStudy.challenge}</p>
      </div>
      <div>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-foreground/35">
          Решение
        </p>
        <p className="text-sm text-foreground/65">{caseStudy.solution}</p>
      </div>

      <div className="mt-auto grid grid-cols-3 gap-3 border-t border-border pt-6">
        {caseStudy.results.map((r) => (
          <div key={r.label} className="text-center">
            <div className="text-lg font-semibold leading-none text-gold">
              {r.value}
            </div>
            <div className="mt-1.5 text-[10px] leading-tight text-foreground/35">
              {r.label}
            </div>
          </div>
        ))}
      </div>
    </Link>
  );
}
