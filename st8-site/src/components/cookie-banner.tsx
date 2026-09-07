"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const STORAGE_KEY = "st8-cookie-consent";

export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) setVisible(true);
  }, []);

  function decide(value: "accepted" | "declined") {
    localStorage.setItem(STORAGE_KEY, value);
    setVisible(false);
    // No analytics are loaded yet. When one is added, gate its script tag
    // on `localStorage.getItem("st8-cookie-consent") === "accepted"`.
  }

  if (!visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-white/10 bg-[#0a0a0a]/98 px-6 py-5 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 sm:flex-row sm:justify-between">
        <p className="text-sm text-foreground/70">
          Мы используем cookie для аналитики и работы сайта. Подробнее — в{" "}
          <Link href="/legal/privacy" className="underline hover:text-gold">
            политике конфиденциальности
          </Link>
          .
        </p>
        <div className="flex shrink-0 gap-3">
          <button
            onClick={() => decide("declined")}
            className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-medium text-foreground/80 transition-colors hover:border-white/30"
          >
            Отклонить
          </button>
          <button
            onClick={() => decide("accepted")}
            className="rounded-full bg-gold px-5 py-2.5 text-sm font-semibold text-[#0a0a0a] transition-colors hover:bg-gold/90"
          >
            Принять
          </button>
        </div>
      </div>
    </div>
  );
}
