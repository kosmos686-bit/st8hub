"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { FileText } from "lucide-react";
import { TELEGRAM_URL } from "@/lib/constants";

export function RoiCalculator() {
  const [points, setPoints] = useState(5);
  const [check, setCheck] = useState(1500);
  const [guests, setGuests] = useState(80);

  // Blended savings estimate: 5% of annual revenue. Individual levers
  // (no-show, закупки, чек, списания) are not independent percentages of
  // revenue — summing them (as the old formula did) overstated savings
  // by 6-7x. 5% sits in the realistic 4-6% range for this kind of
  // automation and isn't broken down into fake precise sub-percentages.
  const SAVINGS_RATE = 0.05;

  const total = useMemo(() => {
    const dailyRevenue = points * guests * check;
    const annualRevenue = dailyRevenue * 365;
    return Math.round(annualRevenue * SAVINGS_RATE);
  }, [points, check, guests]);

  return (
    <div className="mx-auto max-w-3xl rounded-[20px] border border-border bg-card px-6 py-8 sm:px-10 sm:py-12">
      <div className="grid gap-8 md:grid-cols-2 md:gap-12">
        <div>
          <div className="mb-6">
            <div className="mb-3 flex items-center justify-between text-sm text-foreground/70">
              <span>Количество точек</span>
              <span className="text-base font-semibold text-gold">{points}</span>
            </div>
            <input
              type="range"
              min={1}
              max={50}
              value={points}
              onChange={(e) => setPoints(Number(e.target.value))}
              className="roi-slider w-full"
            />
          </div>

          <div className="mb-6">
            <div className="mb-3 flex items-center justify-between text-sm text-foreground/70">
              <span>Средний чек, руб.</span>
              <span className="text-base font-semibold text-gold">
                {check.toLocaleString("ru-RU")}
              </span>
            </div>
            <input
              type="range"
              min={500}
              max={10000}
              step={100}
              value={check}
              onChange={(e) => setCheck(Number(e.target.value))}
              className="roi-slider w-full"
            />
          </div>

          <div>
            <div className="mb-3 flex items-center justify-between text-sm text-foreground/70">
              <span>Гостей в день (на точку)</span>
              <span className="text-base font-semibold text-gold">{guests}</span>
            </div>
            <input
              type="range"
              min={20}
              max={500}
              step={10}
              value={guests}
              onChange={(e) => setGuests(Number(e.target.value))}
              className="roi-slider w-full"
            />
          </div>
        </div>

        <div className="flex flex-col items-center justify-center rounded-2xl border border-gold/15 bg-gold/5 px-6 py-8 text-center">
          <div className="text-4xl font-light tracking-tight text-gold sm:text-5xl">
            {total.toLocaleString("ru-RU")} <span className="text-2xl">руб.</span>
          </div>
          <div className="mt-2 text-sm text-foreground/60">
            экономия за 12 месяцев
          </div>
          <Link
            href={TELEGRAM_URL}
            target="_blank"
            rel="noopener"
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition-colors hover:bg-gold"
          >
            <FileText className="h-4 w-4" />
            Получить персональное КП
          </Link>
          <p className="mt-4 text-xs text-foreground/50">
            Оценка: 5% годовой выручки за счёт сокращения списаний, роста
            среднего чека, оптимизации закупок и снижения no-show. Точную
            цифру считаем после аудита ваших данных.
          </p>
        </div>
      </div>
    </div>
  );
}
