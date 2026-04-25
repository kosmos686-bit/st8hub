"use client";

import { useRef } from "react";
import { motion, useInView, useScroll, useTransform } from "framer-motion";

const industries = [
  {
    icon: "🍽️",
    title: "HoReCa",
    sub: "Рестораны и отели",
    desc: "AI-агент принимает брони в Telegram 24/7, автоматизирует обратную связь и управляет заявками без потерь.",
    metrics: ["−40% время ответа", "+28% конверсия"],
    accent: "from-orange-900/20",
  },
  {
    icon: "🛍️",
    title: "Ритейл",
    sub: "Сети и дистрибьюторы",
    desc: "Квалификация B2B-клиентов, автоматические follow-up, интеграция с CRM — продажи без ручного труда.",
    metrics: ["×3 квалификация", "+35% выручка"],
    accent: "from-blue-900/20",
  },
  {
    icon: "⚙️",
    title: "Производство",
    sub: "Заводы и фабрики",
    desc: "Лидогенерация из 2GIS и HH, автопрогрев аудитории, персонализированные КП за 30 секунд.",
    metrics: ["500+ лидов/день", "КП за 30 сек"],
    accent: "from-zinc-900/30",
  },
  {
    icon: "🚛",
    title: "Логистика",
    sub: "ТК и склады",
    desc: "Мониторинг тендеров, автоответы на заявки, интеграция amoCRM. 481 лид в первый месяц работы.",
    metrics: ["481 лид/мес", "amoCRM интеграция"],
    accent: "from-green-900/20",
  },
];

function Card({ item, index }: { item: typeof industries[0]; index: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.12, duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
      className="group relative bg-white/[0.03] border border-white/8 rounded-3xl p-7 overflow-hidden hover:border-[#D4A017]/35 transition-all duration-500 cursor-default"
    >
      {/* Hover gradient */}
      <div className={`absolute inset-0 bg-gradient-to-br ${item.accent} to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

      <div className="relative">
        <div className="text-5xl mb-5">{item.icon}</div>
        <h3 className="text-xl font-black mb-1 group-hover:text-[#D4A017] transition-colors">{item.title}</h3>
        <p className="text-[#D4A017]/70 text-xs font-semibold uppercase tracking-wide mb-4">{item.sub}</p>
        <p className="text-white/55 text-sm leading-relaxed mb-6">{item.desc}</p>
        <div className="flex flex-wrap gap-2">
          {item.metrics.map((m) => (
            <span
              key={m}
              className="px-3 py-1 bg-[#D4A017]/10 border border-[#D4A017]/20 rounded-full text-[#D4A017] text-xs font-semibold"
            >
              {m}
            </span>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export default function Industries() {
  const sectionRef = useRef(null);
  const headRef = useRef(null);
  const headInView = useInView(headRef, { once: true, margin: "-80px" });

  const { scrollYProgress } = useScroll({ target: sectionRef, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [50, -50]);

  return (
    <section id="industries" className="py-28 px-6 overflow-hidden" ref={sectionRef}>
      <div className="max-w-7xl mx-auto">
        <motion.div style={{ y }} ref={headRef} className="text-center mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            animate={headInView ? { opacity: 1 } : {}}
            className="text-[#D4A017] text-xs font-bold uppercase tracking-[0.2em] mb-5 block"
          >
            Отрасли
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.1, duration: 0.6 }}
            className="text-4xl lg:text-5xl font-black"
          >
            Работаем с вашей{" "}
            <span className="text-gradient">индустрией</span>
          </motion.h2>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
          {industries.map((ind, i) => (
            <Card key={ind.title} item={ind} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
