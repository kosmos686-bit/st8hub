"use client";

import { Check, Rocket } from "lucide-react";
import { cn } from "@/lib/utils";

interface Tier {
  id: string;
  name: string;
  subtitle: string;
  price: string;
  period: string;
  features: string[];
  cta: string;
  featured?: boolean;
}

const tiers: Tier[] = [
  {
    id: "basic",
    name: "Базовый",
    subtitle: "1-3 точки",
    price: "65 000 ₽",
    period: "единоразово + поддержка",
    features: [
      "AI-консьерж для бронирования",
      "Telegram + WhatsApp",
      "Интеграция iiko / R-Keeper",
      "Базовая CRM и напоминания",
      "Настройка за 3 дня",
      "Поддержка 24/7",
    ],
    cta: "Запустить пилот",
  },
  {
    id: "business",
    name: "Бизнес",
    subtitle: "4-10 точек",
    price: "165 000 ₽",
    period: "единоразово + поддержка",
    features: [
      "Всё из Базового",
      "Интеграция Remarket",
      "Предиктивные закупки (7 дней)",
      "Кросс-аналитика по точкам",
      "Персонализация для VIP",
      "Выделенный менеджер",
    ],
    cta: "Запустить пилот",
    featured: true,
  },
  {
    id: "enterprise",
    name: "Сеть",
    subtitle: "10+ точек",
    price: "385 000 ₽",
    period: "единоразово + поддержка",
    features: [
      "Всё из Бизнес",
      "Единая система управления сетью",
      "Computer vision на кухнях",
      "Автозакупки у поставщиков",
      "On-premise deployment",
      "Обучение команды",
    ],
    cta: "Обсудить проект",
  },
];

function openLeadForm(planName: string) {
  const msg = `Здравствуйте! Хочу запустить пилот — тариф ${planName}`;
  window.open(
    `https://t.me/Zzima686?text=${encodeURIComponent(msg)}`,
    "_blank"
  );
}

export function PricingSection() {
  return (
    <div className="grid gap-5 md:grid-cols-3">
      {tiers.map((tier) => (
        <div
          key={tier.id}
          className={cn(
            "relative flex flex-col gap-6 rounded-2xl border p-8 transition-colors",
            tier.featured
              ? "border-gold/30 bg-gradient-to-b from-gold/[0.03] to-card"
              : "border-border bg-card hover:border-gold/15"
          )}
        >
          {tier.featured && (
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gold px-4 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-[#0a0a0a]">
              Популярный
            </span>
          )}

          <div>
            <h3 className="text-lg font-semibold">{tier.name}</h3>
            <p className="mt-1 text-xs text-foreground/50">{tier.subtitle}</p>
            <p className="mt-4 text-3xl font-light tracking-tight">
              {tier.price}
            </p>
            <p className="mt-1 text-xs text-foreground/50">{tier.period}</p>
          </div>

          <ul className="flex flex-1 flex-col gap-3 text-sm text-foreground/70">
            {tier.features.map((f) => (
              <li key={f} className="flex items-start gap-2.5">
                <Check className="mt-0.5 h-4 w-4 shrink-0 text-gold" />
                {f}
              </li>
            ))}
          </ul>

          <button
            onClick={() => openLeadForm(tier.name)}
            className={cn(
              "flex w-full items-center justify-center gap-2 rounded-full py-3.5 text-sm font-semibold transition-colors",
              tier.featured
                ? "bg-white text-black hover:bg-gold"
                : "border border-border text-foreground hover:border-gold/40 hover:text-gold"
            )}
          >
            {tier.featured && <Rocket className="h-4 w-4" />}
            {tier.cta}
          </button>
        </div>
      ))}
    </div>
  );
}
