import type { Metadata } from "next";
import { Hero } from "@/components/hero";
import { RoiCalculator } from "@/components/roi-calculator";
import { SolutionsAccordion } from "@/components/solutions-accordion";
import { PricingSection } from "@/components/pricing-section";
import { HowItWorks } from "@/components/how-it-works";
import { ProjectsSection } from "@/components/projects-section";
import { PartnersSection } from "@/components/partners-section";
import { TeamSection } from "@/components/team-section";
import { LeadForm } from "@/components/lead-form";

export const metadata: Metadata = {
  title: "ST8-AI — AI-автоматизация для бизнеса",
  description:
    "ST8-AI внедряет AI-автоматизацию в ресторанах, производстве, ритейле и логистике. 4 внедрённых кейса. Окупаемость от 3 месяцев. Гарантия KPI по договору.",
};

function SectionHeader({
  label,
  title,
  description,
}: {
  label: string;
  title: React.ReactNode;
  description?: string;
}) {
  return (
    <div className="mx-auto mb-12 max-w-2xl text-center sm:mb-16">
      <div className="mb-4 text-xs font-semibold uppercase tracking-[0.15em] text-gold">
        {label}
      </div>
      <h2 className="text-[clamp(2rem,4vw,3rem)] font-semibold tracking-tight">
        {title}
      </h2>
      {description && (
        <p className="mx-auto mt-4 max-w-xl text-foreground/50">{description}</p>
      )}
    </div>
  );
}

export default function Home() {
  return (
    <>
      <Hero />

      <section id="roi" className="bg-background px-6 py-24 md:py-40">
        <SectionHeader
          label="Калькулятор"
          title={
            <>
              Сколько вы <span className="text-gold">сэкономите</span> за год?
            </>
          }
          description="Ползунки ниже рассчитывают реальную экономию на основе данных 47 внедрённых проектов"
        />
        <RoiCalculator />
      </section>

      <section id="solutions" className="bg-[#0a0a0a] px-6 py-24 md:py-40">
        <SectionHeader
          label="Решения"
          title={
            <>
              AI для <span className="text-gold">вашей отрасли</span>
            </>
          }
          description="Кастомные решения под конкретного клиента — не коробочные продукты"
        />
        <div className="mx-auto max-w-6xl">
          <SolutionsAccordion />
        </div>
      </section>

      <section id="pricing" className="bg-background px-6 py-24 md:py-40">
        <SectionHeader
          label="Тарифы"
          title={
            <>
              Выберите <span className="text-gold">масштаб</span> внедрения
            </>
          }
          description="Все тарифы включают обучение моделей на ваших данных и интеграцию без остановки бизнеса"
        />
        <div className="mx-auto max-w-5xl">
          <PricingSection />
        </div>
      </section>

      <section id="how" className="bg-[#0a0a0a] px-6 py-24">
        <SectionHeader
          label="Процесс"
          title={
            <>
              От аудита до <span className="text-gold">результата</span>
            </>
          }
          description="Внедрение без остановки бизнеса — работаем ночью и в выходные"
        />
        <HowItWorks />
      </section>

      <section id="projects" className="bg-background px-6 py-24 md:py-40">
        <SectionHeader
          label="Кейсы"
          title={
            <>
              Решения для <span className="text-gold">ключевых клиентов</span>
            </>
          }
          description="Работающие пилоты и внедрённые системы — от dark kitchen до логистических хабов"
        />
        <div className="mx-auto max-w-6xl">
          <ProjectsSection />
        </div>
      </section>

      <section id="partners" className="bg-background px-6 py-24">
        <SectionHeader
          label="Партнёры"
          title={
            <>
              Работаем в <span className="text-gold">партнёрстве</span>
            </>
          }
        />
        <PartnersSection />
      </section>

      <section id="team" className="bg-[#0a0a0a] px-6 py-24 md:py-40">
        <SectionHeader
          label="Команда"
          title={
            <>
              Люди за <span className="text-gold">ST8-AI</span>
            </>
          }
        />
        <TeamSection />
      </section>

      <section id="lead" className="bg-background px-6 py-24 md:py-40">
        <SectionHeader
          label="Заявка"
          title={
            <>
              Обсудим <span className="text-gold">вашу задачу</span>?
            </>
          }
          description="Оставьте контакты — посчитаем экономию для вашего бизнеса и предложим сценарий внедрения"
        />
        <LeadForm />
      </section>
    </>
  );
}
