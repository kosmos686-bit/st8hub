import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Спасибо",
  description: "Заявка отправлена — ST8-AI свяжется с вами в ближайшее время.",
  robots: { index: false, follow: false },
};

export default function ThankYouPage() {
  return (
    <section className="flex flex-1 flex-col items-center justify-center px-6 py-24 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">Спасибо!</h1>
      <p className="mt-3 max-w-md text-foreground/70">
        Заявка получена. Мы свяжемся с вами в течение рабочего дня.
      </p>
      <Button asChild className="mt-8 bg-gold text-[#0a0a0a] hover:bg-gold/90">
        <Link href="/">На главную</Link>
      </Button>
    </section>
  );
}
