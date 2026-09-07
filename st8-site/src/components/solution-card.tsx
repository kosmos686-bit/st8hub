import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { Solution } from "@/lib/data/solutions";

export function SolutionCard({ solution }: { solution: Solution }) {
  return (
    <Link
      href={`/solutions/${solution.slug}`}
      className="group relative flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 transition-colors hover:border-gold/40"
    >
      <h3 className="font-semibold text-card-foreground">{solution.name}</h3>
      <p className="text-sm text-foreground/60">{solution.tagline}</p>
      <span className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-gold">
        Подробнее
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
      </span>
    </Link>
  );
}
