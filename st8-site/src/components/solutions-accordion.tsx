"use client";

import { useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import { Check, ChevronDown, Send } from "lucide-react";
import { solutions } from "@/lib/data/solutions";
import { TELEGRAM_URL } from "@/lib/constants";
import { cn } from "@/lib/utils";

export function SolutionsAccordion() {
  const [openSlug, setOpenSlug] = useState<string | null>(null);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {solutions.map((solution) => {
        const isOpen = openSlug === solution.slug;
        const Icon = solution.icon;

        return (
          <div
            key={solution.slug}
            className={cn(
              "col-span-1 rounded-2xl border border-border bg-card p-6 transition-colors",
              isOpen && "border-gold/25 sm:col-span-2 lg:col-span-3"
            )}
          >
            <button
              type="button"
              onClick={() => setOpenSlug(isOpen ? null : solution.slug)}
              className="relative flex w-full flex-col items-start text-left"
            >
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl border border-gold/20 bg-gold/10 text-gold">
                <Icon className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">{solution.name}</h3>
              <p className="mb-4 text-sm leading-relaxed text-foreground/60">
                {solution.description}
              </p>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-gold/10 px-3 py-1.5 text-xs font-semibold text-gold">
                {solution.metric}
              </span>
              <div
                className={cn(
                  "absolute right-0 top-0 flex h-8 w-8 items-center justify-center rounded-full border border-border text-foreground/50 transition-transform",
                  isOpen && "rotate-180 border-gold/40 text-gold"
                )}
              >
                <ChevronDown className="h-4 w-4" />
              </div>
            </button>

            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                  className="overflow-hidden"
                >
                  <div className="mt-5 grid gap-8 border-t border-border pt-5 md:grid-cols-2">
                    <div>
                      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gold">
                        Что входит в решение
                      </h4>
                      <ul className="space-y-2.5">
                        {solution.features.map((f) => (
                          <li key={f.title} className="flex items-start gap-2.5 text-sm">
                            <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
                            <span className="text-foreground/70">
                              <span className="font-medium text-foreground">
                                {f.title}
                              </span>{" "}
                              — {f.description}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wide text-gold">
                        Как это работает
                      </h4>
                      <p className="text-sm leading-relaxed text-foreground/70">
                        {solution.howItWorks}
                      </p>

                      <h4 className="mb-3 mt-5 text-xs font-semibold uppercase tracking-wide text-gold">
                        Результаты клиентов
                      </h4>
                      <div className="grid grid-cols-3 gap-3 rounded-xl border border-gold/10 bg-gold/[0.03] p-4">
                        {solution.stats.map((s) => (
                          <div key={s.label} className="text-center">
                            <div className="text-lg font-light text-gold">
                              {s.value}
                            </div>
                            <div className="mt-1 text-[11px] text-foreground/50">
                              {s.label}
                            </div>
                          </div>
                        ))}
                      </div>

                      <Link
                        href={TELEGRAM_URL}
                        target="_blank"
                        rel="noopener"
                        onClick={(e) => e.stopPropagation()}
                        className="mt-5 inline-flex items-center gap-2 rounded-full bg-gold px-5 py-2.5 text-sm font-semibold text-[#0a0a0a] transition-colors hover:bg-gold/90"
                      >
                        <Send className="h-3.5 w-3.5" />
                        Написать в Telegram
                      </Link>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
