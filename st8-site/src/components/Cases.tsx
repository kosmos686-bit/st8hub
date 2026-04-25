"use client";

import { useRef } from "react";
import { motion, useInView } from "framer-motion";

const cases = [
  {
    client: "Логистический хаб",
    industry: "Логистика",
    tag: "Лидогенерация",
    challenge: "Ручной сбор лидов занимал 8 часов в день, конверсия падала",
    solution: "Автоматический сбор 2GIS + AI-квалификация + автопрогрев",
    results: [
      { v: "481", l: "лидов/месяц" },
      { v: "−90%", l: "время на сбор" },
      { v: "×4", l: "рост пайплайна" },
    ],
  },
  {
    client: "Atelier Family",
    industry: "Ритейл / App",
    tag: "CRM",
    challenge: "Нет единой системы учёта клиентов — заявки терялись",
    solution: "Интеграция AI CRM в Telegram + мобильное приложение v3",
    results: [
      { v: "+35%", l: "LTV клиентов" },
      { v: "2 нед", l: "внедрение" },
      { v: "0", l: "потерянных заявок" },
    ],
  },
  {
    client: "AIRI",
    industry: "IT / Партнёрство",
    tag: "Масштабирование",
    challenge: "Нужно масштабировать продажи без раздувания штата",
    solution: "ST8-AI как платформа агентских продаж, 5 треков одновременно",
    results: [
      { v: "5", l: "треков продаж" },
      { v: "+200к ₽", l: "первый месяц" },
      { v: "1", l: "вместо 5 менеджеров" },
    ],
  },
];

function CaseCard({ item, index }: { item: typeof cases[0]; index: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.18, duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
      className="group flex flex-col bg-white/[0.03] border border-white/8 rounded-3xl p-7 hover:border-[#D4A017]/30 transition-all duration-400"
    >
      <div className="flex items-start justify-between mb-6">
        <div>
          <span className="text-[#D4A017]/70 text-[10px] font-bold uppercase tracking-wider mb-1.5 block">
            {item.industry}
          </span>
          <h3 className="text-xl font-black group-hover:text-[#D4A017] transition-colors">{item.client}</h3>
        </div>
        <span className="px-3 py-1 bg-[#D4A017]/10 border border-[#D4A017]/20 rounded-full text-[#D4A017] text-[10px] font-bold whitespace-nowrap ml-3">
          {item.tag}
        </span>
      </div>

      <div className="mb-3">
        <p className="text-white/35 text-[10px] uppercase tracking-wider mb-1 font-semibold">Задача</p>
        <p className="text-white/65 text-sm leading-relaxed">{item.challenge}</p>
      </div>
      <div className="mb-6">
        <p className="text-white/35 text-[10px] uppercase tracking-wider mb-1 font-semibold">Решение</p>
        <p className="text-white/65 text-sm leading-relaxed">{item.solution}</p>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-auto pt-6 border-t border-white/8">
        {item.results.map((r) => (
          <div key={r.l} className="text-center">
            <div className="text-[#D4A017] font-black text-lg leading-none">{r.v}</div>
            <div className="text-white/35 text-[10px] mt-1.5 leading-tight">{r.l}</div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export default function Cases() {
  const headRef = useRef(null);
  const headInView = useInView(headRef, { once: true, margin: "-80px" });

  return (
    <section id="cases" className="py-28 px-6">
      <div className="max-w-7xl mx-auto">
        <div ref={headRef} className="text-center mb-16">
          <motion.span
            initial={{ opacity: 0 }}
            animate={headInView ? { opacity: 1 } : {}}
            className="text-[#D4A017] text-xs font-bold uppercase tracking-[0.2em] mb-5 block"
          >
            Кейсы
          </motion.span>
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={headInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.1, duration: 0.6 }}
            className="text-4xl lg:text-5xl font-black"
          >
            Реальные результаты{" "}
            <span className="text-gradient">реальных клиентов</span>
          </motion.h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {cases.map((c, i) => (
            <CaseCard key={c.client} item={c} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
