import type { Metadata } from "next";
import { PricingSection } from "@/components/pricing-section";

export const metadata: Metadata = {
  title: "Цены",
  description: "Стоимость внедрения AI-автоматизации ST8-AI.",
};

export default function PricingPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="text-center">
          <h1 className="text-3xl font-semibold tracking-tight">Цены</h1>
          <p className="mt-3 text-foreground/70">
            Стоимость зависит от количества сценариев и глубины интеграции.
            Ниже — ориентировочные пакеты.
          </p>
        </div>
        <div className="mt-12">
          <PricingSection />
        </div>
      </div>
    </section>
  );
}
