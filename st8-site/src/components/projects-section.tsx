import Link from "next/link";
import { ArrowRight, ArrowUpRight, Sparkles, ShoppingBag, Truck } from "lucide-react";
import { liveProjects } from "@/lib/data/projects";
import { cases } from "@/lib/data/cases";

const logoStyles: Record<string, string> = {
  АВ: "bg-[linear-gradient(135deg,#1a3a1a,#2d5a2d)] text-[#7cb87c] border-[#7cb87c]/30",
  LG: "bg-[linear-gradient(135deg,#1a1a3a,#2d2d5a)] text-[#8b8bd4] border-[#8b8bd4]/30",
  UF: "bg-[linear-gradient(135deg,#3a1a1a,#5a2d2d)] text-[#d48484] border-[#d48484]/30",
};

function ProjectVisual({ visual }: { visual: "kitchen" | "stroy" | "resto" }) {
  if (visual === "kitchen") {
    return (
      <div className="flex h-full flex-col justify-center gap-2 px-5">
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-medium text-foreground/70">Горячий цех</span>
          <span className="font-semibold text-gold">0 в очереди</span>
        </div>
        <div className="flex items-start gap-1.5 rounded-md border-l-2 border-gold bg-gold/5 px-2 py-1.5 text-[10px] text-foreground/50">
          <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-gold" />
          AI: приготовить 4 порции батчем — экономия 18 мин
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-medium text-foreground/70">Холодный цех</span>
          <span className="font-semibold text-gold">0 в очереди</span>
        </div>
      </div>
    );
  }

  const label = visual === "stroy" ? "ST8 BUILD" : "ST8 RESTO";
  const sub = visual === "stroy" ? "AI MASTER" : "CHEFF AI";
  const width = visual === "stroy" ? "73%" : "61%";
  const tags =
    visual === "stroy" ? ["Стройка", "Сметы", "ГОСТ"] : ["ТТК", "HACCP", "КБЖУ"];

  return (
    <div className="flex h-full flex-col justify-center gap-3 px-5">
      <div>
        <div className="text-[16px] font-semibold tracking-wide">{label}</div>
        <div className="text-[10px] uppercase tracking-[0.1em] text-gold">{sub}</div>
      </div>
      <div className="h-[3px] w-full overflow-hidden rounded-full bg-white/8">
        <div
          className="h-full rounded-full bg-gradient-to-r from-gold to-gold/60"
          style={{ width }}
        />
      </div>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((t) => (
          <span
            key={t}
            className="rounded-full bg-white/4 px-2 py-0.5 text-[9px] text-foreground/50"
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

const caseIcons = [Truck, ShoppingBag, Sparkles];

export function ProjectsSection() {
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {liveProjects.map((project) => (
        <a
          key={project.slug}
          href={project.url}
          target="_blank"
          rel="noopener"
          className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-all hover:border-gold/20"
        >
          <div className="relative h-[190px] shrink-0 border-b border-border bg-background">
            <span className="absolute left-3 top-3 z-10 flex items-center gap-1.5 rounded-full border border-gold/25 bg-gold/10 px-2.5 py-1 text-[9px] font-semibold uppercase tracking-wide text-gold">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold" />
              Клиент ST8 AI
            </span>
            <ProjectVisual visual={project.visual} />
          </div>

          <div className="flex flex-1 flex-col p-5">
            <div className="mb-2.5 flex items-center gap-2.5 border-b border-border pb-2.5">
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border text-xs font-semibold ${
                  logoStyles[project.clientShort] ?? ""
                }`}
              >
                {project.clientShort}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1 truncate text-sm font-semibold group-hover:text-gold">
                  {project.client}
                  <ArrowUpRight className="h-3 w-3 shrink-0" />
                </div>
                <div className="truncate text-[11px] text-foreground/50">
                  {project.type}
                </div>
              </div>
            </div>

            <h3 className="mb-1.5 text-[15px] font-semibold">{project.title}</h3>
            <p className="mb-3 flex-1 text-xs leading-relaxed text-foreground/50">
              {project.description}
            </p>

            <div className="mb-3 flex flex-wrap gap-1.5">
              {project.tags.map((t) => (
                <span
                  key={t}
                  className="rounded-full bg-gold/8 px-2 py-0.5 text-[10px] font-medium text-gold"
                >
                  {t}
                </span>
              ))}
            </div>

            <div className="flex items-center gap-1.5 border-t border-border pt-3.5 text-xs font-semibold text-gold transition-all group-hover:gap-2.5">
              Подробнее о проекте
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>
        </a>
      ))}

      {cases.map((c, i) => {
        const Icon = caseIcons[i % caseIcons.length];
        return (
          <Link
            key={c.slug}
            href={`/cases/${c.slug}`}
            className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-all hover:border-gold/20"
          >
            <div className="relative flex h-[190px] shrink-0 items-center justify-center border-b border-border bg-background">
              <span className="absolute left-3 top-3 z-10 flex items-center gap-1.5 rounded-full border border-gold/25 bg-gold/10 px-2.5 py-1 text-[9px] font-semibold uppercase tracking-wide text-gold">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold" />
                Клиент ST8 AI
              </span>
              <Icon className="h-10 w-10 text-gold/40" />
            </div>

            <div className="flex flex-1 flex-col p-5">
              <div className="mb-2.5 border-b border-border pb-2.5">
                <div className="text-sm font-semibold group-hover:text-gold">
                  {c.client}
                </div>
                <div className="text-[11px] text-foreground/50">{c.industry}</div>
              </div>

              <p className="mb-3 flex-1 text-xs leading-relaxed text-foreground/50">
                {c.solution}
              </p>

              <div className="mb-3 flex flex-wrap gap-1.5">
                <span className="rounded-full bg-gold/8 px-2 py-0.5 text-[10px] font-medium text-gold">
                  {c.tag}
                </span>
                {c.results[0] && (
                  <span className="rounded-full bg-gold/8 px-2 py-0.5 text-[10px] font-semibold text-gold">
                    {c.results[0].value} {c.results[0].label}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-1.5 border-t border-border pt-3.5 text-xs font-semibold text-gold transition-all group-hover:gap-2.5">
                Подробнее о проекте
                <ArrowRight className="h-3.5 w-3.5" />
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
