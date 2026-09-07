"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import { ChevronDown, Shield, Star, TrendingUp } from "lucide-react";
import { HeroParticles } from "./hero-particles";
import { Preloader } from "./preloader";

interface HeroProps {
  eyebrow?: string;
  title?: React.ReactNode;
  description?: string;
  primaryCta?: { href: string; label: string };
  secondaryCta?: { href: string; label: string };
}

const STAGGER = 0.08;
const WORD_STAGGER = 0.1;

function RevealWord({
  children,
  index,
  ready,
  className,
}: {
  children: React.ReactNode;
  index: number;
  ready: boolean;
  className?: string;
}) {
  return (
    <span className="inline-block overflow-hidden align-bottom">
      <motion.span
        className={`inline-block ${className ?? ""}`}
        initial={{ y: "110%" }}
        animate={{ y: ready ? "0%" : "110%" }}
        transition={{
          duration: 0.7,
          ease: [0.16, 1, 0.3, 1],
          delay: WORD_STAGGER * index,
        }}
      >
        {children}
      </motion.span>
    </span>
  );
}

export function Hero({
  eyebrow,
  title,
  description,
  primaryCta = { href: "#roi", label: "Рассчитать экономию" },
  secondaryCta = { href: "#solutions", label: "Узнать больше" },
}: HeroProps) {
  const isHome = !title;
  const [introReady, setIntroReady] = useState(!isHome);

  return (
    <section
      className={`relative -mt-16 flex flex-col justify-end overflow-hidden sm:-mt-[72px] ${
        isHome ? "min-h-dvh" : "min-h-[60vh]"
      }`}
    >
      {isHome && <Preloader onComplete={() => setIntroReady(true)} />}

      {/* No video asset yet — plain gradient background. Re-add <video> with
          a real poster + source once footage exists; a half-wired video tag
          with no media is worse than no tag at all. */}
      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_50%_20%,rgba(212,175,55,0.20),transparent_55%),radial-gradient(ellipse_at_10%_100%,rgba(212,175,55,0.08),transparent_50%),linear-gradient(180deg,#0a0a0a,#050505)]" />
      <div className="absolute inset-0 z-[1] bg-gradient-to-b from-background/25 to-background/80" />
      <HeroParticles />

      <div className="relative z-10 px-6 pb-10 pt-24 sm:px-8 sm:pb-12 md:px-12 md:pb-16">
        <div className="max-w-4xl">
          {isHome && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: introReady ? 1 : 0, y: introReady ? 0 : 8 }}
              transition={{ duration: 0.4 }}
              className="mb-6 flex flex-wrap gap-3 sm:gap-6"
            >
              <span className="flex items-center gap-1.5 text-xs text-foreground/70 sm:text-sm">
                <Star className="h-4 w-4 fill-current sm:h-5 sm:w-5" />
                <span className="font-semibold text-gold">4</span> кейса
              </span>
              <span className="flex items-center gap-1.5 text-xs text-foreground/70 sm:text-sm">
                <TrendingUp className="h-4 w-4 sm:h-5 sm:w-5" />
                Окупаемость <span className="font-semibold text-gold">от 3 месяцев</span>
              </span>
              <span className="flex items-center gap-1.5 text-xs text-foreground/70 sm:text-sm">
                <Shield className="h-4 w-4 sm:h-5 sm:w-5" />
                Гарантия результата по договору
              </span>
            </motion.div>
          )}

          {eyebrow && (
            <p className="mb-4 text-sm font-medium uppercase tracking-[0.2em] text-gold">
              {eyebrow}
            </p>
          )}

          {isHome ? (
            <h1 className="mb-6 break-words text-[clamp(2rem,10vw,8.75rem)] font-semibold uppercase leading-[0.9] tracking-[-0.04em]">
              <RevealWord index={0} ready={introReady}>
                Автоматизация
              </RevealWord>{" "}
              <RevealWord index={1} ready={introReady}>
                бизнеса
              </RevealWord>
              <br />
              <RevealWord index={2} ready={introReady} className="text-gold">
                с
              </RevealWord>{" "}
              <RevealWord index={3} ready={introReady} className="text-gold">
                гарантией
              </RevealWord>{" "}
              <RevealWord index={4} ready={introReady} className="text-gold">
                результата
              </RevealWord>
            </h1>
          ) : (
            <motion.h1
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-5 text-[clamp(2.5rem,6vw,5rem)] font-semibold leading-[1.05] tracking-tight"
            >
              {title}
            </motion.h1>
          )}

          <motion.p
            initial={{ opacity: 0, y: 14 }}
            animate={{
              opacity: introReady ? 1 : 0,
              y: introReady ? 0 : 14,
            }}
            transition={{ duration: 0.5, delay: isHome ? STAGGER : 0 }}
            className="mb-8 max-w-xl text-lg leading-relaxed text-foreground/60 md:text-xl"
          >
            {description ??
              "AI-агенты для ресторанов, производства и логистики — без остановки бизнеса"}
          </motion.p>

          {isHome && (
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{
                opacity: introReady ? 1 : 0,
                y: introReady ? 0 : 14,
              }}
              transition={{ duration: 0.5, delay: STAGGER * 2 }}
              className="flex flex-wrap items-center gap-3"
            >
              <Link
                href={primaryCta.href}
                className="inline-flex items-center gap-2.5 rounded-full bg-gold px-7 py-3.5 text-[15px] font-semibold text-[#0a0a0a] transition-all hover:-translate-y-0.5 hover:shadow-[0_10px_40px_rgba(212,175,55,0.35)]"
              >
                {primaryCta.label}
              </Link>
              <Link
                href={secondaryCta.href}
                className="inline-flex items-center gap-2.5 rounded-full border border-white/15 px-7 py-3.5 text-[15px] font-medium text-foreground transition-colors hover:border-gold/40"
              >
                {secondaryCta.label}
              </Link>
            </motion.div>
          )}

          {isHome && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{
                opacity: introReady ? 1 : 0,
                y: introReady ? 0 : 10,
              }}
              transition={{ duration: 0.5, delay: STAGGER * 3 }}
              className="mt-10 flex flex-wrap items-center gap-4 border-t border-white/8 pt-5 sm:gap-6"
            >
              <span className="text-[11px] font-medium uppercase tracking-[0.1em] text-foreground/40">
                Интеграции
              </span>
              <div className="flex flex-wrap items-center gap-5">
                {["iiko", "R-Keeper", "1С", "amoCRM"].map((name) => (
                  <span
                    key={name}
                    className="text-[13px] font-semibold tracking-wide text-foreground/35 transition-colors hover:text-foreground/70"
                  >
                    {name}
                  </span>
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {isHome && (
        <div className="hidden sm:absolute sm:bottom-6 sm:left-1/2 sm:z-10 sm:flex sm:-translate-x-1/2 sm:flex-col sm:items-center sm:gap-2 sm:opacity-50">
          <span className="text-[10px] uppercase tracking-[0.15em] text-foreground/50">
            Вниз
          </span>
          <ChevronDown className="h-5 w-5 animate-bounce text-foreground/50" />
        </div>
      )}
    </section>
  );
}
